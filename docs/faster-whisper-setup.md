# faster-whisper 安装指南

本 skill 在 `ASR_BACKEND=faster-whisper` 时，使用 `faster-whisper` 作为本地语音识别后端，将音频转为字幕文本。

官方参考：
- [faster-whisper README](https://github.com/SYSTRAN/faster-whisper)
- [CTranslate2 Hardware Support](https://opennmt.net/CTranslate2/hardware_support.html)

## 步骤 1：确认后端选择

在 `.env` 或 shell 环境中设置：

```bash
ASR_BACKEND=faster-whisper
```

未配置时也会默认使用这个后端。

## 步骤 2：确认 Python 版本

`faster-whisper` 需要 Python 3.9+。

```bash
python3 --version
```

如果版本低于 3.9，请先升级 Python。

## 步骤 3：安装 faster-whisper

推荐使用安装 helper。它会先测速常见 PyPI 镜像，选择最快可用源，然后创建独立 venv 安装，避免污染系统 Python：

```bash
python3 ~/.codex/skills/video-to-subtitle-summary/scripts/install_faster_whisper.py
```

默认 venv 路径：

```text
~/.cache/video-to-subtitle-summary/faster-whisper-venv
```

如需指定 venv 路径：

```bash
python3 ~/.codex/skills/video-to-subtitle-summary/scripts/install_faster_whisper.py \
  --venv-dir /tmp/video_analysis/faster_whisper_venv
```

使用自定义 venv 时，在 `.env` 或 shell 环境中指定：

```bash
FW_PYTHON=/tmp/video_analysis/faster_whisper_venv/bin/python
```

这会同时安装 `ctranslate2` 等依赖。如果你明确要装进当前 Python 环境，也可以手动执行 `python3 -m pip install -U faster-whisper`。

## 步骤 4：按需安装 FFmpeg 和 yt-dlp

**FFmpeg（视频提音频需要）：**

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
choco install ffmpeg
```

**yt-dlp（B 站视频下载或 YouTube 字幕抓取需要）：**

```bash
# macOS
brew install yt-dlp

# 通用
python3 -m pip install -U yt-dlp
```

## 步骤 5：可选配置运行时参数

将以下变量写入 `.env` 或 shell 配置：

```bash
FW_MODEL_SIZE=small
FW_DEVICE=auto
FW_COMPUTE_TYPE=
```

说明：
- `FW_MODEL_SIZE`：默认 `small`
- `FW_DEVICE`：`auto`、`cpu`、`cuda`
- `FW_COMPUTE_TYPE`：留空时自动选择；例如 CPU 常见为 `int8`，CUDA 常见为 `float16`

## 步骤 6：验证安装

```bash
~/.cache/video-to-subtitle-summary/faster-whisper-venv/bin/python - <<'PY'
import ctranslate2
import faster_whisper

print("faster_whisper:", faster_whisper.__file__)
print("cuda_devices:", ctranslate2.get_cuda_device_count())
print("cpu_compute_types:", ctranslate2.get_supported_compute_types("cpu"))
PY
```

如果输出了模块路径和 `cuda_devices` 数值，说明安装成功。

## GPU 说明

### CPU 默认行为

- `FW_DEVICE=auto` 时，如果没有可用的 NVIDIA/CUDA 设备，会自动使用 `cpu`
- Apple Silicon（M1/M2/M3）即使有 Metal GPU，也会按 CPU 路径运行

### NVIDIA GPU

如果你在 Linux/Windows 服务器或工作站上使用 NVIDIA GPU：

1. 安装兼容版本的 NVIDIA 驱动
2. 按官方要求准备 CUDA 12 与 cuDNN 9 运行时
3. 保持 `FW_DEVICE=auto`，helper 会在检测到 CUDA 时自动切到 `device="cuda"`

> 如果 CUDA 运行时不完整，helper 会报错或回退到 CPU。优先确保 `ctranslate2.get_cuda_device_count()` 能返回正确的设备数量。

## 常见问题

**Q: `ModuleNotFoundError: No module named 'faster_whisper'`？**  
A: 执行 `python3 ~/.codex/skills/video-to-subtitle-summary/scripts/install_faster_whisper.py`。如果你用的是自定义 venv，运行转写时也要使用该 venv 的 Python。

**Q: Apple Silicon 为什么没有走 GPU？**  
A: 当前方案只把 NVIDIA/CUDA 视为可用 GPU 路径。Apple GPU 会回退到 CPU。

**Q: 首次运行很慢？**  
A: 首次会下载模型文件，后续会复用本地缓存。

**Q: 该选什么模型？**  
A: 默认 `small`，通常是速度和质量的平衡点。资源更紧张可降到 `base`，更看重准确率可升到 `medium` 或 `large-v3`。
