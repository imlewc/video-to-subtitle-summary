#!/usr/bin/env python3
"""Download a video by trying AI Douyin/TikHub candidate URLs in order."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


def extract_candidates(response: dict[str, Any]) -> list[str]:
    raw_candidates: list[str] = []

    download_urls = response.get("download_urls")
    if isinstance(download_urls, list):
        raw_candidates.extend(str(url) for url in download_urls if url)

    download_url = response.get("download_url")
    if download_url:
        raw_candidates.append(str(download_url))

    candidates: list[str] = []
    seen: set[str] = set()
    for candidate in raw_candidates:
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        candidates.append(candidate)

    return candidates


def describe_candidate(candidate: str) -> str:
    parsed = urllib.parse.urlparse(candidate)
    domain = parsed.netloc or "unknown-host"
    suffix = Path(parsed.path).suffix or ".mp4"
    return f"{domain}{suffix}"


def download_first_working_candidate(
    candidates: Iterable[str],
    output_path: Path,
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: int = 30,
) -> str:
    errors: list[str] = []
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for index, candidate in enumerate(candidates, 1):
        partial_path = output_path.with_suffix(output_path.suffix + ".part")
        if partial_path.exists():
            partial_path.unlink()

        request = urllib.request.Request(candidate, headers={"User-Agent": USER_AGENT})
        try:
            print(f"Trying candidate {index}: {describe_candidate(candidate)}", file=sys.stderr)
            with opener(request, timeout=timeout) as response:
                with partial_path.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
            partial_path.replace(output_path)
            return candidate
        except Exception as exc:  # noqa: BLE001 - show all failed candidates to the user
            errors.append(f"{index}: {exc}")
            if partial_path.exists():
                partial_path.unlink()

    raise RuntimeError("all download URL candidates failed: " + "; ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--response-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    response = json.loads(args.response_json.read_text(encoding="utf-8"))
    candidates = extract_candidates(response)
    if not candidates:
        print("ERROR: no download_url or download_urls found", file=sys.stderr)
        return 1

    selected = download_first_working_candidate(
        candidates,
        args.output,
        timeout=args.timeout,
    )
    print(
        json.dumps(
            {
                "video_path": str(args.output),
                "selected_url_index": candidates.index(selected) + 1,
                "selected_domain": urllib.parse.urlparse(selected).netloc,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
