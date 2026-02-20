---
name: video-to-subtitle-summary
description: Use when user provides a Douyin video URL or a local video/audio file path and wants to extract subtitles and generate AI summary. Triggers on Douyin URLs like v.douyin.com, share links, or local file paths ending in .mp4/.mp3/.wav etc.
args: <douyin_url_or_file_path> - 抖音视频链接或本地视频/音频文件路径（必需）
---

# 视频转字幕与AI总结技能

## Overview

将抖音视频或本地视频/音频文件转换为字幕文本并生成AI摘要。

**核心流程：**
- **在线视频：** 获取视频信息 → 下载视频 → 提取音频 → 语音识别 → 生成字幕 → AI总结
- **本地文件：** 提取音频（如需） → 语音识别 → 生成字幕 → AI总结

## When to Use

- 用户提供抖音链接，要求提取字幕或生成总结
- 用户提供本地视频/音频文件路径，要求转字幕或生成总结
- 需要将视频内容转为文字

**不适用于：** 实时语音识别、直播字幕

## 外部依赖

| 服务                | 用途                   | 必需                           |
| ------------------- | ---------------------- | ------------------------------ |
| **TikHub API**      | 获取视频信息和下载地址 | 仅在线视频模式需要             |
| **字节跳动 VC API** | 语音转文字             | ✅                              |
| **FFmpeg**          | 提取音频（本地工具）   | ✅（音频文件可跳过）            |

## API 凭证（环境变量）

通过环境变量读取，支持以下任意方式配置：

**方式一：.env 文件（推荐）** — 在 skill 目录下创建 `.env` 文件：

```bash
TIKHUB_TOKEN="your_token"
BYTEDANCE_VC_TOKEN="your_token"
BYTEDANCE_VC_APPID="your_appid"
```

**方式二：Shell 配置** — 添加到 `~/.zshrc` 或 `~/.bashrc`：

```bash
export TIKHUB_TOKEN="your_token"
export BYTEDANCE_VC_TOKEN="your_token"
export BYTEDANCE_VC_APPID="your_appid"
```

> 详细申请教程见 [TikHub 申请指南](./docs/tikhub-setup.md) 和 [火山引擎开通指南](./docs/bytedance-vc-setup.md)

---

## 执行步骤

### 步骤0: 判断输入类型

根据用户输入判断处理模式：

- **在线视频模式**：输入为 URL（包含 `http`/`https`、`douyin.com`、`v.douyin.com` 等）→ 从步骤1开始，完整执行
- **本地文件模式**：输入为本地文件路径（如 `/path/to/video.mp4`、`~/Downloads/audio.mp3`）→ **跳过步骤1和步骤2**，根据文件类型决定：
  - 本地**视频**文件（`.mp4`、`.mov`、`.avi`、`.mkv` 等）→ 从步骤3（提取音频）开始
  - 本地**音频**文件（`.mp3`、`.wav`、`.m4a`、`.flac` 等）→ **跳过步骤3**，直接从步骤4（语音识别）开始

### 步骤0.5: 环境检查（必须首先执行）

在开始任何处理之前，**必须先执行以下检查脚本**，任何一项缺失则停止并提示用户：

> **注意：** 本地文件模式下不需要检查 `TIKHUB_TOKEN`，仅需 `BYTEDANCE_VC_TOKEN`、`BYTEDANCE_VC_APPID` 和 `FFmpeg`。

```bash
# 加载环境变量：优先从 .env 文件读取，其次从 shell 配置读取
SKILL_DIR="$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")"
if [ -f "$HOME/.claude/skills/video-to-subtitle-summary/.env" ]; then
  set -a; source "$HOME/.claude/skills/video-to-subtitle-summary/.env"; set +a
fi
source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null

MISSING=""
[ -z "$TIKHUB_TOKEN" ] && MISSING="$MISSING TIKHUB_TOKEN"
[ -z "$BYTEDANCE_VC_TOKEN" ] && MISSING="$MISSING BYTEDANCE_VC_TOKEN"
[ -z "$BYTEDANCE_VC_APPID" ] && MISSING="$MISSING BYTEDANCE_VC_APPID"
which ffmpeg >/dev/null 2>&1 || MISSING="$MISSING FFmpeg"
if [ -n "$MISSING" ]; then
  echo "ERROR: 缺少必需依赖:$MISSING"
  echo "请配置环境变量（.env 文件或 shell 配置）:"
  echo '  TIKHUB_TOKEN="your_token"'
  echo '  BYTEDANCE_VC_TOKEN="your_token"'
  echo '  BYTEDANCE_VC_APPID="your_appid"'
  echo "FFmpeg 安装: brew install ffmpeg (macOS) / sudo apt install ffmpeg (Linux)"
  exit 1
else
  echo "OK: 所有依赖就绪"
  echo "TIKHUB_TOKEN=${TIKHUB_TOKEN:0:10}..."
  echo "BYTEDANCE_VC_APPID=$BYTEDANCE_VC_APPID"
fi
```

**如果检查失败，立即停止并告知用户缺少哪些配置，不要继续后续步骤。**

**⚠️ Claude Code 注意：** 由于 Bash 工具的限制，`source` 设置的变量无法在后续独立命令中使用。执行时使用以下方式提取环境变量：

```bash
# 从 .env 文件或 shell 配置提取环境变量
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env"
if [ -f "$ENV_FILE" ]; then
  TIKHUB_TOKEN=$(grep "TIKHUB_TOKEN" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
  BYTEDANCE_VC_TOKEN=$(grep "BYTEDANCE_VC_TOKEN" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
  BYTEDANCE_VC_APPID=$(grep "BYTEDANCE_VC_APPID" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
else
  TIKHUB_TOKEN=$(grep "TIKHUB_TOKEN" ~/.zshrc ~/.bashrc 2>/dev/null | head -1 | cut -d'"' -f2)
  BYTEDANCE_VC_TOKEN=$(grep "BYTEDANCE_VC_TOKEN" ~/.zshrc ~/.bashrc 2>/dev/null | head -1 | cut -d'"' -f2)
  BYTEDANCE_VC_APPID=$(grep "BYTEDANCE_VC_APPID" ~/.zshrc ~/.bashrc 2>/dev/null | head -1 | cut -d'"' -f2)
fi
```

### 步骤1: 获取视频信息（仅在线视频模式）

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env" && if [ -f "$ENV_FILE" ]; then TIKHUB_TOKEN=$(grep "TIKHUB_TOKEN" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'"); else TIKHUB_TOKEN=$(grep "TIKHUB_TOKEN" ~/.zshrc ~/.bashrc 2>/dev/null | head -1 | cut -d'"' -f2); fi && curl -s -X GET "https://api.tikhub.io/api/v1/douyin/web/fetch_one_video_by_share_url?share_url={ENCODED_URL}" -H "Authorization: Bearer $TIKHUB_TOKEN" -H "Accept: application/json"
```

**提取关键字段：**

```bash
jq '{
  aweme_id: .data.aweme_detail.aweme_id,
  desc: .data.aweme_detail.desc,
  author: .data.aweme_detail.author.nickname,
  video_url: .data.aweme_detail.video.play_addr.url_list[0]
}'
```

### 步骤2: 下载视频（仅在线视频模式）

```bash
mkdir -p /tmp/video_analysis/{VIDEO_ID}
curl -L -o /tmp/video_analysis/{VIDEO_ID}/video.mp4 -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" "{VIDEO_URL}"
```

### 步骤3: 提取音频（本地音频文件可跳过）

> **本地文件模式：** 如果输入是本地视频文件，将 `{VIDEO_ID}` 替换为文件名（不含扩展名），输入路径替换 `/tmp/video_analysis/{VIDEO_ID}/video.mp4`。如果输入已经是音频文件（`.mp3`、`.wav` 等），直接跳到步骤4，使用该文件作为音频输入。

```bash
ffmpeg -i /tmp/video_analysis/{VIDEO_ID}/video.mp4 -q:a 0 -map a -y /tmp/video_analysis/{VIDEO_ID}/audio.mp3
```

### 步骤4: 提交语音识别

**⚠️ Authorization 格式：`Bearer;token`（分号连接，无空格）**

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env" && if [ -f "$ENV_FILE" ]; then BYTEDANCE_VC_TOKEN=$(grep "BYTEDANCE_VC_TOKEN" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'"); BYTEDANCE_VC_APPID=$(grep "BYTEDANCE_VC_APPID" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'"); else BYTEDANCE_VC_TOKEN=$(grep "BYTEDANCE_VC_TOKEN" ~/.zshrc ~/.bashrc 2>/dev/null | head -1 | cut -d'"' -f2); BYTEDANCE_VC_APPID=$(grep "BYTEDANCE_VC_APPID" ~/.zshrc ~/.bashrc 2>/dev/null | head -1 | cut -d'"' -f2); fi && curl -s -X POST "https://openspeech.bytedance.com/api/v1/vc/submit?appid=$BYTEDANCE_VC_APPID&language=zh-CN&words_per_line=20&max_lines=2" -H "Content-Type: audio/mpeg" -H "Authorization: Bearer;$BYTEDANCE_VC_TOKEN" --data-binary @/tmp/video_analysis/{VIDEO_ID}/audio.mp3

# 返回: {"id":"task-id","code":0,"message":"Success"}
```

### 步骤5: 轮询获取字幕

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env" && if [ -f "$ENV_FILE" ]; then BYTEDANCE_VC_TOKEN=$(grep "BYTEDANCE_VC_TOKEN" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'"); BYTEDANCE_VC_APPID=$(grep "BYTEDANCE_VC_APPID" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'"); else BYTEDANCE_VC_TOKEN=$(grep "BYTEDANCE_VC_TOKEN" ~/.zshrc ~/.bashrc 2>/dev/null | head -1 | cut -d'"' -f2); BYTEDANCE_VC_APPID=$(grep "BYTEDANCE_VC_APPID" ~/.zshrc ~/.bashrc 2>/dev/null | head -1 | cut -d'"' -f2); fi && curl -s "https://openspeech.bytedance.com/api/v1/vc/query?appid=$BYTEDANCE_VC_APPID&id={TASK_ID}" -H "Authorization: Bearer;$BYTEDANCE_VC_TOKEN"

# code=0 成功，code=2000 处理中（等待5秒后重试）
```

### 步骤6: 处理字幕

```bash
# 提取纯文本
cat subtitle.json | jq -r '.utterances[].text' | tr '\n' ' ' > text.txt
```

**生成 SRT 格式：**

```python
import json
with open('subtitle.json', 'r') as f:
    data = json.load(f)

def ms_to_srt(ms):
    h, m, s, millis = ms//3600000, (ms%3600000)//60000, (ms%60000)//1000, ms%1000
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"

with open('subtitle.srt', 'w') as f:
    for i, u in enumerate(data['utterances'], 1):
        f.write(f"{i}\n{ms_to_srt(u['start_time'])} --> {ms_to_srt(u['end_time'])}\n{u['text']}\n\n")
```

### 步骤7: AI生成总结

**直接由 Claude 完成，无需调用第三方 API。**

读取字幕文本后生成：

1. **标题**：简洁概括，不超过30字
2. **摘要**：主要观点和关键信息，200-300字
3. **要点**：核心观点的结构化列表

---

## 输出格式

```markdown
## 视频分析结果

### 视频信息

| 项目   | 内容 |
| ------ | ---- |
| 视频ID | xxx  |
| 作者   | xxx  |
| 时长   | xxx  |

### AI生成标题

xxx

### AI摘要

xxx

### 核心要点

1. xxx
2. xxx

### 生成文件

- 视频: /tmp/video_analysis/{ID}/video.mp4
- 音频: /tmp/video_analysis/{ID}/audio.mp3
- SRT字幕: /tmp/video_analysis/{ID}/subtitle.srt
- 纯文本: /tmp/video_analysis/{ID}/text.txt
```

---

## 常见问题

| 问题             | 解决方案                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------- |
| **缺少环境变量** | 在 `.env` 文件或 `~/.zshrc`/`~/.bashrc` 中配置，详见 [申请教程](./docs/)                          |
| 环境变量未生效   | 执行 `source ~/.zshrc` 或重启终端；使用 `.env` 文件则无需此步骤                                   |
| TikHub API 404   | 端点: `/api/v1/douyin/web/fetch_one_video_by_share_url`                                           |
| 字节API认证失败  | Authorization: `Bearer;token`（分号无空格）                                                       |
| 视频下载失败     | 添加 User-Agent header                                                                            |
| FFmpeg 找不到    | macOS: `brew install ffmpeg` / Linux: `sudo apt install ffmpeg` / Windows: `choco install ffmpeg` |
| curl 命令报错    | 使用单行命令，避免多行换行                                                                        |
