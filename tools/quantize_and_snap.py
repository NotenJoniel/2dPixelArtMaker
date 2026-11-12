#!/usr/bin/env python3
"""
quantize_and_snap.py — 外部参考画像や高解像度画像の等倍ドット縮小・クロマキー背景透過・指定パレット減色ツール

コード描画を主軸としつつ、外部画像やラフを取り込んで規格化する際の補助ツールです。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from pixel_canvas import Palette, parse_hex_color


def nearest_palette_color(rgb: tuple[int, int, int], palette_rgbs: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    r, g, b = rgb
    best = palette_rgbs[0]
    best_dist = float("inf")
    for pr, pg, pb in palette_rgbs:
        # 人間の視覚感度に近い重み付きRGB距離
        dr, dg, db = r - pr, g - pg, b - pb
        dist = 2 * dr * dr + 4 * dg * dg + 3 * db * db
        if dist < best_dist:
            best_dist = dist
            best = (pr, pg, pb)
    return best


def process_image(
    src_path: Path,
    out_path: Path,
    *,
    target_size: tuple[int, int] | None = None,
    chroma_hex: str | None = "#FF00FF",
    chroma_tolerance: int = 24,
    alpha_threshold: int = 128,
    palette_path: Path | None = None,
) -> Path:
    img = Image.open(src_path).convert("RGBA")

    if target_size is not None and img.size != target_size:
        img = img.resize(target_size, resample=Image.Resampling.NEAREST)

    chroma_rgb = parse_hex_color(chroma_hex)[:3] if chroma_hex else None
    palette_rgbs: list[tuple[int, int, int]] | None = None
    if palette_path is not None:
        pal = Palette.from_file(palette_path)
        palette_rgbs = sorted(pal.allowed_rgb_set())
        if not palette_rgbs:
            raise ValueError(f"Palette {palette_path} contains no opaque colors.")

    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < alpha_threshold:
                px[x, y] = (0, 0, 0, 0)
                continue
            if chroma_rgb is not None:
                if (
                    abs(r - chroma_rgb[0]) <= chroma_tolerance
                    and abs(g - chroma_rgb[1]) <= chroma_tolerance
                    and abs(b - chroma_rgb[2]) <= chroma_tolerance
                ):
                    px[x, y] = (0, 0, 0, 0)
                    continue
            if palette_rgbs is not None:
                nr, ng, nb = nearest_palette_color((r, g, b), palette_rgbs)
                px[x, y] = (nr, ng, nb, 255)
            else:
                px[x, y] = (r, g, b, 255)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Snap image to 1x pixel size, clean binary alpha, and quantize to palette.")
    parser.add_argument("input", type=Path, help="Input image path")
    parser.add_argument("--out", type=Path, required=True, help="Output 1x PNG path")
    parser.add_argument("--width", type=int, help="Target 1x width in pixels")
    parser.add_argument("--height", type=int, help="Target 1x height in pixels")
    parser.add_argument("--chroma", type=str, default="#FF00FF", help="Chroma key hex to make transparent ('' to disable)")
    parser.add_argument("--tolerance", type=int, default=24, help="Chroma key RGB tolerance (default: 24)")
    parser.add_argument("--alpha-threshold", type=int, default=128, help="Binary alpha threshold 1..255 (default: 128)")
    parser.add_argument("--palette", type=Path, help="Optional .json or .hex palette file to quantize colors")
    args = parser.parse_args()

    target_sz = (args.width, args.height) if (args.width and args.height) else None
    chroma = args.chroma if args.chroma.strip() else None

    out = process_image(
        args.input,
        args.out,
        target_size=target_sz,
        chroma_hex=chroma,
        chroma_tolerance=args.tolerance,
        alpha_threshold=args.alpha_threshold,
        palette_path=args.palette,
    )
    print(f"[OK] Processed 1x pixel asset: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
