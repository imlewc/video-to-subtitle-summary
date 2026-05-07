---
name: video-to-subtitle-summary
description: Use when user provides a short video platform URL (Douyin, Xiaohongshu, Bilibili, etc.) or a local video/audio file path and wants to extract subtitles and generate AI summary. Triggers on URLs like v.douyin.com, xhslink.com, xiaohongshu.com, bilibili.com, b23.tv, share links, or local file paths ending in .mp4/.mp3/.wav etc.
args: <video_url_or_file_path> - 视频链接（抖音/小红书/B站等）或本地视频/音频文件路径（必需）
---

# 视频转字幕与 AI 总结技能

## Overview

将短视频平台（抖音、小红书、B 站、YouTube 等）视频或本地视频/音频文件转换为字幕文本并生成 AI 摘要。

**核心流程：**
- **在线视频：** 获取视频信息 → 下载视频/直接抓字幕 → 选择字幕后端 → 生成字幕 → AI 总结
- **本地文件：** 提取音频（如需） → 选择字幕后端 → 生成字幕 → AI 总结

默认使用本地 `faster-whisper`，也支持通过环境变量切换到火山引擎 VC API。
YouTube 优先使用 `yt-dlp` 直接抓取人工字幕或自动字幕；只有没有可用字幕时，才需要下载音视频并回退到 ASR。

## When to Use

- 用户提供短视频平台链接（抖音、小红书、B 站、YouTube 等），要求提取字幕或生成总结
- 用户提供本地视频/音频文件路径，要求转字幕或生成总结
- 需要将视频内容转为文字

**不适用于：** 实时语音识别、直播字幕

## 外部依赖

| 依赖 | 用途 | 必需 |
| --- | --- | --- |
| **TikHub API** | 获取抖音/小红书/B 站视频信息和下载地址 | 仅抖音/小红书/B 站需要 |
| **Python 3.9+** | 运行 `faster-whisper` helper | 仅 `ASR_BACKEND=faster-whisper` 时需要 |
| **faster-whisper** | 本地语音转文字 | 仅 `ASR_BACKEND=faster-whisper` 时需要 |
| **字节跳动 VC API** | 云端语音转文字 | 仅 `ASR_BACKEND=volcengine` 时需要 |
| **FFmpeg** | 从视频提取音频 | ✅（音频文件可跳过） |
| **yt-dlp** | 下载 B 站视频；抓取 YouTube 字幕 | 仅 B 站或 YouTube 需要 |

## 环境变量

通过环境变量读取，支持以下任意方式配置：

**方式一：.env 文件（推荐）** — 在 skill 目录下创建 `.env` 文件：

```bash
ASR_BACKEND="faster-whisper"
TIKHUB_TOKEN="your_token"

FW_MODEL_SIZE="small"
FW_DEVICE="auto"
FW_COMPUTE_TYPE=""

BYTEDANCE_VC_TOKEN="your_token"
BYTEDANCE_VC_APPID="your_appid"
```

**方式二：Shell 配置** — 添加到 `~/.zshrc` 或 `~/.bashrc`：

```bash
export ASR_BACKEND="faster-whisper"
export TIKHUB_TOKEN="your_token"

export FW_MODEL_SIZE="small"
export FW_DEVICE="auto"
export FW_COMPUTE_TYPE=""

export BYTEDANCE_VC_TOKEN="your_token"
export BYTEDANCE_VC_APPID="your_appid"
```

说明：
- `ASR_BACKEND`：可选，默认 `faster-whisper`
- `TIKHUB_TOKEN`：仅抖音/小红书/B 站需要；YouTube 不需要
- `FW_MODEL_SIZE` / `FW_DEVICE` / `FW_COMPUTE_TYPE`：仅 `faster-whisper` 后端使用
- `BYTEDANCE_VC_TOKEN` / `BYTEDANCE_VC_APPID`：仅 `volcengine` 后端使用

> 安装与运行时说明见 [TikHub 申请指南](./docs/tikhub-setup.md)、[faster-whisper 安装指南](./docs/faster-whisper-setup.md) 和 [火山引擎开通指南](./docs/bytedance-vc-setup.md)

## 执行步骤

### 步骤 0：判断输入类型

根据用户输入判断处理模式：

- **在线视频模式**：输入为 URL
  - **抖音/TikTok**：`douyin.com`、`v.douyin.com`、`tiktok.com`
  - **小红书**：`xiaohongshu.com`、`xhslink.com`
  - **B 站**：`bilibili.com`、`b23.tv`
  - **YouTube**：`youtube.com`、`youtu.be`
- **本地文件模式**：输入为本地文件路径
  - 本地**视频**文件（`.mp4`、`.mov`、`.avi`、`.mkv` 等）→ 从步骤 3（提取音频）开始
  - 本地**音频**文件（`.mp3`、`.wav`、`.m4a`、`.flac` 等）→ 跳过步骤 3，直接从步骤 4（转写）开始

### 步骤 0.5：读取后端配置

先读取 `ASR_BACKEND`，未配置时默认使用 `faster-whisper`：

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env"

read_env() {
  local key="$1"
  if [ -f "$ENV_FILE" ]; then
    grep "^${key}=" "$ENV_FILE" | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'"
  else
    printenv "$key"
  fi
}

ASR_BACKEND="$(read_env ASR_BACKEND)"
[ -z "$ASR_BACKEND" ] && ASR_BACKEND="faster-whisper"

echo "ASR_BACKEND=$ASR_BACKEND"
```

支持值：
- `faster-whisper`
- `volcengine`

### 步骤 0.6：环境检查（必须首先执行）

在开始任何处理之前，先检查当前模式和当前字幕后端需要的依赖。

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env"

read_env() {
  local key="$1"
  if [ -f "$ENV_FILE" ]; then
    grep "^${key}=" "$ENV_FILE" | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'"
  else
    printenv "$key"
  fi
}

ASR_BACKEND="$(read_env ASR_BACKEND)"
[ -z "$ASR_BACKEND" ] && ASR_BACKEND="faster-whisper"
TIKHUB_TOKEN="$(read_env TIKHUB_TOKEN)"
BYTEDANCE_VC_TOKEN="$(read_env BYTEDANCE_VC_TOKEN)"
BYTEDANCE_VC_APPID="$(read_env BYTEDANCE_VC_APPID)"

MISSING=""

if [ "{INPUT_MODE}" = "url" ]; then
  if [ "{PLATFORM}" = "douyin" ] || [ "{PLATFORM}" = "xiaohongshu" ] || [ "{PLATFORM}" = "bilibili" ]; then
    [ -z "$TIKHUB_TOKEN" ] && MISSING="$MISSING TIKHUB_TOKEN"
  fi
  if [ "{PLATFORM}" = "bilibili" ] || [ "{PLATFORM}" = "youtube" ]; then
    command -v yt-dlp >/dev/null 2>&1 || MISSING="$MISSING yt-dlp"
  fi
fi

if [ "{NEEDS_FFMPEG}" = "yes" ] && [ "{PLATFORM}" != "youtube" ]; then
  command -v ffmpeg >/dev/null 2>&1 || MISSING="$MISSING ffmpeg"
fi

if [ "$ASR_BACKEND" = "faster-whisper" ]; then
  command -v python3 >/dev/null 2>&1 || MISSING="$MISSING python3"
  python3 - <<'PY' >/dev/null 2>&1 || MISSING="$MISSING faster-whisper"
import faster_whisper
import ctranslate2
PY
elif [ "$ASR_BACKEND" = "volcengine" ]; then
  [ -z "$BYTEDANCE_VC_TOKEN" ] && MISSING="$MISSING BYTEDANCE_VC_TOKEN"
  [ -z "$BYTEDANCE_VC_APPID" ] && MISSING="$MISSING BYTEDANCE_VC_APPID"
else
  MISSING="$MISSING invalid_ASR_BACKEND"
fi

if [ -n "$MISSING" ]; then
  echo "ERROR: 缺少必需依赖或配置:$MISSING"
  echo "ASR_BACKEND=$ASR_BACKEND"
  echo "可选值: faster-whisper / volcengine"
  exit 1
else
  echo "OK: 运行依赖已就绪 (ASR_BACKEND=$ASR_BACKEND)"
fi
```

如果检查失败：
- `ASR_BACKEND=faster-whisper`：参考 [docs/faster-whisper-setup.md](./docs/faster-whisper-setup.md)
- `ASR_BACKEND=volcengine`：参考 [docs/bytedance-vc-setup.md](./docs/bytedance-vc-setup.md)

### 步骤 1：获取视频信息（仅在线视频模式）

根据 URL 域名识别平台，调用对应的 TikHub API 端点：

| 平台 | URL 特征 | API 端点 |
| --- | --- | --- |
| 抖音/TikTok | `douyin.com`、`tiktok.com` | `/api/v1/hybrid/video_data` |
| 小红书 | `xiaohongshu.com`、`xhslink.com` | `/api/v1/xiaohongshu/web/get_note_info_v7` |
| B 站 | `bilibili.com`、`b23.tv` | `/api/v1/bilibili/web/fetch_one_video_v3` |
| YouTube | `youtube.com`、`youtu.be` | 不调用 TikHub，直接进入步骤 2 |

**抖音/TikTok：**

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env"
if [ -f "$ENV_FILE" ]; then
  TIKHUB_TOKEN=$(grep "^TIKHUB_TOKEN=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
else
  TIKHUB_TOKEN="$TIKHUB_TOKEN"
fi

curl -s -X GET "https://api.tikhub.io/api/v1/hybrid/video_data?url={ENCODED_URL}&minimal=true" \
  -H "Authorization: Bearer $TIKHUB_TOKEN" \
  -H "Accept: application/json"
```

提取关键字段：

```bash
jq '{
  video_id: .data.aweme_id,
  desc: .data.desc,
  author: .data.author.nickname,
  video_url: .data.video.play_addr.url_list[0]
}'
```

**小红书：**

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env"
if [ -f "$ENV_FILE" ]; then
  TIKHUB_TOKEN=$(grep "^TIKHUB_TOKEN=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
else
  TIKHUB_TOKEN="$TIKHUB_TOKEN"
fi

curl -s -X GET "https://api.tikhub.io/api/v1/xiaohongshu/web/get_note_info_v7?share_text={ENCODED_URL}" \
  -H "Authorization: Bearer $TIKHUB_TOKEN" \
  -H "Accept: application/json"
```

提取关键字段：

```bash
jq '{
  note_id: .data[0].note_list[0].note_id,
  title: .data[0].note_list[0].title,
  author: .data[0].user.nickname,
  type: .data[0].note_list[0].type,
  video_url: .data[0].note_list[0].video.consumer.origin_video_key
}'
```

> 小红书视频下载地址格式：`https://sns-video-bd.xhscdn.com/{origin_video_key}`

**B 站：**

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env"
if [ -f "$ENV_FILE" ]; then
  TIKHUB_TOKEN=$(grep "^TIKHUB_TOKEN=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
else
  TIKHUB_TOKEN="$TIKHUB_TOKEN"
fi

curl -s -X GET "https://api.tikhub.io/api/v1/bilibili/web/fetch_one_video_v3?url={ENCODED_URL}" \
  -H "Authorization: Bearer $TIKHUB_TOKEN" \
  -H "Accept: application/json"
```

提取关键字段：

```bash
jq '{
  bvid: .data.bvid,
  title: .data.title,
  author: .data.owner.name,
  duration: .data.duration,
  desc: .data.desc
}'
```

> B 站 API 只返回元数据，不含直接下载地址。步骤 2 中使用 `yt-dlp` 下载。

### 步骤 2：下载视频（仅在线视频模式）

根据平台使用不同的下载方式：

**YouTube（优先直接抓字幕，不下载视频）：**

```bash
mkdir -p /tmp/video_analysis/{VIDEO_ID}
python3 "$HOME/.claude/skills/video-to-subtitle-summary/scripts/download_youtube_subtitles.py" \
  "https://www.youtube.com/watch?v={VIDEO_ID}" \
  --output-dir /tmp/video_analysis/{VIDEO_ID} \
  --languages zh-Hans,zh-Hant,zh,en
```

输出文件固定为：
- `/tmp/video_analysis/{VIDEO_ID}/subtitle.srt`
- `/tmp/video_analysis/{VIDEO_ID}/text.txt`

如果命令提示没有可用字幕，再使用 `yt-dlp` 下载音频或视频，并从步骤 3 继续走 `ASR_BACKEND`。

**抖音/TikTok：**

```bash
mkdir -p /tmp/video_analysis/{VIDEO_ID}
curl -L -o /tmp/video_analysis/{VIDEO_ID}/video.mp4 \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  "{VIDEO_URL}"
```

**小红书：**

```bash
mkdir -p /tmp/video_analysis/{NOTE_ID}
curl -L -o /tmp/video_analysis/{NOTE_ID}/video.mp4 \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  "https://sns-video-bd.xhscdn.com/{ORIGIN_VIDEO_KEY}"
```

**B 站：**

```bash
mkdir -p /tmp/video_analysis/{BVID}
yt-dlp -o /tmp/video_analysis/{BVID}/video.mp4 "https://www.bilibili.com/video/{BVID}/"
```

### 步骤 3：提取音频（本地音频文件可跳过）

> 本地文件模式下，如果输入是本地视频文件，将 `{VIDEO_ID}` 替换为文件名（不含扩展名），输入路径替换为实际视频路径。

```bash
ffmpeg -i /tmp/video_analysis/{VIDEO_ID}/video.mp4 -q:a 0 -map a -y /tmp/video_analysis/{VIDEO_ID}/audio.mp3
```

### 步骤 4：根据 `ASR_BACKEND` 选择字幕后端

如果平台是 YouTube 且步骤 2 已成功生成 `subtitle.srt` 和 `text.txt`，跳过本步骤，直接进入步骤 5 总结。

#### 方案 A：`ASR_BACKEND=faster-whisper`（默认）

helper 路径：

```bash
$HOME/.claude/skills/video-to-subtitle-summary/scripts/transcribe_faster_whisper.py
```

执行命令：

```bash
python3 "$HOME/.claude/skills/video-to-subtitle-summary/scripts/transcribe_faster_whisper.py" \
  /tmp/video_analysis/{VIDEO_ID}/audio.mp3 \
  --output-dir /tmp/video_analysis/{VIDEO_ID}
```

说明：
- helper 会自动读取 `FW_MODEL_SIZE`、`FW_DEVICE`、`FW_COMPUTE_TYPE`
- 当 `FW_DEVICE=auto` 时，只有检测到 NVIDIA/CUDA 才会使用 `device="cuda"`
- 输出文件固定为：
  - `/tmp/video_analysis/{VIDEO_ID}/subtitle.srt`
  - `/tmp/video_analysis/{VIDEO_ID}/text.txt`

#### 方案 B：`ASR_BACKEND=volcengine`

提交任务：

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env"
if [ -f "$ENV_FILE" ]; then
  BYTEDANCE_VC_TOKEN=$(grep "^BYTEDANCE_VC_TOKEN=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
  BYTEDANCE_VC_APPID=$(grep "^BYTEDANCE_VC_APPID=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
else
  BYTEDANCE_VC_TOKEN="$BYTEDANCE_VC_TOKEN"
  BYTEDANCE_VC_APPID="$BYTEDANCE_VC_APPID"
fi

curl -s -X POST "https://openspeech.bytedance.com/api/v1/vc/submit?appid=$BYTEDANCE_VC_APPID&language=zh-CN&words_per_line=20&max_lines=2" \
  -H "Content-Type: audio/mpeg" \
  -H "Authorization: Bearer;$BYTEDANCE_VC_TOKEN" \
  --data-binary @/tmp/video_analysis/{VIDEO_ID}/audio.mp3
```

轮询结果：

```bash
ENV_FILE="$HOME/.claude/skills/video-to-subtitle-summary/.env"
if [ -f "$ENV_FILE" ]; then
  BYTEDANCE_VC_TOKEN=$(grep "^BYTEDANCE_VC_TOKEN=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
  BYTEDANCE_VC_APPID=$(grep "^BYTEDANCE_VC_APPID=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
else
  BYTEDANCE_VC_TOKEN="$BYTEDANCE_VC_TOKEN"
  BYTEDANCE_VC_APPID="$BYTEDANCE_VC_APPID"
fi

curl -s "https://openspeech.bytedance.com/api/v1/vc/query?appid=$BYTEDANCE_VC_APPID&id={TASK_ID}" \
  -H "Authorization: Bearer;$BYTEDANCE_VC_TOKEN"
```

结果处理：

```bash
jq -r '.utterances[].text' subtitle.json | tr '\n' ' ' > /tmp/video_analysis/{VIDEO_ID}/text.txt
```

生成 SRT：

```python
import json

with open('subtitle.json', 'r') as f:
    data = json.load(f)

def ms_to_srt(ms):
    h, m, s, millis = ms//3600000, (ms%3600000)//60000, (ms%60000)//1000, ms%1000
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"

with open('/tmp/video_analysis/{VIDEO_ID}/subtitle.srt', 'w') as f:
    for i, u in enumerate(data['utterances'], 1):
        f.write(f"{i}\n{ms_to_srt(u['start_time'])} --> {ms_to_srt(u['end_time'])}\n{u['text']}\n\n")
```

### 步骤 5：AI 生成总结

直接由 Claude 完成，无需调用第三方总结 API。

读取 `text.txt` 后生成。

总结时应一并提供以下上下文：
- **原视频标题**：如果是在线视频，优先使用平台返回的原始标题字段
  - 抖音/TikTok：优先 `desc`
  - 小红书：优先 `title`
  - B 站：优先 `title`
- **兜底标题**：如果没有明确标题，可使用文件名或视频 ID 作为参考标识
- **字幕说明**：明确告诉 Claude，正文可能来自 YouTube 字幕、自动字幕或语音识别，可能存在同音字、断句、专有名词识别错误；在不偏离原意的前提下，可以结合原视频标题和上下文做适度修正

推荐直接使用如下提示方式：

```text
以下是一个视频的分析素材，请基于这些信息生成总结：

原视频标题：{ORIGINAL_TITLE}
来源平台：{PLATFORM}
作者：{AUTHOR}
说明：下面的正文来自平台字幕、自动字幕或语音识别，可能存在少量识别误差、断句问题或专有名词错误。请以原视频标题和上下文为参考，在不改变原意的前提下做适度修正，再完成总结。

语音识别文本：
{TEXT_CONTENT}

请输出：
1. AI生成标题：简洁概括，不超过30字；可以参考原视频标题，但不要机械照抄，必要时可根据正文纠正明显错误
2. AI摘要：提炼主要观点和关键信息，200-300字
3. 核心要点：输出3-5条结构化要点
```

如果原视频标题与正文明显冲突：
- 优先以正文主旨为准
- 保留“可能因语音识别存在误差”的判断，不要凭空补充未出现的信息

1. **标题**：简洁概括，不超过 30 字
2. **摘要**：主要观点和关键信息，200-300 字
3. **要点**：核心观点的结构化列表

## 输出格式

```markdown
## 视频分析结果

### 视频信息

| 项目 | 内容 |
| --- | --- |
| 视频ID | xxx |
| 作者 | xxx |
| 时长 | xxx |

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

## 常见问题

| 问题 | 解决方案 |
| --- | --- |
| **缺少环境变量** | 先确认 `ASR_BACKEND`；在线视频模式下仍需 `TIKHUB_TOKEN`；火山后端需要 `BYTEDANCE_VC_TOKEN` 和 `BYTEDANCE_VC_APPID` |
| `ASR_BACKEND` 无效 | 只支持 `faster-whisper` 和 `volcengine` |
| `faster-whisper` 导入失败 | 执行 `python3 -m pip install -U faster-whisper` |
| 火山 API 认证失败 | Authorization 必须是 `Bearer;token`（分号无空格） |
| 首次运行较慢 | `faster-whisper` 首次会下载模型，等待下载完成后重试 |
| CUDA 环境不可用 | `FW_DEVICE=auto` 会自动回退到 CPU；只有 NVIDIA/CUDA 才走 GPU |
| 视频下载失败 | 抖音/小红书加 `User-Agent`；B 站使用 `yt-dlp` |
| FFmpeg 找不到 | macOS: `brew install ffmpeg` / Linux: `sudo apt install ffmpeg` / Windows: `choco install ffmpeg` |
| yt-dlp 找不到 | macOS: `brew install yt-dlp` / 通用: `python3 -m pip install -U yt-dlp`（B 站 / YouTube 需要） |
