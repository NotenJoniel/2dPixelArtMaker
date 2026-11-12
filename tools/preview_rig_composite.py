#!/usr/bin/env python3
"""
preview_rig_composite.py — 分割パーツ群 + <asset_id>_meta.json の合成プレビュー生成ツール

機能:
1. meta.json の z_index 昇順で全パーツ（または指定 preset の差分パーツ）を合成
2. 左側に「通常拡大プレビュー」、右側に「ピボット十字＆接地基準線(origin)＆1pxグリッド付きプレビュー」、
   下段に「個別パーツ一覧シート」を並べた確認用画像を workspace/03_preview/ 等に出力
3. --save-base 指定時は等倍(1x)の結合立ち絵 <asset_id>_base.png も保存
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from pixel_canvas import PixelCanvas


def composite_character(meta_path: Path, preset: str = "default") -> tuple[PixelCanvas, list[tuple[str, Image.Image, tuple[int, int]]]]:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    base_dir = meta_path.parent
    cw, ch = meta["canvas_size"]
    part_mode = meta.get("part_mode", "canvas_aligned")
    presets = meta.get("presets", {})
    variant_overrides: dict[str, str] = presets.get(preset, {}) if preset != "default" else presets.get("default", {})

    parts_sorted = sorted(meta.get("parts", []), key=lambda p: p.get("z_index", 0))
    canvas = PixelCanvas(cw, ch)
    loaded_parts: list[tuple[str, Image.Image, tuple[int, int]]] = []

    for part in parts_sorted:
        part_id = part["id"]
        rel_file = part["file"]
        if part_id in variant_overrides:
            v_key = variant_overrides[part_id]
            rel_file = part.get("variants", {}).get(v_key, rel_file)

        part_img_path = base_dir / rel_file
        if not part_img_path.exists():
            raise FileNotFoundError(f"Part file missing for '{part_id}': {part_img_path}")

        part_img = Image.open(part_img_path).convert("RGBA")
        ox, oy = part.get("offset", [0, 0])
        px, py = part.get("pivot", [cw // 2, ch // 2])

        if part_mode == "trimmed":
            world_pivot = (ox + px, oy + py)
        else:
            world_pivot = (px, py)

        canvas.image.alpha_composite(part_img, dest=(int(ox), int(oy)))
        loaded_parts.append((part_id, part_img, world_pivot))

    canvas._px = canvas.image.load()
    return canvas, loaded_parts


def build_inspection_sheet(
    meta: dict,
    composite_canvas: PixelCanvas,
    loaded_parts: list[tuple[str, Image.Image, tuple[int, int]]],
    scale: int,
) -> Image.Image:
    cw, ch = meta["canvas_size"]
    origin = tuple(meta["origin"]) if "origin" in meta else None
    pivots = [p[2] for p in loaded_parts]

    clean_view = composite_canvas.render_preview_image(scale=scale, checker=True, grid=False)
    debug_view = composite_canvas.render_preview_image(
        scale=scale, checker=True, grid=True, pivots=pivots, origin=origin
    )

    margin = 16
    top_w = clean_view.width * 2 + margin * 3
    top_h = clean_view.height + margin * 2

    # 個別パーツのミニプレビュータイル (最大6列)
    part_scale = max(2, scale // 2)
    cell_w = cw * part_scale + 8
    cell_h = ch * part_scale + 8
    cols = max(1, min(6, len(loaded_parts)))
    rows = math.ceil(len(loaded_parts) / cols) if loaded_parts else 0
    parts_area_w = cols * cell_w + margin * 2
    parts_area_h = (rows * cell_h + margin) if rows > 0 else 0

    sheet_w = max(top_w, parts_area_w)
    sheet_h = top_h + parts_area_h
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (28, 30, 36, 255))
    draw = ImageDraw.Draw(sheet)

    # 上段: 左=クリーン合成、右=グリッド＆ピボット＆接地線
    sheet.alpha_composite(clean_view, dest=(margin, margin))
    sheet.alpha_composite(debug_view, dest=(margin * 2 + clean_view.width, margin))
    draw.rectangle([margin - 1, margin - 1, margin + clean_view.width, margin + clean_view.height], outline=(90, 96, 110, 255))
    draw.rectangle(
        [margin * 2 + clean_view.width - 1, margin - 1, margin * 2 + clean_view.width * 2, margin + debug_view.height],
        outline=(90, 96, 110, 255),
    )

    # 下段: 分割パーツ一覧
    y_start = top_h
    for idx, (_pid, p_img, _piv) in enumerate(loaded_parts):
        r = idx // cols
        c = idx % cols
        bx = margin + c * cell_w
        by = y_start + r * cell_h
        draw.rectangle([bx, by, bx + cw * part_scale + 3, by + ch * part_scale + 3], fill=(44, 47, 56, 255), outline=(72, 76, 90, 255))
        up = p_img.resize((p_img.width * part_scale, p_img.height * part_scale), resample=Image.Resampling.NEAREST)
        sheet.alpha_composite(up, dest=(bx + 2, by + 2))

    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description="Composite character parts and generate zoomed inspection preview.")
    parser.add_argument("meta_json", type=Path, help="Path to <asset_id>_meta.json")
    parser.add_argument("--out-dir", type=Path, default=Path("workspace/03_preview"), help="Output directory for preview PNG")
    parser.add_argument("--preset", type=str, default="default", help="Variant preset name defined in meta.json")
    parser.add_argument("--scale", type=int, default=8, help="Integer upscale factor for preview (default: 8)")
    parser.add_argument("--save-base", action="store_true", help="Also write 1x <asset_id>_base.png next to meta.json")
    args = parser.parse_args()

    meta = json.loads(args.meta_json.read_text(encoding="utf-8"))
    asset_id = meta.get("asset_id", args.meta_json.stem.replace("_meta", ""))
    composite_canvas, loaded_parts = composite_character(args.meta_json, preset=args.preset)

    if args.save_base:
        base_out = args.meta_json.parent / f"{asset_id}_base.png"
        composite_canvas.save(base_out)
        print(f"[OK] Saved 1x base composite: {base_out}")

    sheet = build_inspection_sheet(meta, composite_canvas, loaded_parts, scale=args.scale)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    preview_out = args.out_dir / f"{asset_id}_{args.preset}_rig_preview_{args.scale}x.png"
    sheet.save(preview_out, format="PNG")
    print(f"[OK] Saved inspection sheet: {preview_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
