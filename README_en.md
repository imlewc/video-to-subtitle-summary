# video-to-subtitle-summary

A Claude Code Skill that automatically converts short video platform (Douyin, Xiaohongshu, Bilibili, YouTube, etc.) videos or local video/audio files into subtitle text and generates AI summaries.

**Core Flow:**
- **Online video:** Provide a video link → Auto-download video or fetch native subtitles → Generate subtitles → AI summary
- **Local file:** Provide a local video/audio path → Extract audio (if needed) → Choose subtitle backend → Generate subtitles → AI summary

The default subtitle backend is local `faster-whisper`, with optional support for Volcengine VC through environment variables.
YouTube links first use `yt-dlp` to fetch manual or automatic subtitles directly, without TikHub, video download, or ASR by default.

[中文文档](./README.md)

## Update Notes

This version supports two subtitle backends:
- **`faster-whisper`**: the default local option
- **`volcengine`**: an optional cloud backend using Volcengine VC

That means:
- You do not need a Volcengine account by default
- `BYTEDANCE_VC_TOKEN` and `BYTEDANCE_VC_APPID` are only required when `ASR_BACKEND=volcengine`
- If you want local/private processing and no subtitle API fees, keep the default
- If you prefer the cloud backend, switch the environment variable

> Douyin, Xiaohongshu, and Bilibili still require TikHub for metadata and download URLs. YouTube subtitles are fetched directly with `yt-dlp`. The transcription backend itself is controlled by `ASR_BACKEND`.

## Demo

Give it a video link or a local file path, and it automatically outputs:

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
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Video download and YouTube subtitle tool (Bilibili / YouTube) |
| [TikHub](https://tikhub.io/) account | Fetch Douyin/Xiaohongshu/Bilibili metadata and download URLs |
| Python 3.9+ + [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Required when `ASR_BACKEND=faster-whisper` |
| [Volcengine](https://www.volcengine.com/) account | Required when `ASR_BACKEND=volcengine` |

## Quick Start

### 1. Choose a subtitle backend

Recommended default:

```bash
ASR_BACKEND=faster-whisper
```

Optional cloud backend:

```bash
ASR_BACKEND=volcengine
```

### 2. Install dependencies for the selected backend

**Option A: faster-whisper (default)**

```bash
python3 -m pip install -U faster-whisper
```

> The default path is CPU. The helper switches to GPU only when NVIDIA/CUDA is available. Apple Silicon still runs on CPU. See [docs/faster-whisper-setup.md](./docs/faster-whisper-setup.md) for GPU notes.

**Option B: Volcengine VC (optional)**

Follow [docs/bytedance-vc-setup.md](./docs/bytedance-vc-setup.md) to enable the service and get your `APPID` and `Token`.

### 2.5 Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows (using Chocolatey)
choco install ffmpeg
```

### 2.8 Install yt-dlp (Bilibili / YouTube)

```bash
# macOS
brew install yt-dlp

# Universal
python3 -m pip install -U yt-dlp
```

### 3. Copy the Skill to Claude Code

```bash
# Clone the repository
git clone https://github.com/imlewc/video-to-subtitle-summary.git

# Copy to Claude Code skills directory
cp -r video-to-subtitle-summary ~/.claude/skills/video-to-subtitle-summary
```

### 4. Configure Environment Variables

Configure TikHub credentials if you need Douyin, Xiaohongshu, or Bilibili. YouTube does not require TikHub. Then set the subtitle backend you want to use.

**Option 1: Using `.env` file (Recommended)**

```bash
cp .env.example ~/.claude/skills/video-to-subtitle-summary/.env
# Edit the .env file with your configuration
```

**Option 2: Add to shell config**

```bash
export ASR_BACKEND="faster-whisper"
export TIKHUB_TOKEN="your_tikhub_api_token"

export FW_MODEL_SIZE="small"
export FW_DEVICE="auto"
export FW_COMPUTE_TYPE=""

export BYTEDANCE_VC_TOKEN="your_bytedance_vc_token"
export BYTEDANCE_VC_APPID="your_bytedance_vc_appid"
```

Notes:
- `ASR_BACKEND`: optional, defaults to `faster-whisper`
- `TIKHUB_TOKEN`: required only for Douyin/Xiaohongshu/Bilibili; not required for YouTube
- `FW_MODEL_SIZE` / `FW_DEVICE` / `FW_COMPUTE_TYPE`: used only by `faster-whisper`
- `BYTEDANCE_VC_TOKEN` / `BYTEDANCE_VC_APPID`: used only by `volcengine`

## Usage

### Online Video

Simply send a video link in Claude Code (supports Douyin, Xiaohongshu, Bilibili, YouTube, etc.):

```
Please extract subtitles and summarize this video: https://v.douyin.com/xxxxxx/
```

```
Please summarize this Xiaohongshu video: https://www.xiaohongshu.com/explore/xxxxxx
```

```
Please summarize this Bilibili video: https://www.bilibili.com/video/BVxxxxxxxxxx/
```

```
Please summarize this YouTube video: https://www.youtube.com/watch?v=O87FdYIPeQk
```

Or use the skill command:

```
/video-to-subtitle-summary https://v.douyin.com/xxxxxx/
```

### Local File

Provide a local video or audio file path:

```
Please extract subtitles and summarize: /Users/me/Downloads/video.mp4
```

```
/video-to-subtitle-summary ~/Desktop/recording.mp3
```

> Local file mode skips the download step automatically. Audio files also skip audio extraction, so TikHub is not required.

### Direct YouTube Subtitle Fetch

YouTube links first run:

```bash
python3 ~/.claude/skills/video-to-subtitle-summary/scripts/download_youtube_subtitles.py \
  "https://www.youtube.com/watch?v=O87FdYIPeQk" \
  --output-dir /tmp/video_analysis/O87FdYIPeQk \
  --languages zh-Hans,zh-Hant,zh,en
```

This generates `/tmp/video_analysis/O87FdYIPeQk/subtitle.srt` and `/tmp/video_analysis/O87FdYIPeQk/text.txt`. If no subtitles are available, fall back to downloading audio and transcribing through `ASR_BACKEND`.

## Setup Guides

| Topic | Guide |
|------|------|
| TikHub API | [Setup Guide](./docs/tikhub-setup.md) |
| faster-whisper runtime | [Setup Guide](./docs/faster-whisper-setup.md) |
| Volcengine VC | [Setup Guide](./docs/bytedance-vc-setup.md) |

## Pricing

| Service | Cost |
|--------|------|
| TikHub API | 100 free requests/day, paid from $0.001/request |
| YouTube subtitle fetch | No API fee, uses local `yt-dlp` |
| faster-whisper | No API fee, uses local CPU/GPU resources |
| Volcengine VC | Subtitle API fees apply only when `ASR_BACKEND=volcengine` |
| Claude Code | Depends on your subscription plan |

> The default `faster-whisper` path does not incur Volcengine subtitle API fees.
> The first run downloads model files. Later runs reuse the local cache.

## Project Structure

```text
video-to-subtitle-summary/
├── README.md
├── README_en.md
├── LICENSE
├── SKILL.md
├── .env.example
├── scripts/
│   ├── download_youtube_subtitles.py
│   └── transcribe_faster_whisper.py
├── tests/
│   ├── test_download_youtube_subtitles.py
│   └── test_transcribe_faster_whisper.py
└── docs/
    ├── tikhub-setup.md
    ├── faster-whisper-setup.md
    └── bytedance-vc-setup.md
```

## License

[MIT](./LICENSE)
