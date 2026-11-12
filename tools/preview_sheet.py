#!/usr/bin/env python3
"""
preview_sheet.py — スプライトシート＆複数サイズ区分(S/M/L/XL)ラインナップの視覚確認プレビュー生成ツール

【目的】
どのAIモデルでも「動き・シルエット識別性・4種の床背景での視認性・S/M/L/XLのサイズ対比」を
ワンコマンドで `workspace/03_preview/` に出力して視覚セルフレビューできるようにする。

出力内容:
  1. --sheet <sheet.json> 指定時:
     - <id>_frames_<N>x.png     : グリッド線＋接地ライン(origin)付きの全フレーム拡大シート
     - <id>_silhouette_6x.png   : シルエット識別性チェック用の黒塗りシート
     - <id>_grounds_4x.png      : 4種の地面背景（草原・土・石床・暗所）＋等倍(1x)での視認性モック
     - <id>_<anim>_6x.gif       : アニメーション確認用ループGIF

  2. --lineup <assets_dir> 指定時:
     - scale_lineup_4x.png      : assets/ 内の全キャラ・モブ・モンスター・ボス(32x32〜128x128混在OK)を
                                  共通の接地ラインに揃えて並べた4種地面のサイズ対比シート

CLI使用例:
  py tools/preview_sheet.py --sheet assets/characters/chr_001_hero/spritesheets/chr_001_hero_sheet.json --out-dir workspace/03_preview
  py tools/preview_sheet.py --lineup assets --out-dir workspace/03_preview
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

from pixel_canvas import PixelCanvas

# パレット指定がない場合でも機能する標準4地形カラー（草原・土道・石床・暗所バトル）
DEFAULT_GROUNDS: list[tuple[str, tuple[int, int, int, int]]] = [
    ("grass", (72, 152, 64, 255)),
    ("dirt", (184, 134, 88, 255)),
    ("stone", (124, 134, 150, 255)),
    ("dark", (28, 30, 42, 255)),
]


def _upscale(img: Image.Image, scale: int) -> Image.Image:
    return img.resize((img.width * scale, img.height * scale), resample=Image.Resampling.NEAREST)


def _silhouette(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    out = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    sp, op = rgba.load(), out.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            if sp[x, y][3] > 0:
                op[x, y] = (18, 18, 26, 255)
    return out


def _hstack(images: list[Image.Image], gap: int = 6, bg: tuple[int, int, int, int] = (36, 38, 48, 255)) -> Image.Image:
    w = sum(im.width for im in images) + gap * max(0, len(images) - 1)
    h = max(im.height for im in images)
    out = Image.new("RGBA", (w, h), bg)
    x = 0
    for im in images:
        out.alpha_composite(im.convert("RGBA"), dest=(x, h - im.height))
        x += im.width + gap
    return out


def _vstack(images: list[Image.Image], gap: int = 6, bg: tuple[int, int, int, int] = (36, 38, 48, 255)) -> Image.Image:
    w = max(im.width for im in images)
    h = sum(im.height for im in images) + gap * max(0, len(images) - 1)
    out = Image.new("RGBA", (w, h), bg)
    y = 0
    for im in images:
        out.alpha_composite(im.convert("RGBA"), dest=(0, y))
        y += im.height + gap
    return out


def generate_sheet_previews(sheet_json_path: Path, out_dir: Path, scale: int = 8) -> list[Path]:
    meta = json.loads(sheet_json_path.read_text(encoding="utf-8"))
    asset_id = meta.get("asset_id", sheet_json_path.stem.replace("_sheet", ""))
    img_rel = meta.get("image", f"{asset_id}_sheet.png")
    sheet_png_path = sheet_json_path.parent / img_rel
    if not sheet_png_path.exists():
        raise FileNotFoundError(f"Spritesheet PNG not found: {sheet_png_path}")

    sheet = Image.open(sheet_png_path).convert("RGBA")
    cw, ch = meta["cell_size"]
    pad = int(meta.get("padding", 0))
    origin_list = meta.get("origin")
    origin = (int(origin_list[0]), int(origin_list[1])) if origin_list else (cw // 2, ch - 2)
    anims: dict[str, dict] = meta.get("animations", {})

    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    # 行ごとのアニメーションを抽出（1フレームのみの重複idleエイリアスは複数フレーム行があればGIFから除外可）
    multi_frame_rows = {a["row"] for a in anims.values() if int(a.get("frames", 1)) > 1}
    ordered_anims: list[tuple[str, dict, list[Image.Image]]] = []
    for anim_name, a_spec in anims.items():
        row = int(a_spec["row"])
        start_col = int(a_spec.get("start_col", 0))
        n_frames = int(a_spec.get("frames", 1))
        if n_frames == 1 and row in multi_frame_rows and anim_name.startswith("idle_"):
            continue
        frames: list[Image.Image] = []
        for idx in range(n_frames):
            col = start_col + idx
            x0 = col * (cw + pad)
            y0 = row * (ch + pad)
            frames.append(sheet.crop((x0, y0, x0 + cw, y0 + ch)))
        if (
            asset_id.startswith("chr_")
            and anim_name.startswith(("walk", "run"))
            and len(frames) >= 4
            and len(frames) % 2 == 0
        ):
            half = len(frames) // 2
            if [f.tobytes() for f in frames[:half]] == [f.tobytes() for f in frames[half:]]:
                print(
                    f"[PREVIEW WARN] {asset_id}/{anim_name}: frame 0==2 & frame 1==3 (2-frame hop duplication detected!). "
                    f"Alternate left/right foot stride (see: py tools/character_blueprints.py --walk sfc_16x24 right).",
                    file=sys.stderr,
                )
        ordered_anims.append((anim_name, a_spec, frames))

    if not ordered_anims:
        return saved

    # 1. グリッド＋接地ライン付き拡大フレーム一覧
    grid_rows: list[Image.Image] = []
    sil_rows: list[Image.Image] = []
    rep_frames: list[Image.Image] = []
    for anim_name, _, frames in ordered_anims:
        cells = [
            PixelCanvas.from_image(fr).render_preview_image(scale=scale, checker=True, grid=True, origin=origin)
            for fr in frames
        ]
        row_img = _hstack(cells, gap=6)
        labeled = Image.new("RGBA", (row_img.width + 110, row_img.height), (28, 30, 40, 255))
        dr = ImageDraw.Draw(labeled)
        dr.text((8, max(4, row_img.height // 2 - 6)), anim_name, fill=(220, 228, 245, 255))
        labeled.alpha_composite(row_img, (110, 0))
        grid_rows.append(labeled)

        s_cells = [_upscale(_silhouette(fr), 6) for fr in frames]
        sil_rows.append(_hstack(s_cells, gap=6, bg=(232, 234, 240, 255)))
        rep_frames.append(frames[0])

    frames_out = out_dir / f"{asset_id}_frames_{scale}x.png"
    _vstack(grid_rows, gap=8, bg=(28, 30, 40, 255)).save(frames_out)
    saved.append(frames_out)

    # 2. シルエット確認シート
    sil_out = out_dir / f"{asset_id}_silhouette_6x.png"
    _vstack(sil_rows, gap=6, bg=(232, 234, 240, 255)).save(sil_out)
    saved.append(sil_out)

    # 3. 4種の床色（草・土・石・暗所）＋ 等倍(1x)視認性モック
    ground_strips: list[Image.Image] = []
    strip_frames = ordered_anims[0][2] if len(ordered_anims) == 1 else rep_frames
    for _, g_rgba in DEFAULT_GROUNDS:
        strip = Image.new("RGBA", (cw * len(strip_frames), ch), g_rgba)
        for i, fr in enumerate(strip_frames):
            strip.alpha_composite(fr, (i * cw, 0))
        ground_strips.append(_upscale(strip, 4))
    actual_strip = Image.new("RGBA", (ground_strips[0].width, ch + 8), DEFAULT_GROUNDS[0][1])
    for i, fr in enumerate(strip_frames):
        actual_strip.alpha_composite(fr, (4 + i * (cw + 4), 4))
    grounds_out = out_dir / f"{asset_id}_grounds_4x.png"
    _vstack(ground_strips + [actual_strip], gap=0).save(grounds_out)
    saved.append(grounds_out)

    # 4. アニメーションGIF (6x)
    for anim_name, a_spec, frames in ordered_anims:
        if len(frames) < 2:
            continue
        fps = max(1, int(a_spec.get("fps", 6)))
        gif_imgs = []
        for fr in frames:
            bg_cell = Image.new("RGBA", (cw, ch), DEFAULT_GROUNDS[0][1])
            bg_cell.alpha_composite(fr, (0, 0))
            gif_imgs.append(_upscale(bg_cell, 6).convert("RGB"))
        gif_out = out_dir / f"{asset_id}_{anim_name}_6x.gif"
        gif_imgs[0].save(
            gif_out,
            save_all=True,
            append_images=gif_imgs[1:],
            duration=int(1000 / fps),
            loop=0,
        )
        saved.append(gif_out)

    return saved


def _infer_sprite_origin(asset_dir: Path, img: Image.Image) -> tuple[int, int]:
    meta_path = asset_dir / f"{asset_dir.name}_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if "origin" in meta:
            return int(meta["origin"][0]), int(meta["origin"][1])
    sheet_json = asset_dir / "spritesheets" / f"{asset_dir.name}_sheet.json"
    if sheet_json.exists():
        smeta = json.loads(sheet_json.read_text(encoding="utf-8"))
        if "origin" in smeta:
            return int(smeta["origin"][0]), int(smeta["origin"][1])
    # メタデータがない場合は最下端の不透明ピクセル + 1 を接地ラインとする
    px = img.load()
    ys = [y for y in range(img.height) for x in range(img.width) if px[x, y][3] > 0]
    max_y = max(ys) if ys else (img.height - 2)
    return img.width // 2, max_y + 1


def generate_scale_lineup(assets_dir: Path, out_dir: Path, scale: int = 4) -> Path | None:
    """
    assets/characters と assets/monsters の全ベース立ち絵を収集し、
    キャンバスサイズ (16x16〜128x128) が異なっても共通の接地床ラインに足底を揃えて並べる。
    """
    entries: list[tuple[str, Image.Image, tuple[int, int]]] = []
    for sub in ("characters", "monsters"):
        root = assets_dir / sub
        if not root.is_dir():
            continue
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            candidates = [
                d / f"{d.name}_base.png",
                d / f"{d.name}_down.png",
                d / "stand" / f"{d.name}_stand_down.png",
            ]
            base_png = next((p for p in candidates if p.is_file()), None)
            if base_png is None:
                continue
            im = Image.open(base_png).convert("RGBA")
            orig = _infer_sprite_origin(d, im)
            entries.append((d.name, im, orig))

    if not entries:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    max_above = max(orig[1] for _, _, orig in entries) + 4
    max_below = max(im.height - orig[1] for _, im, orig in entries) + 4
    stage_h = max_above + max_below
    pad_x = 8
    stage_w = pad_x + sum(im.width + pad_x for _, im, _ in entries)
    ground_line_y = max_above - 1

    strips: list[Image.Image] = []
    for _, g_rgba in DEFAULT_GROUNDS:
        stage = Image.new("RGBA", (stage_w, stage_h), g_rgba)
        # 接地床の1px暗線ガイドを薄く引く
        dr = ImageDraw.Draw(stage)
        floor_c = (max(0, g_rgba[0] - 22), max(0, g_rgba[1] - 22), max(0, g_rgba[2] - 22), 255)
        dr.line([(0, ground_line_y + 1), (stage_w - 1, ground_line_y + 1)], fill=floor_c)
        cur_x = pad_x
        for _, im, orig in entries:
            paste_y = max_above - orig[1]
            stage.alpha_composite(im, (cur_x, paste_y))
            cur_x += im.width + pad_x
        strips.append(_upscale(stage, scale))

    out_path = out_dir / f"scale_lineup_{scale}x.png"
    _vstack(strips, gap=0).save(out_path)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="スプライトシート拡大・シルエット・4地形モック・GIF・サイズ対比ラインナップ生成ツール")
    parser.add_argument("--sheet", type=Path, default=None, help="対象の <asset_id>_sheet.json パス")
    parser.add_argument("--lineup", type=Path, default=None, help="assets/ ルートディレクトリを指定して S/M/L/XL サイズ対比シートを生成")
    parser.add_argument("--out-dir", type=Path, default=Path("workspace/03_preview"), help="プレビュー出力先ディレクトリ")
    parser.add_argument("--scale", type=int, default=8, help="--sheet 時のフレーム拡大倍率 (default: 8)")
    args = parser.parse_args()

    if not args.sheet and not args.lineup:
        parser.print_help()
        return 1

    if args.sheet:
        outs = generate_sheet_previews(args.sheet, args.out_dir, scale=args.scale)
        for p in outs:
            print(f"[PREVIEW OK] {p}")

    if args.lineup:
        lp = generate_scale_lineup(args.lineup, args.out_dir, scale=4)
        if lp:
            print(f"[LINEUP OK]  {lp}")
        else:
            print(f"[WARN] No character/monster base PNGs found in {args.lineup}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
