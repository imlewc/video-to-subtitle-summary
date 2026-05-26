#!/usr/bin/env python3
"""Install faster-whisper into a venv after probing PyPI mirror latency."""

from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import venv
from pathlib import Path
from typing import Callable, Iterable


@dataclasses.dataclass(frozen=True)
class PyPIMirror:
    name: str
    index_url: str
    trusted_host: str | None


DEFAULT_MIRRORS = (
    PyPIMirror("清华", "https://pypi.tuna.tsinghua.edu.cn/simple", "pypi.tuna.tsinghua.edu.cn"),
    PyPIMirror("阿里", "https://mirrors.aliyun.com/pypi/simple", "mirrors.aliyun.com"),
    PyPIMirror("腾讯", "https://mirrors.cloud.tencent.com/pypi/simple", "mirrors.cloud.tencent.com"),
    PyPIMirror("中科大", "https://pypi.mirrors.ustc.edu.cn/simple", "pypi.mirrors.ustc.edu.cn"),
    PyPIMirror("官方", "https://pypi.org/simple", None),
)


def default_venv_dir() -> Path:
    return Path.home() / ".cache" / "video-to-subtitle-summary" / "faster-whisper-venv"


def python_in_venv(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def probe_mirror(mirror: PyPIMirror, timeout: float) -> float | None:
    target = mirror.index_url.rstrip("/") + "/faster-whisper/"
    request = urllib.request.Request(target, headers={"User-Agent": "video-to-subtitle-summary/installer"})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(1024)
            status = getattr(response, "status", 200)
            if status >= 400:
                return None
    except (OSError, urllib.error.URLError):
        return None
    return time.monotonic() - started


def select_fastest_mirror(
    mirrors: Iterable[PyPIMirror],
    *,
    probe: Callable[[PyPIMirror, float], float | None] = probe_mirror,
    timeout: float = 5.0,
) -> PyPIMirror:
    results: list[tuple[float, PyPIMirror]] = []
    for mirror in mirrors:
        elapsed = probe(mirror, timeout)
        if elapsed is not None:
            results.append((elapsed, mirror))
            print(f"{mirror.name}: {elapsed:.3f}s", file=sys.stderr)
        else:
            print(f"{mirror.name}: unavailable", file=sys.stderr)

    if not results:
        raise RuntimeError("no PyPI mirror is reachable")

    results.sort(key=lambda item: item[0])
    return results[0][1]


def ensure_venv(venv_dir: Path) -> Path:
    python_path = python_in_venv(venv_dir)
    if not python_path.exists():
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True).create(venv_dir)
    return python_path


def build_install_command(python_path: Path, mirror: PyPIMirror) -> list[str]:
    command = [
        str(python_path),
        "-m",
        "pip",
        "install",
        "-U",
        "-i",
        mirror.index_url,
    ]
    if mirror.trusted_host:
        command.extend(["--trusted-host", mirror.trusted_host])
    command.extend(["pip", "faster-whisper"])
    return command


def verify_install(python_path: Path) -> dict[str, str]:
    script = """
import ctranslate2
import faster_whisper
print(getattr(faster_whisper, '__version__', 'unknown'))
print(getattr(ctranslate2, '__version__', 'unknown'))
"""
    result = subprocess.run(
        [str(python_path), "-c", script],
        check=True,
        text=True,
        capture_output=True,
    )
    lines = result.stdout.strip().splitlines()
    return {
        "faster_whisper": lines[0] if lines else "unknown",
        "ctranslate2": lines[1] if len(lines) > 1 else "unknown",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv-dir", type=Path, default=default_venv_dir())
    parser.add_argument("--probe-timeout", type=float, default=5.0)
    parser.add_argument("--no-probe", action="store_true", help="Use the first mirror without probing.")
    args = parser.parse_args()

    mirror = DEFAULT_MIRRORS[0] if args.no_probe else select_fastest_mirror(DEFAULT_MIRRORS, timeout=args.probe_timeout)
    print(f"Selected mirror: {mirror.name} ({mirror.index_url})", file=sys.stderr)

    python_path = ensure_venv(args.venv_dir)
    subprocess.run(build_install_command(python_path, mirror), check=True)
    versions = verify_install(python_path)

    print(
        json.dumps(
            {
                "venv_python": str(python_path),
                "mirror": mirror.name,
                "index_url": mirror.index_url,
                "versions": versions,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
