#!/usr/bin/env python3
"""Download YouTube subtitles with yt-dlp and emit SRT/text outputs."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


DEFAULT_LANGUAGES = ("zh-Hans", "zh-Hant", "zh", "en")
TIMING_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3})(?:\s+.*)?"
)
TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class OutputPaths:
    srt_path: Path
    text_path: Path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download YouTube subtitles via yt-dlp and write subtitle files.",
    )
    parser.add_argument("url", help="YouTube video URL.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where subtitle.srt and text.txt are written.",
    )
    parser.add_argument(
        "--languages",
        default=",".join(DEFAULT_LANGUAGES),
        help="Comma-separated subtitle language preference list.",
    )
    return parser.parse_args(argv)


def build_ytdlp_command(
    url: str,
    output_stem: Path,
    languages: Sequence[str],
) -> list[str]:
    return [
        "yt-dlp",
        "--ignore-config",
        "--ignore-no-formats-error",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-format",
        "vtt",
        "--sub-langs",
        ",".join(languages),
        "-o",
        str(output_stem),
        url,
    ]


def clean_caption_text(text: str) -> str:
    cleaned = TAG_RE.sub("", text)
    cleaned = html.unescape(cleaned)
    return " ".join(cleaned.split())


def vtt_timestamp_to_srt(timestamp: str) -> str:
    return timestamp.replace(".", ",")


def parse_vtt_cues(vtt_content: str) -> list[tuple[str, str, str]]:
    cues: list[tuple[str, str, str]] = []
    lines = vtt_content.splitlines()
    index = 0

    while index < len(lines):
        match = TIMING_RE.match(lines[index].strip())
        if not match:
            index += 1
            continue

        start = vtt_timestamp_to_srt(match.group("start"))
        end = vtt_timestamp_to_srt(match.group("end"))
        index += 1
        text_lines = []
        while index < len(lines) and lines[index].strip():
            line = lines[index].strip()
            if not line.startswith(("NOTE", "STYLE", "REGION")):
                text_lines.append(line)
            index += 1

        text = clean_caption_text(" ".join(text_lines))
        if text:
            cues.append((start, end, text))

    return cues


def convert_vtt_to_outputs(vtt_content: str, output_dir: Path) -> OutputPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    srt_path = output_dir / "subtitle.srt"
    text_path = output_dir / "text.txt"
    cues = parse_vtt_cues(vtt_content)

    srt_content = "".join(
        f"{index}\n{start} --> {end}\n{text}\n\n"
        for index, (start, end, text) in enumerate(cues, start=1)
    )
    text_content = " ".join(text for _, _, text in cues)
    if text_content:
        text_content = f"{text_content}\n"

    srt_path.write_text(srt_content, encoding="utf-8")
    text_path.write_text(text_content, encoding="utf-8")
    return OutputPaths(srt_path=srt_path, text_path=text_path)


def find_downloaded_vtt(output_dir: Path) -> Path:
    candidates = sorted(output_dir.glob("subtitle*.vtt"))
    if not candidates:
        raise RuntimeError("No YouTube subtitle file was downloaded.")
    return candidates[0]


def download_youtube_subtitles(
    url: str,
    output_dir: Path,
    languages: Sequence[str],
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_stem = output_dir / "subtitle"
    command = build_ytdlp_command(url, output_stem, languages)
    subprocess.run(command, check=True)

    vtt_path = find_downloaded_vtt(output_dir)
    output_paths = convert_vtt_to_outputs(
        vtt_path.read_text(encoding="utf-8"),
        output_dir,
    )
    return {
        "url": url,
        "languages": list(languages),
        "vtt_path": str(vtt_path),
        "srt_path": str(output_paths.srt_path),
        "text_path": str(output_paths.text_path),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir).expanduser().resolve()
    languages = [item.strip() for item in args.languages.split(",") if item.strip()]

    try:
        result = download_youtube_subtitles(args.url, output_dir, languages)
    except Exception as exc:  # pragma: no cover - CLI error handling
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
