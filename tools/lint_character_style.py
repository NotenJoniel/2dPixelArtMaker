#!/usr/bin/env python3
"""
lint_character_style.py — キャラクター＆モンスターのプロポーション・サイズ区分・造形スタイル自動リンター

【目的】
フォーマット検証（validate_assets.py）だけでは見抜けない「AI特有のプログラマーアート癖・モブ化癖」
（サイズ間延び、首伸び、左右完全対称のきのこ頭、兜や帽子の水平一直線バンド、内部の黒横線輪切り、色数超過など）を
数値解析で自動検出し、どのAIモデルでも日本式2Dドット絵の品質基準を維持できるようにする。

使用例:
  # 主人公・仲間キャラ (Mサイズ標準)
  py tools/lint_character_style.py assets/characters/chr_001_hero/chr_001_hero_base.png --size sfc_16x24 --taste retro_classic --role hero

  # 街のモブNPC / 大型キャラ(L)
  py tools/lint_character_style.py assets/characters/chr_101_villager/chr_101_villager_base.png --size sfc_16x24 --taste retro_classic --role mob
  py tools/lint_character_style.py assets/characters/chr_003_general/chr_003_general_base.png --size sfc_16x24 --taste cool --scale L --role party

  # モンスター（S:小型ザコ / M:標準 / L:中ボス / XL:大ボス）
  py tools/lint_character_style.py assets/monsters/mon_001_slime/mon_001_slime_base.png --category monster --size sfc_16x24 --taste retro_classic --scale S --check-ground
  py tools/lint_character_style.py assets/monsters/mon_101_dragon/mon_101_dragon_base.png --category monster --size sfc_16x24 --taste dark_serious --scale XL --role boss
"""

from __future__ import annotations

import argparse
from collections import deque
import sys
from pathlib import Path
from PIL import Image

from character_blueprints import get_role_spec, get_scale_spec, get_size_spec, get_taste_spec


def is_near_black(rgb: tuple[int, int, int]) -> bool:
    r, g, b = rgb
    return r <= 30 and g <= 28 and b <= 45


def is_dark_border_color(rgb: tuple[int, int, int], outline_policy: str) -> bool:
    """主線または色トレスの最深境界色として妥当な暗色かを判定する。"""
    r, g, b = rgb
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    threshold = 72.0 if outline_policy == "selout_no_pure_black" else 55.0
    return lum <= threshold


def find_enclosed_transparent_holes(rgba: Image.Image) -> list[list[tuple[int, int]]]:
    """
    キャンバス外周から8近傍で到達できない「内部に閉じ込められた完全透明(alpha==0)領域」を抽出する。
    ドット絵の1px斜め主線（外周と斜めに接するくぼみ）は外周背景として正しく除外される。
    """
    w, h = rgba.size
    px = rgba.load()
    exterior = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()
    dirs8 = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))

    for x in range(w):
        for y in (0, h - 1):
            if px[x, y][3] == 0 and not exterior[y][x]:
                exterior[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if px[x, y][3] == 0 and not exterior[y][x]:
                exterior[y][x] = True
                q.append((x, y))

    while q:
        cx, cy = q.popleft()
        for dx, dy in dirs8:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and not exterior[ny][nx] and px[nx, ny][3] == 0:
                exterior[ny][nx] = True
                q.append((nx, ny))

    visited = [[False] * w for _ in range(h)]
    holes: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0 and not exterior[y][x] and not visited[y][x]:
                comp: list[tuple[int, int]] = []
                dq: deque[tuple[int, int]] = deque([(x, y)])
                visited[y][x] = True
                while dq:
                    cx, cy = dq.popleft()
                    comp.append((cx, cy))
                    for dx, dy in dirs8:
                        nx, ny = cx + dx, cy + dy
                        if (
                            0 <= nx < w
                            and 0 <= ny < h
                            and px[nx, ny][3] == 0
                            and not exterior[ny][nx]
                            and not visited[ny][nx]
                        ):
                            visited[ny][nx] = True
                            dq.append((nx, ny))
                holes.append(comp)
    return holes


def lint_sprite_image(
    img: Image.Image,
    size_id: str,
    taste_id: str,
    category: str = "character",
    scale_id: str = "M",
    role_id: str = "hero",
    check_ground: bool = False,
    ground_y_override: int | None = None,
    label: str = "sprite",
) -> tuple[list[str], list[str]]:
    """1フレーム分のRGBA画像を解析し、(errors, warnings) を返す。"""
    errors: list[str] = []
    warnings: list[str] = []

    size_spec = get_size_spec(size_id)
    scale_spec = get_scale_spec(size_id, scale_id)
    _ = get_taste_spec(taste_id)
    _ = get_role_spec(role_id)

    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    exp_cw, exp_ch = scale_spec["canvas_size"]
    wep_cw, wep_ch = size_spec["weapon_canvas_size"] if scale_id.upper() == "M" else (exp_cw, exp_ch)
    if (w, h) not in ((exp_cw, exp_ch), (wep_cw, wep_ch)):
        warnings.append(
            f"[{label}] キャンバスサイズ {w}x{h}px が ({size_id} / scale={scale_id.upper()}) の標準 "
            f"({exp_cw}x{exp_ch}) と異なります。"
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

    # 1. 実身長（縦バウンディングボックス）チェック（S/M/L/XL 対応）
    min_h, max_h = scale_spec["height_range"]
    if not (min_h <= bbox_h <= max_h):
        errors.append(
            f"[{label}] 実寸高さ {bbox_h}px が規格 '{size_id}' (scale={scale_id.upper()}) の推奨範囲 "
            f"({min_h}〜{max_h}px) を外れています。"
        )

    # 2. 横幅チェック（武器・杖・翼の余白として character は +6px、monster L/XL は +4px 許容）
    min_bw, max_bw = scale_spec["width_range"]
    extra_margin = 6 if category == "character" else (4 if scale_id.upper() in ("L", "XL") else 2)
    if bbox_w < min_bw:
        warnings.append(
            f"[{label}] 横幅 {bbox_w}px が規格 '{size_id}' (scale={scale_id.upper()}) の最小目安 ({min_bw}px) より細めです。"
        )
    elif bbox_w > max_bw + extra_margin:
        errors.append(
            f"[{label}] 横幅 {bbox_w}px が規格 '{size_id}' (scale={scale_id.upper()}) の上限目安 "
            f"({max_bw}px + 装備余白{extra_margin}px) を超過しています。"
        )

    # 3. 接地ライン（ground_y）チェック（指定時）
    if check_ground or ground_y_override is not None:
        exp_ground_y = ground_y_override if ground_y_override is not None else (scale_spec["origin"][1] - 1)
        if max_y != exp_ground_y:
            errors.append(
                f"[{label}] 下端接地Y座標 (y={max_y}) が基準接地ライン (y={exp_ground_y}, origin={list(scale_spec['origin'])}) と一致していません。"
            )

    # 4. 色数上限チェック（mob の場合は主役より控えめかもアドバイス）
    color_cnt = len(unique_colors)
    max_col = scale_spec["max_colors_limit"]
    if color_cnt > max_col:
        warnings.append(
            f"[{label}] 使用色数 {color_cnt}色 が ({size_id} / scale={scale_id.upper()}) の上限目安 ({max_col}色) を超えています。"
        )
    elif role_id == "mob" and size_id != "fc_16x16" and color_cnt >= max_col - 1:
        warnings.append(
            f"[{label}] モブNPC (role=mob) で {color_cnt}色 使用しています。主役パーティを引き立てるため、モブは主役より2〜4色絞る設計を推奨します。"
        )

    # 5. 主線・色トレス方針チェック
    policy = size_spec["outline_policy"]
    if policy == "selout_no_pure_black":
        ratio = near_black_count / len(opaque_coords)
        if ratio > 0.08:
            warnings.append(
                f"[{label}] 色トレス推奨規格 ('{size_id}') ですが、濃黒ピクセルが全体の {ratio:.0%} を占めています。"
                f" 純黒・濃黒主線を減らし、各素材の deep 影色（Sel-Out）へ置き換えてください。"
            )

    # 5b. 内部の孤立透過ピンホール（前髪と顔の境界隙間・ポリゴン塗り漏れ穴）検知（キャラ・モンスター共通）
    enclosed_holes = find_enclosed_transparent_holes(rgba)
    center_x = scale_spec["origin"][0]
    head_core_half_w = max(3, int(scale_spec["width_range"][1] * 0.35))
    head_y_min = min_y + 2
    head_y_max = min_y + int(bbox_h * 0.48)

    for comp in enclosed_holes:
        hole_size = len(comp)
        cardinal_rgbs: list[tuple[int, int, int]] = []
        for hx, hy in comp:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = hx + dx, hy + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 0:
                    cardinal_rgbs.append(px[nx, ny][:3])

        # (A) 主線で閉じられていない微小ピンホール（1〜4px、周囲4近傍の半数以上に肌・髪・服などの非主線色が直接露出）
        if hole_size <= 4 and cardinal_rgbs:
            non_dark_cnt = sum(1 for rgb in cardinal_rgbs if not is_dark_border_color(rgb, policy))
            if non_dark_cnt * 2 >= len(cardinal_rgbs):
                errors.append(
                    f"[{label}] 内部に主線で囲まれていない透過ピンホール（塗り漏れ穴）が検出されました: "
                    f"座標 {comp[0]} 付近（計{hole_size}px）。前髪と顔の境界やポリゴン継ぎ目の隙間を埋めてください。"
                )
                continue

        # (B) 人型キャラの頭部・顔コア領域内に生じた孤立透過穴（暗色に囲まれていても顔・頭内の穴はNG）
        if category == "character" and hole_size <= 6:
            in_head_core = all(
                head_y_min <= hy <= head_y_max and abs(hx - center_x) <= head_core_half_w
                for hx, hy in comp
            )
            if in_head_core:
                errors.append(
                    f"[{label}] 頭部・顔領域の内部に孤立した透過穴が検出されました: "
                    f"座標 {comp[0]} 付近（計{hole_size}px）。前髪・目元・頭部の塗り残しを確認してください。"
                )

    # 以降の人体プロポーション検査は人型キャラクター（category == "character"）のみに適用
    if category != "character":
        return errors, warnings

    # 6. 内部の長い黒横線（胴体輪切りボーダー）検知
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
        if scale_id.upper() in ("L", "XL"):
            threshold_run = int(threshold_run * 1.5)
        if max_interior_black_run >= threshold_run:
            warnings.append(
                f"[{label}] キャラ内部に長さ {max_interior_black_run}px の連続した黒横線が検出されました。"
                f" 顎下やベルトが黒線で輪切りになると野暮ったく見えるため、同系色の暗色シェード（色トレス）で繋ぐことを推奨します。"
            )

    # 7. 首なし直結規格での「細い首（ろくろ首）」検知
    if not size_spec["has_neck"] and scale_id.upper() in ("S", "M"):
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

    # 8. 頭部上端の完全左右対称（お椀・きのこヘルメット型）検知
    if taste_id in ("cool", "cute") and role_id in ("hero", "party") and bbox_h >= 18:
        top_rows = max(4, int(bbox_h * 0.28))
        symmetric_rows = 0
        checked_rows = 0
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
                    f" 主役・仲間キャラ（role={role_id}）では斜め分けや外ハネ毛束、羽飾り等で非対称な魅力を作ることを推奨します。"
                )

    # 9. 主役・仲間キャラ（hero/party）の「兜・帽子つば・鉢巻の水平一直線バンド（モブ兵士化）」検知
    if role_id in ("hero", "party") and size_id != "fc_16x16" and bbox_h >= 18:
        band_y_start = min_y + int(bbox_h * 0.20)
        band_y_end = min_y + int(bbox_h * 0.45)
        head_xs_zone = [
            x
            for y in range(band_y_start, band_y_end + 1)
            for x in range(w)
            if px[x, y][3] > 0
        ]
        if head_xs_zone:
            head_span = max(head_xs_zone) - min(head_xs_zone) + 1
            flat_threshold = max(9, int(head_span * 0.65))
            longest_flat_band = 0
            for y in range(max(1, band_y_start), min(h - 1, band_y_end + 1)):
                run = 0
                prev_rgb: tuple[int, int, int] | None = None
                for x in range(min_x, max_x + 1):
                    r, g, b, a = px[x, y]
                    rgb = (r, g, b)
                    if a > 0 and not is_near_black(rgb):
                        # 上または下が別色である「水平帯ライン」かどうかを確認
                        up_diff = px[x, y - 1][3] == 0 or px[x, y - 1][:3] != rgb
                        dn_diff = px[x, y + 1][3] == 0 or px[x, y + 1][:3] != rgb
                        if up_diff and dn_diff:
                            run = (run + 1) if rgb == prev_rgb else 1
                            prev_rgb = rgb
                            longest_flat_band = max(longest_flat_band, run)
                        else:
                            run = 0
                            prev_rgb = None
                    else:
                        run = 0
                        prev_rgb = None
            if longest_flat_band >= flat_threshold:
                warnings.append(
                    f"[{label}] 額・帽子領域に単色で長さ {longest_flat_band}px の完全水平な一直線バンドが検出されました。"
                    f" 兜の縁や帽子のつばが真横一直線だとモブ兵士・三角コーンのように単調に見えるため、"
                    f"眉間への1px V字ブリッジ・斜め被り・前髪の覗きを入れることを推奨します。"
                )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="キャラクター＆モンスターのプロポーション・サイズ区分・造形スタイル自動リンター")
    parser.add_argument("image", type=Path, help="検証対象の等倍PNGパス")
    parser.add_argument("--size", required=True, help="サイズ規格ID (fc_16x16 / sfc_16x24 / hd2d_18x32 / high_32x56)")
    parser.add_argument("--taste", required=True, help="テイストID (cute / cool / retro_classic / dark_serious)")
    parser.add_argument(
        "--category",
        choices=("character", "monster"),
        default=None,
        help="アセット種別 (省略時はファイル名先頭 'mon_' なら monster、それ以外は character)",
    )
    parser.add_argument(
        "--scale",
        choices=("S", "M", "L", "XL", "s", "m", "l", "xl"),
        default=None,
        help="サイズ区分 (S:小型 / M:標準 / L:大型・中ボス / XL:特大・大ボス。省略時は character=M, monster=S)",
    )
    parser.add_argument(
        "--role",
        choices=("hero", "party", "mob", "enemy", "midboss", "boss"),
        default=None,
        help="役割ランク (hero / party / mob / enemy / midboss / boss)",
    )
    parser.add_argument("--frame", default=None, help="スプライトシートの場合の1フレームサイズ (例: 32x32) — 先頭フレームを検証")
    parser.add_argument("--check-ground", action="store_true", help="足底・下端が規格の標準接地Y座標(origin[1]-1)に一致しているかも検証")
    parser.add_argument("--ground-y", type=int, default=None, help="任意の接地Y座標を明示指定して検証")
    parser.add_argument("--strict", action="store_true", help="警告(WARN)もエラー終了コードとして扱う")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"[FATAL] File not found: {args.image}", file=sys.stderr)
        return 2

    category = args.category
    if category is None:
        category = "monster" if args.image.name.startswith("mon_") else "character"

    scale_id = (args.scale or ("S" if category == "monster" else "M")).upper()
    if args.role:
        role_id = args.role
    else:
        if category == "monster":
            role_id = "boss" if scale_id == "XL" else ("midboss" if scale_id == "L" else "enemy")
        else:
            role_id = "hero"

    img = Image.open(args.image).convert("RGBA")
    if args.frame:
        fw_s, fh_s = args.frame.lower().split("x")
        fw, fh = int(fw_s), int(fh_s)
        img = img.crop((0, 0, fw, fh))

    errors, warnings = lint_sprite_image(
        img,
        size_id=args.size,
        taste_id=args.taste,
        category=category,
        scale_id=scale_id,
        role_id=role_id,
        check_ground=args.check_ground,
        ground_y_override=args.ground_y,
        label=args.image.name,
    )

    spec_tag = f"{args.size} x {args.taste} | {category} | scale={scale_id} | role={role_id}"
    for w_msg in warnings:
        print(f"[STYLE WARN]  {w_msg}")
    for e_msg in errors:
        print(f"[STYLE ERROR] {e_msg}")

    if not errors and not warnings:
        print(f"[STYLE PASS]  {args.image.name} conforms cleanly to ({spec_tag}).")
        return 0

    if errors or (args.strict and warnings):
        print(f"[STYLE FAIL]  {len(errors)} error(s), {len(warnings)} warning(s) ({spec_tag}).")
        return 1

    print(f"[STYLE OK*]   0 errors, {len(warnings)} advisory warning(s) ({spec_tag}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
