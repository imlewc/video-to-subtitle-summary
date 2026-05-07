#!/usr/bin/env python3
"""Transcribe audio with faster-whisper and emit SRT/text outputs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


CPU_COMPUTE_TYPE_ORDER = (
    "int8",
    "int8_float32",
    "int16",
    "float32",
)
CUDA_COMPUTE_TYPE_ORDER = (
    "float16",
    "int8_float16",
    "int8",
    "int8_float32",
    "bfloat16",
    "float32",
)


@dataclass(frozen=True)
class RuntimeConfig:
    model_size: str
    device: str
    compute_type: str


@dataclass(frozen=True)
class OutputPaths:
    srt_path: Path
    text_path: Path


def env_or_default(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    cleaned = value.strip()
    return cleaned if cleaned else default


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run faster-whisper transcription and write subtitle files.",
    )
    parser.add_argument("audio_path", help="Path to the input audio file.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where subtitle.srt and text.txt are written.",
    )
    parser.add_argument(
        "--model-size",
        default=env_or_default("FW_MODEL_SIZE", "small"),
        help="faster-whisper model size. Defaults to FW_MODEL_SIZE or 'small'.",
    )
    parser.add_argument(
        "--device",
        default=env_or_default("FW_DEVICE", "auto"),
        choices=("auto", "cpu", "cuda"),
        help="Execution device. Defaults to FW_DEVICE or auto-detect.",
    )
    parser.add_argument(
        "--compute-type",
        default=env_or_default("FW_COMPUTE_TYPE"),
        help="Optional compute type override. Defaults to runtime-based selection.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language hint. Defaults to automatic language detection.",
    )
    return parser.parse_args(argv)


def load_ctranslate2():
    try:
        import ctranslate2  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'ctranslate2'. Install 'faster-whisper' first, "
            "for example: pip install faster-whisper"
        ) from exc
    return ctranslate2


def load_whisper_model():
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'faster-whisper'. Install it with "
            "'pip install faster-whisper'."
        ) from exc
    return WhisperModel


def resolve_runtime_config(
    model_size: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
    ctranslate2_module=None,
) -> RuntimeConfig:
    ct2 = ctranslate2_module or load_ctranslate2()
    requested_device = device or env_or_default("FW_DEVICE", "auto")
    resolved_device = resolve_device(requested_device, ct2)
    supported_compute_types = set(ct2.get_supported_compute_types(resolved_device))
    requested_compute_type = compute_type or env_or_default("FW_COMPUTE_TYPE")
    resolved_compute_type = resolve_compute_type(
        resolved_device,
        supported_compute_types,
        requested_compute_type,
    )
    return RuntimeConfig(
        model_size=model_size or env_or_default("FW_MODEL_SIZE", "small") or "small",
        device=resolved_device,
        compute_type=resolved_compute_type,
    )


def resolve_device(requested_device: str, ctranslate2_module) -> str:
    if requested_device in {"cpu", "cuda"}:
        return requested_device

    if requested_device != "auto":
        raise ValueError(f"Unsupported device: {requested_device}")

    return "cuda" if ctranslate2_module.get_cuda_device_count() > 0 else "cpu"


def resolve_compute_type(
    device: str,
    supported_compute_types: set[str],
    requested_compute_type: str | None,
) -> str:
    if not supported_compute_types:
        raise RuntimeError(f"No compute types reported for device '{device}'.")

    if requested_compute_type and requested_compute_type in supported_compute_types:
        return requested_compute_type

    order = CUDA_COMPUTE_TYPE_ORDER if device == "cuda" else CPU_COMPUTE_TYPE_ORDER
    if requested_compute_type:
        ordered_candidates = (requested_compute_type, *order)
    else:
        ordered_candidates = order

    for candidate in ordered_candidates:
        if candidate in supported_compute_types:
            return candidate

    return sorted(supported_compute_types)[0]


def ms_to_srt_timestamp(milliseconds: int) -> str:
    total_ms = max(0, int(milliseconds))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def seconds_to_srt_timestamp(seconds: float) -> str:
    return ms_to_srt_timestamp(round(seconds * 1000))


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def write_outputs(segments: Iterable[object], output_dir: Path) -> OutputPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    srt_path = output_dir / "subtitle.srt"
    text_path = output_dir / "text.txt"

    normalized_segments = []
    for segment in segments:
        text = normalize_text(getattr(segment, "text", ""))
        if not text:
            continue
        normalized_segments.append(
            (
                len(normalized_segments) + 1,
                seconds_to_srt_timestamp(float(getattr(segment, "start"))),
                seconds_to_srt_timestamp(float(getattr(segment, "end"))),
                text,
            )
        )

    srt_content = "".join(
        f"{index}\n{start} --> {end}\n{text}\n\n"
        for index, start, end, text in normalized_segments
    )
    text_content = " ".join(text for _, _, _, text in normalized_segments)
    if text_content:
        text_content = f"{text_content}\n"

    srt_path.write_text(srt_content, encoding="utf-8")
    text_path.write_text(text_content, encoding="utf-8")

    return OutputPaths(srt_path=srt_path, text_path=text_path)


def transcribe_audio(
    audio_path: Path,
    output_dir: Path,
    runtime_config: RuntimeConfig,
    language: str | None = None,
) -> dict[str, object]:
    WhisperModel = load_whisper_model()
    model = WhisperModel(
        runtime_config.model_size,
        device=runtime_config.device,
        compute_type=runtime_config.compute_type,
    )
    segments_iter, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,
        language=language,
    )
    segments = list(segments_iter)
    output_paths = write_outputs(segments, output_dir)

    return {
        "model_size": runtime_config.model_size,
        "device": runtime_config.device,
        "compute_type": runtime_config.compute_type,
        "language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "segment_count": len(segments),
        "audio_path": str(audio_path),
        "output_dir": str(output_dir),
        "srt_path": str(output_paths.srt_path),
        "text_path": str(output_paths.text_path),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    audio_path = Path(args.audio_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not audio_path.exists():
        print(
            f"ERROR: Audio file not found: {audio_path}",
            file=sys.stderr,
        )
        return 1

    try:
        runtime_config = resolve_runtime_config(
            model_size=args.model_size,
            device=args.device,
            compute_type=args.compute_type,
        )
        result = transcribe_audio(
            audio_path=audio_path,
            output_dir=output_dir,
            runtime_config=runtime_config,
            language=args.language,
        )
    except Exception as exc:  # pragma: no cover - CLI error handling
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = {
        "runtime": asdict(runtime_config),
        "result": result,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
