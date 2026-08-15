"""Thin subprocess wrapper around the `sticker-convert` package for
downloading and converting LINE/KakaoTalk sticker packs.

We deliberately never pass `--export-telegram` (or any other `--export-*`
flag): those flags *upload* to a live account and require credentials (a
Telegram bot token + a real account's user id). This tool only ever produces
local files.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from .utils import StickerExportError

_LINE_HOSTS = {"store.line.me", "line.me"}
_KAKAO_HOSTS = {"e.kakao.com", "emoticon.kakao.com"}


def detect_platform(url: str) -> str:
    """Return "line" or "kakao" for a supported sticker pack URL."""
    host = urlparse(url).netloc.lower()
    if host in _LINE_HOSTS:
        return "line"
    if host in _KAKAO_HOSTS:
        return "kakao"
    raise StickerExportError(
        f"Unrecognized sticker pack URL: {url!r}. Expected a "
        "store.line.me/... , line.me/... , e.kakao.com/t/... or "
        "emoticon.kakao.com/items/... link."
    )


def _run_sticker_convert(args: list[str]) -> None:
    cmd = [sys.executable, "-m", "sticker_convert", "--no-confirm", "--no-progress", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise StickerExportError(
            "sticker-convert failed (exit code "
            f"{proc.returncode}):\n{proc.stdout}\n{proc.stderr}\n\n"
            "If this is an animated Kakao pack, note that Kakao has changed "
            "its platform in ways that can break animated downloads - see "
            "https://github.com/laggykiller/sticker-convert for current status."
        )


def _list_output_files(out_dir: Path) -> list[Path]:
    files = sorted(p for p in out_dir.rglob("*") if p.is_file())
    if not files:
        raise StickerExportError(f"sticker-convert produced no files in {out_dir}")
    return files


def download_telegram(url: str, out_dir: Path, vid_format: str = ".webm") -> list[Path]:
    """Download a LINE/Kakao pack and convert it to local Telegram-ready
    sticker files (static image, animated .webm or .tgs), sized and timed to
    fit Telegram's own limits via sticker-convert's "telegram" compression
    preset.
    """
    platform = detect_platform(url)
    out_dir.mkdir(parents=True, exist_ok=True)
    flag = "--download-line" if platform == "line" else "--download-kakao"
    _run_sticker_convert(
        [
            flag,
            url,
            "--output-dir",
            str(out_dir),
            "--preset",
            "telegram",
            "--vid-format",
            vid_format,
        ]
    )
    return _list_output_files(out_dir)


def download_intermediate(url: str, out_dir: Path) -> list[Path]:
    """Download a LINE/Kakao pack with sticker-convert's compression stage
    skipped (`--no-compress`), keeping each sticker in its original decoded
    format/quality. This is the input to our own transparent-GIF pipeline,
    since sticker-convert's own GIF output does not keep an alpha channel.
    """
    platform = detect_platform(url)
    out_dir.mkdir(parents=True, exist_ok=True)
    flag = "--download-line" if platform == "line" else "--download-kakao"
    _run_sticker_convert(
        [
            flag,
            url,
            "--output-dir",
            str(out_dir),
            "--no-compress",
        ]
    )
    return _list_output_files(out_dir)
