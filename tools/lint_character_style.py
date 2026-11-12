#!/usr/bin/env python3
"""
lint_character_style.py — キャラクタードット絵のプロポーション・造形スタイル自動リンター

【目的】
フォーマット検証（validate_assets.py）だけでは見抜けない「AI特有のプログラマーアート癖」
（サイズ間延び、首伸び、左右完全対称のきのこ頭、内部の黒横線による輪切り、色数超過など）を
数値解析で自動検出し、どのAIモデルでも日本式2Dドット絵の品質基準を維持できるようにする。

使用例:
  py tools/lint_character_style.py assets/characters/chr_001_hero/spritesheets/chr_001_hero_sheet.png --frame 32x32 --size sfc_16x24 --taste cool
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from PIL import Image

from character_blueprints import get_size_spec, get_taste_spec


def is_near_black(rgb: tuple[int, int, int]) -> bool:
    r, g, b = rgb
    return r <= 30 and g <= 28 and b <= 45


def lint_sprite_image(
    img: Image.Image,
    size_id: str,
    taste_id: str,
    label: str = "sprite",
) -> tuple[list[str], list[str]]:
    """1フレーム分のRGBA画像を解析し、(errors, warnings) を返す。"""
    errors: list[str] = []
    warnings: list[str] = []

    size_spec = get_size_spec(size_id)
    _ = get_taste_spec(taste_id)

    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    exp_cw, exp_ch = size_spec["canvas_size"]
    wep_cw, wep_ch = size_spec["weapon_canvas_size"]
    if (w, h) not in ((exp_cw, exp_ch), (wep_cw, wep_ch)):
        warnings.append(
            f"[{label}] キャンバスサイズ {w}x{h}px が規格 {size_id} の標準 "
            f"({exp_cw}x{exp_ch} または {wep_cw}x{wep_ch}) と異なります。"
        )

    opaque_coords: list[tuple[int, int]] = []
    unique_colors: set[tuple[int, int, int]] = set()
    near_black_count = 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0:
                opaque_coords.append((x, y))
                unique_colors.add((r, g, b))
                if is_near_black((r, g, b)):
                    near_black_count += 1

    if not opaque_coords:
        errors.append(f"[{label}] 不透明ピクセルが存在しません（空の画像です）。")
        return errors, warnings

    min_x = min(x for x, _ in opaque_coords)
    max_x = max(x for x, _ in opaque_coords)
    min_y = min(y for _, y in opaque_coords)
    max_y = max(y for _, y in opaque_coords)
    bbox_w = max_x - min_x + 1
    bbox_h = max_y - min_y + 1

    # 1. 実身長（縦バウンディングボックス）チェック
    min_h, max_h = size_spec["body_height_range"]
    if not (min_h <= bbox_h <= max_h):
        errors.append(
            f"[{label}] 実身長 {bbox_h}px が規格 '{size_id}' の推奨範囲 ({min_h}〜{max_h}px) を外れています。"
            f" 頭:体:足のピクセル配分を見直してください。"
        )

    # 2. 横幅チェック（武器・マント余白 +6px まで許容）
    min_bw, max_bw = size_spec["body_width_range"]
    if bbox_w < min_bw:
        warnings.append(f"[{label}] 横幅 {bbox_w}px が規格 '{size_id}' の最小目安 ({min_bw}px) より細すぎます。")
    elif bbox_w > max_bw + 6:
        errors.append(
            f"[{label}] 横幅 {bbox_w}px が規格 '{size_id}' の上限目安 ({max_bw}px + 武器余白6px) を大きく超過しています。"
            f" 胴体や頭部が横に間延びしていないか確認してください。"
        )

    # 3. 色数上限チェック
    color_cnt = len(unique_colors)
    max_col = size_spec["max_colors_limit"]
    if color_cnt > max_col:
        warnings.append(
            f"[{label}] 使用色数 {color_cnt}色 が規格 '{size_id}' の上限目安 ({max_col}色) を超えています。"
        )

    # 4. 主線・色トレス方針チェック
    policy = size_spec["outline_policy"]
    if policy == "selout_no_pure_black":
        ratio = near_black_count / len(opaque_coords)
        if ratio > 0.08:
            warnings.append(
                f"[{label}] 色トレス推奨規格 ('{size_id}') ですが、濃黒ピクセルが全体の {ratio:.0%} を占めています。"
                f" 純黒・濃黒主線を減らし、各素材の deep 影色（Sel-Out）へ置き換えてください。"
            )

    # 内部の長い黒横線（輪切りボーダー）検知
    if policy in ("outer_dark_inner_selout", "selout_no_pure_black"):
        max_interior_black_run = 0
        y_start = min_y + int(bbox_h * 0.35)
        y_end = min_y + int(bbox_h * 0.85)
        for y in range(max(1, y_start), min(h - 1, y_end)):
            run = 0
            for x in range(min_x + 1, max_x):
                r, g, b, a = px[x, y]
                up_a = px[x, y - 1][3]
                dn_a = px[x, y + 1][3]
                if a > 0 and is_near_black((r, g, b)) and up_a > 0 and dn_a > 0:
                    run += 1
                    max_interior_black_run = max(max_interior_black_run, run)
                else:
                    run = 0
        threshold_run = 9 if taste_id == "cute" else 7
        if max_interior_black_run >= threshold_run:
            warnings.append(
                f"[{label}] キャラ内部に長さ {max_interior_black_run}px の連続した黒横線が検出されました。"
                f" 顎下やベルトが黒線で輪切りになると野暮ったく見えるため、同系色の暗色シェード（色トレス）で繋ぐことを推奨します。"
            )

    # 5. 首なし直結規格での「細い首（ろくろ首）」検知
    if not size_spec["has_neck"]:
        row_widths: list[int] = []
        for y in range(min_y, max_y + 1):
            xs = [x for x in range(w) if px[x, y][3] > 0]
            row_widths.append((max(xs) - min(xs) + 1) if xs else 0)

        neck_zone_start = int(bbox_h * 0.35)
        neck_zone_end = int(bbox_h * 0.65)
        thin_streak = 0
        for ry in range(neck_zone_start, neck_zone_end):
            if 0 < row_widths[ry] <= 4:
                thin_streak += 1
                if thin_streak >= 2:
                    errors.append(
                        f"[{label}] 首なし直結規格 ('{size_id}') で幅4px以下の細い首が2行以上連続しています。"
                        f" 顎の下端ラインを肩・襟の上端へ直接乗せてください。"
                    )
                    break
            else:
                thin_streak = 0

    # 6. 頭部上端の完全左右対称（お椀・きのこヘルメット型）検知
    if taste_id in ("cool", "cute") and bbox_h >= 18:
        top_rows = max(4, int(bbox_h * 0.28))
        symmetric_rows = 0
        checked_rows = 0
        # 頭部の中心Xを推定
        head_xs = [
            x
            for y in range(min_y, min_y + top_rows)
            for x in range(w)
            if px[x, y][3] > 0
        ]
        if head_xs:
            h_min_x, h_max_x = min(head_xs), max(head_xs)
            for y in range(min_y, min_y + top_rows):
                row_mask = [1 if px[x, y][3] > 0 else 0 for x in range(h_min_x, h_max_x + 1)]
                if sum(row_mask) >= 2:
                    checked_rows += 1
                    if row_mask == list(reversed(row_mask)):
                        symmetric_rows += 1
            if checked_rows >= 4 and symmetric_rows == checked_rows:
                warnings.append(
                    f"[{label}] 頭部上端（{checked_rows}行）のシルエットが100%左右対称（お椀・きのこ型）になっています。"
                    f" '{taste_id}' テイストでは斜め分けや外ハネ毛束を入れて非対称な魅力を作ることを推奨します。"
                )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="キャラクタードット絵のプロポーション＆スタイル自動リンター")
    parser.add_argument("image", type=Path, help="検証対象の等倍PNGパス")
    parser.add_argument("--size", required=True, help="サイズ規格ID (fc_16x16 / sfc_16x24 / hd2d_18x32 / high_32x56)")
    parser.add_argument("--taste", required=True, help="テイストID (cute / cool / retro_classic / dark_serious)")
    parser.add_argument("--frame", default=None, help="スプライトシートの場合の1フレームサイズ (例: 32x32) — 先頭フレームを検証")
    parser.add_argument("--strict", action="store_true", help="警告(WARN)もエラー終了コードとして扱う")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"[FATAL] File not found: {args.image}", file=sys.stderr)
        return 2

    img = Image.open(args.image).convert("RGBA")
    if args.frame:
        fw_s, fh_s = args.frame.lower().split("x")
        fw, fh = int(fw_s), int(fh_s)
        img = img.crop((0, 0, fw, fh))

    errors, warnings = lint_sprite_image(img, args.size, args.taste, label=args.image.name)

    for w_msg in warnings:
        print(f"[STYLE WARN]  {w_msg}")
    for e_msg in errors:
        print(f"[STYLE ERROR] {e_msg}")

    if not errors and not warnings:
        print(f"[STYLE PASS]  {args.image.name} conforms cleanly to ({args.size} x {args.taste}).")
        return 0

    if errors or (args.strict and warnings):
        print(f"[STYLE FAIL]  {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1

    print(f"[STYLE OK*]   0 errors, {len(warnings)} advisory warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
