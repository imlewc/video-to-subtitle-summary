# video-to-subtitle-summary

A Claude Code Skill that automatically converts Douyin (TikTok China) videos into subtitle text and generates AI summaries.

**Core Flow:** Provide a Douyin link → Auto-download video → Extract audio → Speech recognition → Generate subtitles → AI summary

[中文文档](./README.md)

## Demo

Give it a Douyin video link, and it automatically outputs:

```markdown
## Video Analysis Result

### Video Info
| Field | Value |
|-------|-------|
| Video ID | 7456789012345 |
| Author | Knowledge Blogger |
| Duration | 3:25 |

### AI Generated Title
Deep Analysis of 2024 AI Development Trends and Personal Strategies

### AI Summary
The video discusses the development trends of AI technology in 2024,
including the evolution of large models, AI applications across industries,
and how individuals can seize opportunities in the AI era...

### Key Points
1. Large models are evolving from "general intelligence" to "specialized intelligence"
2. AI application layer offers more startup opportunities than the foundation model layer
3. Mastering AI tools will become a core workplace competency

### Generated Files
- Video: /tmp/video_analysis/7456789012345/video.mp4
- Audio: /tmp/video_analysis/7456789012345/audio.mp3
- SRT Subtitles: /tmp/video_analysis/7456789012345/subtitle.srt
- Plain Text: /tmp/video_analysis/7456789012345/text.txt
```

## Prerequisites

| Dependency | Description |
|-----------|-------------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Anthropic's official CLI tool |
| [FFmpeg](https://ffmpeg.org/) | Audio/video processing tool |
| [TikHub](https://tikhub.io/) account | Fetch Douyin video info and download URLs |
| [Volcengine](https://www.volcengine.com/) account | ByteDance speech recognition service |

## Quick Start

### 1. Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg
```

### 2. Copy the Skill to Claude Code

```bash
# Clone the repository
git clone https://github.com/ultrasev/video-to-subtitle-summary.git

# Copy to Claude Code skills directory
cp -r video-to-subtitle-summary ~/.claude/skills/video-to-subtitle-summary
```

### 3. Configure Environment Variables

Apply for API credentials (see tutorial links below), then configure environment variables.

**Option 1: Using .env file (Recommended)**

```bash
cp .env.example ~/.claude/skills/video-to-subtitle-summary/.env
# Edit the .env file with your credentials
```

**Option 2: Add to Shell config**

```bash
# Add to ~/.zshrc or ~/.bashrc
export TIKHUB_TOKEN="your_tikhub_api_token"
export BYTEDANCE_VC_TOKEN="your_bytedance_vc_token"
export BYTEDANCE_VC_APPID="your_bytedance_vc_appid"
```

## Usage

Simply send a Douyin link in Claude Code:

```
Please extract subtitles and summarize this video: https://v.douyin.com/xxxxxx/
```

Or use the skill command:

```
/video-to-subtitle-summary https://v.douyin.com/xxxxxx/
```

## API Setup Guides

| Service | Guide | Free Tier |
|---------|-------|-----------|
| TikHub API | [Setup Guide](./docs/tikhub-setup.md) | 100 requests/day |
| Volcengine Speech Recognition | [Setup Guide](./docs/bytedance-vc-setup.md) | ~20,000 free requests for new users |

## Pricing

| Service | Free Tier | Paid Pricing |
|---------|-----------|-------------|
| TikHub API | 100 requests/day | From $0.001/request |
| Volcengine Speech Recognition | ~20,000 requests for new users | From ¥4.5/hour |
| Claude Code | Depends on your subscription plan | - |

> For personal daily use, the free tier is usually sufficient.

## Project Structure

```
video-to-subtitle-summary/
├── README.md                     # Chinese README
├── README_en.md                  # English README (this file)
├── LICENSE                       # MIT License
├── SKILL.md                      # The skill itself
├── .env.example                  # Environment variable template
└── docs/
    ├── tikhub-setup.md           # TikHub API setup guide
    └── bytedance-vc-setup.md     # Volcengine speech recognition setup guide
```

## License

[MIT](./LICENSE)
