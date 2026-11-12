#!/usr/bin/env python3
"""
pack_spritesheet.py — 個別フレーム画像群から汎用スプライトシートPNG＋メタデータJSONを生成するツール

使い方1（単一フォルダ内の連番フレームを1行シート化）:
  py tools/pack_spritesheet.py --frames-dir workspace/02_work/mon_001_slime/idle \
      --asset-id mon_001_slime --anim-name idle --fps 6 \
      --out assets/monsters/mon_001_slime/spritesheets/mon_001_slime_sheet.png

使い方2（複数アニメーション定義JSONから複数行シート化）:
  py tools/pack_spritesheet.py --spec workspace/02_work/chr_001_hero/sheet_build.json \
      --out assets/characters/chr_001_hero/spritesheets/chr_001_hero_sheet.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def pack_rows(
    asset_id: str,
    rows_spec: list[dict],
    out_png: Path,
    *,
    cell_size: tuple[int, int] | None = None,
    origin: list[int] | None = None,
    padding: int = 0,
) -> tuple[Path, Path]:
    loaded_rows: list[tuple[dict, list[Image.Image]]] = []
    max_w, max_h, max_cols = 0, 0, 0

    for row_info in rows_spec:
        frames = [Image.open(Path(fp)).convert("RGBA") for fp in row_info["files"]]
        if not frames:
            raise ValueError(f"Animation '{row_info['name']}' has no frame files.")
        for im in frames:
            max_w = max(max_w, im.width)
            max_h = max(max_h, im.height)
        max_cols = max(max_cols, len(frames))
        loaded_rows.append((row_info, frames))

    cw, ch = cell_size if cell_size else (max_w, max_h)
    num_rows = len(loaded_rows)
    sheet_w = max_cols * cw + max(0, max_cols - 1) * padding
    sheet_h = num_rows * ch + max(0, num_rows - 1) * padding

    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    animations_meta: dict[str, dict] = {}

    for r_idx, (row_info, frames) in enumerate(loaded_rows):
        for c_idx, frame_img in enumerate(frames):
            dx = c_idx * (cw + padding) + (cw - frame_img.width) // 2
            dy = r_idx * (ch + padding) + (ch - frame_img.height)
            sheet.alpha_composite(frame_img, dest=(dx, dy))

        animations_meta[row_info["name"]] = {
            "row": r_idx,
            "start_col": 0,
            "frames": len(frames),
            "fps": int(row_info.get("fps", 8)),
            "loop": bool(row_info.get("loop", True)),
        }

    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png, format="PNG")

    meta_out = out_png.with_suffix(".json")
    meta_payload = {
        "schema_version": "1.0",
        "asset_id": asset_id,
        "image": out_png.name,
        "sheet_size": [sheet_w, sheet_h],
        "cell_size": [cw, ch],
        "origin": origin if origin is not None else [cw // 2, ch - 4],
        "padding": padding,
        "animations": animations_meta,
    }
    meta_out.write_text(json.dumps(meta_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_png, meta_out


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack animation frames into a spritesheet PNG + JSON.")
    parser.add_argument("--spec", type=Path, help="JSON build spec listing multiple animation rows")
    parser.add_argument("--frames-dir", type=Path, help="Directory of sequential PNG frames (single-row mode)")
    parser.add_argument("--asset-id", type=str, default="sprite_asset", help="Asset ID for metadata")
    parser.add_argument("--anim-name", type=str, default="idle", help="Animation name in single-row mode")
    parser.add_argument("--fps", type=int, default=8, help="FPS in single-row mode")
    parser.add_argument("--no-loop", action="store_true", help="Disable loop flag in single-row mode")
    parser.add_argument("--padding", type=int, default=0, help="Transparent pixel padding between cells")
    parser.add_argument("--out", type=Path, required=True, help="Output spritesheet PNG path")
    args = parser.parse_args()

    if args.spec:
        spec_data = json.loads(args.spec.read_text(encoding="utf-8"))
        base = args.spec.parent
        rows_spec = []
        for anim_name, info in spec_data["animations"].items():
            files = [str(base / f) if not Path(f).is_absolute() else f for f in info["files"]]
            rows_spec.append(
                {
                    "name": anim_name,
                    "files": files,
                    "fps": info.get("fps", 8),
                    "loop": info.get("loop", True),
                }
            )
        cell_sz = tuple(spec_data["cell_size"]) if "cell_size" in spec_data else None
        png_p, json_p = pack_rows(
            asset_id=spec_data.get("asset_id", args.asset_id),
            rows_spec=rows_spec,
            out_png=args.out,
            cell_size=cell_sz,
            origin=spec_data.get("origin"),
            padding=spec_data.get("padding", args.padding),
        )
    elif args.frames_dir:
        frame_files = sorted(str(p) for p in args.frames_dir.glob("*.png"))
        if not frame_files:
            print(f"[ERROR] No PNG files found in {args.frames_dir}", file=sys.stderr)
            return 1
        rows_spec = [
            {
                "name": args.anim_name,
                "files": frame_files,
                "fps": args.fps,
                "loop": not args.no_loop,
            }
        ]
        png_p, json_p = pack_rows(
            asset_id=args.asset_id,
            rows_spec=rows_spec,
            out_png=args.out,
            padding=args.padding,
        )
    else:
        parser.error("Either --spec or --frames-dir must be provided.")
        return 1

    print(f"[OK] Packed spritesheet: {png_p}")
    print(f"[OK] Wrote metadata:    {json_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
