"""Transparent-background GIF export.

This is the one piece not covered by `sticker-convert` (its own GIF output
flattens onto an opaque background) or by this repo's existing Go bot (whose
`FFToGif` doesn't reserve a transparency index either). GIF has no true alpha
channel, only a single binary transparent color in its palette, so
`alpha_threshold` below is a cutoff, not smooth blending.
"""

from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from .downloader import download_intermediate
from .utils import StickerExportError

_SOURCE_EXTS = {".png", ".apng", ".webp", ".gif", ".webm", ".mp4"}


def _sanitize_line_apng(path: Path) -> None:
    """Strip a stray tEXt chunk some older LINE APNGs carry right after acTL,
    which ffmpeg's apng demuxer fails to parse. Best-effort: leaves the file
    untouched if the expected chunk layout isn't found.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return
    if len(data) < 42 or data[37:41] != b"acTL":
        return
    text_start = None
    text_end = None
    for i in range(len(data) - 8):
        tag = data[i : i + 4]
        if tag == b"tEXt" and text_start is None:
            text_start = i - 4
        elif tag == b"IDAT" and text_start is not None:
            text_end = i - 4
            break
    if text_start is None or text_end is None:
        return
    path.write_bytes(data[:text_start] + data[text_end:])


def frames_to_transparent_gif(
    src: Path, dst: Path, fps: int = 30, alpha_threshold: int = 128
) -> None:
    """Convert an alpha-carrying image/video (APNG/animated WEBP/WEBM/PNG) to
    a GIF that keeps a real transparency index in its palette.
    """
    if src.suffix.lower() == ".apng":
        _sanitize_line_apng(src)

    filter_complex = (
        f"fps={fps},split[a][b];"
        "[a]palettegen=reserve_transparent=1:transparency_color=ffffff[p];"
        f"[b][p]paletteuse=alpha_threshold={alpha_threshold}"
    )
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(src),
        "-filter_complex",
        filter_complex,
        "-gifflags",
        "-offsetting",
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not dst.exists():
        raise StickerExportError(
            f"ffmpeg failed converting {src} to transparent GIF:\n{proc.stderr}"
        )


def export_pack_as_gif_zip(
    url: str, out_zip: Path, fps: int = 30, alpha_threshold: int = 128
) -> Path:
    """Download a LINE/Kakao pack and export the whole pack as a zip of
    per-sticker transparent-background GIFs.
    """
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="sticker-downloader-") as tmp:
        tmp_dir = Path(tmp)
        src_dir = tmp_dir / "src"
        gif_dir = tmp_dir / "gif"
        gif_dir.mkdir()

        src_files = download_intermediate(url, src_dir)
        source_files = [f for f in src_files if f.suffix.lower() in _SOURCE_EXTS]
        if not source_files:
            raise StickerExportError(f"No convertible sticker files found for {url}")

        gif_files = []
        errors: dict[str, str] = {}
        for src in source_files:
            dst = gif_dir / (src.stem + ".gif")
            try:
                frames_to_transparent_gif(
                    src, dst, fps=fps, alpha_threshold=alpha_threshold
                )
                gif_files.append(dst)
            except StickerExportError as exc:
                errors[src.name] = str(exc)

        if not gif_files:
            raise StickerExportError(
                f"All {len(source_files)} sticker(s) failed to convert to GIF:\n"
                + "\n".join(f"- {name}: {err}" for name, err in errors.items())
            )

        manifest = {
            "source_url": url,
            "sticker_count": len(gif_files),
            "failed": errors,
        }
        (gif_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for gif in gif_files:
                zf.write(gif, arcname=gif.name)
            zf.write(gif_dir / "manifest.json", arcname="manifest.json")

    return out_zip
