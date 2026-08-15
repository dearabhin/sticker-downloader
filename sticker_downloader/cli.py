"""Command-line entry point for sticker-downloader."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import downloader, gif_export
from .utils import StickerExportError, check_deps


def _cmd_telegram(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    files = downloader.download_telegram(args.url, out_dir, vid_format=args.format)
    total_size = sum(f.stat().st_size for f in files)
    print(f"Wrote {len(files)} Telegram-ready sticker file(s) to {out_dir}")
    print(f"Total size: {total_size / 1024:.1f} KiB")
    return 0


def _cmd_gif(args: argparse.Namespace) -> int:
    out_zip = Path(args.out)
    gif_export.export_pack_as_gif_zip(
        args.url, out_zip, fps=args.fps, alpha_threshold=args.alpha_threshold
    )
    print(f"Wrote transparent-background GIF pack to {out_zip}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sticker-downloader",
        description=(
            "Convert LINE/KakaoTalk sticker packs to Telegram-ready animated "
            "stickers, or download a whole pack as transparent-background "
            "GIFs. Wraps the sticker-convert package for download/decode "
            "(pip install sticker-convert if it's missing)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_tg = sub.add_parser(
        "telegram", help="Convert a LINE/Kakao pack to local Telegram sticker files."
    )
    p_tg.add_argument("url", help="LINE or Kakao sticker pack URL.")
    p_tg.add_argument("--out", default="./telegram_stickers", help="Output directory.")
    p_tg.add_argument(
        "--format",
        default=".webm",
        choices=[".webm", ".tgs"],
        help="Animated sticker format (default: .webm).",
    )
    p_tg.set_defaults(func=_cmd_telegram)

    p_gif = sub.add_parser(
        "gif", help="Download a whole pack as transparent-background GIFs (zip)."
    )
    p_gif.add_argument("url", help="LINE or Kakao sticker pack URL.")
    p_gif.add_argument("--out", default="./stickers_gif.zip", help="Output zip path.")
    p_gif.add_argument("--fps", type=int, default=30, help="Output GIF frame rate.")
    p_gif.add_argument(
        "--alpha-threshold",
        type=int,
        default=128,
        help="Alpha cutoff (0-255) for the GIF's binary transparency (default: 128).",
    )
    p_gif.set_defaults(func=_cmd_gif)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        check_deps()
        return args.func(args)
    except StickerExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
