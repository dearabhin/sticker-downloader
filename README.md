# sticker-downloader

A small Python CLI for two specific jobs:

1. Convert a LINE or KakaoTalk sticker pack link into local, Telegram-ready
   animated sticker files (`.webm` or `.tgs`), so you can `/addstickers` them
   yourself.
2. Download a whole LINE/Kakao sticker pack as a zip of animated GIFs with a
   real transparent background.

This is a thin wrapper around [`sticker-convert`](https://github.com/laggykiller/sticker-convert),
which already handles the hard, fragile parts (LINE store scraping, Kakao's
API/decryption, Telegram size/duration compression). This tool adds the one
thing that isn't covered upstream: **GIF export that keeps real
transparency** (`sticker-convert`'s own GIF output flattens onto an opaque
background instead).

This tool never uploads anything to Telegram/Signal/etc. — it only produces
local files.

## Install

```bash
pip install -e .
```

Requires `ffmpeg` on `PATH` (used for the GIF export step).

## Usage

```bash
# LINE or Kakao pack -> local Telegram-ready sticker files
sticker-downloader telegram "https://store.line.me/stickershop/product/1234/en" --out ./out

# LINE or Kakao pack -> a zip of transparent-background GIFs
sticker-downloader gif "https://store.line.me/stickershop/product/1234/en" --out ./pack.gif.zip
```

`sticker-downloader telegram` accepts `--format .webm` (default) or `--format .tgs`.

`sticker-downloader gif` accepts `--fps` (default 30) and `--alpha-threshold`
(0-255, default 128) — the alpha cutoff above which a pixel is kept fully
opaque and below which it becomes the GIF's single transparent color.

### A note on GIF transparency

GIF has no true alpha channel — only one "this color is transparent" entry
in its palette. That means edges will not anti-alias smoothly against an
arbitrary background the way a WEBM or APNG would; pixels are either fully
opaque or fully transparent, split at `--alpha-threshold`. If you need
smooth alpha blending, use the `telegram` subcommand's `.webm` output (or
`sticker-convert` directly with `--img-format .apng`) instead.

### Kakao animated packs

Kakao has changed its platform/APIs over time in ways that have broken
animated-sticker downloading for tools like this one (other LINE/Kakao
import tools, e.g. [moe-sticker-bot](https://github.com/star-39/moe-sticker-bot),
have hit the same issue and disabled animated Kakao import). If a Kakao pack
fails to download, check
[`sticker-convert`'s current status](https://github.com/laggykiller/sticker-convert)
for that platform.

## Tests

```bash
pip install -e ".[test]"
pytest tests
```

## License

GPL-3.0-or-later, matching the rest of this repository. `sticker-convert`
itself is GPL-2.0.
