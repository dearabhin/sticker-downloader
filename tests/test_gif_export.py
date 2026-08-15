from __future__ import annotations

import shutil
import zipfile

import pytest

from sticker_downloader import gif_export

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg not available"
)


def _make_alpha_png(path):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((16, 16, 48, 48), fill=(255, 0, 0, 255))
    img.save(path)


def test_frames_to_transparent_gif_preserves_transparency(tmp_path):
    from PIL import Image

    src = tmp_path / "src.png"
    dst = tmp_path / "out.gif"
    _make_alpha_png(src)

    gif_export.frames_to_transparent_gif(src, dst)

    assert dst.exists()
    with Image.open(dst) as gif:
        assert gif.info.get("transparency") is not None
        rgba = gif.convert("RGBA")
        corner = rgba.getpixel((0, 0))
        center = rgba.getpixel((32, 32))
    assert corner[3] == 0  # outside the drawn square: was fully transparent
    assert center[3] > 0  # inside the drawn square: was opaque


def test_export_pack_as_gif_zip(tmp_path, monkeypatch):
    from PIL import Image

    src_dir = tmp_path / "srcs"
    src_dir.mkdir()
    src_files = []
    for i in range(2):
        p = src_dir / f"{i}.png"
        Image.new("RGBA", (32, 32), (0, 0, 0, 0)).save(p)
        src_files.append(p)

    def fake_download_intermediate(url, out_dir):
        return src_files

    monkeypatch.setattr(gif_export, "download_intermediate", fake_download_intermediate)

    out_zip = tmp_path / "pack.zip"
    gif_export.export_pack_as_gif_zip(
        "https://store.line.me/stickershop/product/1/en", out_zip
    )

    assert out_zip.exists()
    with zipfile.ZipFile(out_zip) as zf:
        names = zf.namelist()
    assert "manifest.json" in names
    assert sum(1 for n in names if n.endswith(".gif")) == 2
