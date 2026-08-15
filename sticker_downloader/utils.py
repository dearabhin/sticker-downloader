"""Shared helpers: the package's exception type and a startup dependency check."""

from __future__ import annotations

import importlib.util
import shutil


class StickerExportError(RuntimeError):
    """Raised for any expected failure in the sticker-downloader pipeline."""


def check_deps() -> None:
    """Raise StickerExportError naming any missing required dependency."""
    missing = []
    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg (install via your system package manager)")
    if importlib.util.find_spec("sticker_convert") is None:
        missing.append("sticker-convert (install via `pip install sticker-convert`)")
    if missing:
        raise StickerExportError(
            "Missing required dependencies:\n  - " + "\n  - ".join(missing)
        )
