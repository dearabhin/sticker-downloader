from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sticker_downloader import downloader
from sticker_downloader.utils import StickerExportError


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://store.line.me/stickershop/product/1234/en", "line"),
        ("https://line.me/S/sticker/1234/?lang=en", "line"),
        ("https://e.kakao.com/t/abcdef", "kakao"),
        ("https://emoticon.kakao.com/items/abcdef", "kakao"),
    ],
)
def test_detect_platform(url, expected):
    assert downloader.detect_platform(url) == expected


def test_detect_platform_rejects_unknown_host():
    with pytest.raises(StickerExportError):
        downloader.detect_platform("https://example.com/stickers/1")


@patch("sticker_downloader.downloader.subprocess.run")
def test_download_telegram_builds_expected_args(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    (tmp_path / "0.webm").write_bytes(b"fake")

    downloader.download_telegram(
        "https://store.line.me/stickershop/product/1234/en", tmp_path
    )

    cmd = mock_run.call_args[0][0]
    assert "--download-line" in cmd
    assert "https://store.line.me/stickershop/product/1234/en" in cmd
    assert "--preset" in cmd and "telegram" in cmd
    assert "--export-telegram" not in cmd  # this tool must never try to upload
    assert str(tmp_path) in cmd


@patch("sticker_downloader.downloader.subprocess.run")
def test_download_kakao_uses_kakao_flag(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    (tmp_path / "0.webp").write_bytes(b"fake")

    downloader.download_telegram("https://e.kakao.com/t/abcdef", tmp_path)

    cmd = mock_run.call_args[0][0]
    assert "--download-kakao" in cmd
    assert "--download-line" not in cmd


@patch("sticker_downloader.downloader.subprocess.run")
def test_download_telegram_raises_on_failure(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")
    with pytest.raises(StickerExportError):
        downloader.download_telegram(
            "https://store.line.me/stickershop/product/1234/en", tmp_path
        )


@patch("sticker_downloader.downloader.subprocess.run")
def test_download_telegram_raises_if_no_files_produced(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    with pytest.raises(StickerExportError):
        downloader.download_telegram(
            "https://store.line.me/stickershop/product/1234/en", tmp_path
        )


@patch("sticker_downloader.downloader.subprocess.run")
def test_download_intermediate_uses_no_compress(mock_run, tmp_path):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    (tmp_path / "0.apng").write_bytes(b"fake")

    downloader.download_intermediate("https://e.kakao.com/t/abcdef", tmp_path)

    cmd = mock_run.call_args[0][0]
    assert "--download-kakao" in cmd
    assert "--no-compress" in cmd
    assert "--preset" not in cmd
