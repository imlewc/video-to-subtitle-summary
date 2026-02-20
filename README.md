# video-to-subtitle-summary

一个 Claude Code Skill，自动将抖音视频或本地视频/音频文件转换为字幕文本并生成 AI 摘要。

**核心流程：**
- **在线视频：** 提供抖音链接 → 自动下载视频 → 提取音频 → 语音识别 → 生成字幕 → AI 总结
- **本地文件：** 提供本地视频/音频路径 → 提取音频（如需） → 语音识别 → 生成字幕 → AI 总结

[English](./README_en.md)

## 效果展示

输入一个抖音视频链接或本地文件路径，自动输出：

```markdown
## 视频分析结果

### 视频信息
| 项目 | 内容 |
|------|------|
| 视频ID | 7456789012345 |
| 作者 | 某知识博主 |
| 时长 | 3:25 |

### AI生成标题
深度解析2024年AI发展趋势与个人应对策略

### AI摘要
视频主要讨论了2024年AI技术的发展趋势，包括大模型的演进方向、
AI在各行业的落地应用，以及普通人如何把握AI时代的机遇...

### 核心要点
1. 大模型正在从"通用智能"向"专业智能"演进
2. AI应用层的创业机会远大于基础模型层
3. 掌握AI工具使用能力将成为职场核心竞争力

### 生成文件
- 视频: /tmp/video_analysis/7456789012345/video.mp4
- 音频: /tmp/video_analysis/7456789012345/audio.mp3
- SRT字幕: /tmp/video_analysis/7456789012345/subtitle.srt
- 纯文本: /tmp/video_analysis/7456789012345/text.txt
```

## 前置条件

| 依赖 | 说明 |
|------|------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Anthropic 官方 CLI 工具 |
| [FFmpeg](https://ffmpeg.org/) | 音视频处理工具 |
| [TikHub](https://tikhub.io/) 账号 | 获取抖音视频信息和下载地址（仅在线视频需要） |
| [火山引擎](https://www.volcengine.com/) 账号 | 字节跳动语音识别服务 |

## 快速安装

### 1. 安装 FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows (使用 Chocolatey)
choco install ffmpeg
```

### 2. 复制 Skill 到 Claude Code

```bash
# 克隆仓库
git clone https://github.com/imlewc/video-to-subtitle-summary.git

# 复制到 Claude Code skills 目录
cp -r video-to-subtitle-summary ~/.claude/skills/video-to-subtitle-summary
```

### 3. 配置环境变量

申请 API 凭证（参见下方教程链接），然后配置环境变量。

**方式一：使用 .env 文件（推荐）**

```bash
cp .env.example ~/.claude/skills/video-to-subtitle-summary/.env
# 编辑 .env 文件填入你的凭证
```

**方式二：写入 Shell 配置**

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
export TIKHUB_TOKEN="your_tikhub_api_token"
export BYTEDANCE_VC_TOKEN="your_bytedance_vc_token"
export BYTEDANCE_VC_APPID="your_bytedance_vc_appid"
```

## 使用方法

### 在线视频

在 Claude Code 中直接发送抖音链接即可：

```
请帮我提取这个视频的字幕并总结：https://v.douyin.com/xxxxxx/
```

或者使用 skill 命令：

```
/video-to-subtitle-summary https://v.douyin.com/xxxxxx/
```

### 本地文件

直接提供本地视频或音频文件路径：

```
请帮我提取字幕并总结：/Users/me/Downloads/video.mp4
```

```
/video-to-subtitle-summary ~/Desktop/recording.mp3
```

> 本地文件模式会自动跳过视频下载步骤，音频文件还会跳过音频提取步骤，无需 TikHub API。

## API 申请教程

| 服务 | 教程 | 免费额度 |
|------|------|---------|
| TikHub API | [申请教程](./docs/tikhub-setup.md) | 100 次/天（免费套餐） |
| 火山引擎语音识别 | [开通教程](./docs/bytedance-vc-setup.md) | 新用户赠送约 2 万次 |

## 费用说明

| 服务 | 免费额度 | 付费价格 |
|------|---------|---------|
| TikHub API | 100 次/天 | $0.001/次起 |
| 火山引擎语音识别 | 新用户 ~2 万次 | ¥4.5/小时起 |
| Claude Code | 取决于你的订阅计划 | - |

> 对于个人日常使用，免费额度通常足够。

## 项目结构

```
video-to-subtitle-summary/
├── README.md                     # 项目介绍（本文件）
├── README_en.md                  # English README
├── LICENSE                       # MIT 协议
├── SKILL.md                      # Skill 本体
├── .env.example                  # 环境变量模板
└── docs/
    ├── tikhub-setup.md           # TikHub API 申请教程
    └── bytedance-vc-setup.md     # 火山引擎语音识别开通教程
```

## License

[MIT](./LICENSE)
