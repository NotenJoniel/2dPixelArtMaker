#!/usr/bin/env python3
"""
pixel_canvas.py — コードによる2Dピクセルアート描画コアライブラリ

特徴:
- 完全な整数ピクセルグリッド描画（アンチエイリアス・半透明にじみゼロ）
- セマンティックパレット (.json / .hex) 対応
- 記号ドットマップ (ASCII Pixel Map) 描画
- ブレゼンハム線分（L字ジャギー除去オプション付き）・対称楕円・スキャンライン多角形
- 関節のりしろ部分の主線省略に対応した4近傍1pxアウトライン自動生成
- チェッカーボード背景・グリッド・ピボットマーカー付き拡大プレビュー出力
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Iterable, Mapping, Sequence, Union

from PIL import Image, ImageDraw

RGBA = tuple[int, int, int, int]
ColorSpec = Union[str, Sequence[int], None]
TRANSPARENT: RGBA = (0, 0, 0, 0)


def parse_hex_color(hex_str: str) -> RGBA:
    """'#RRGGBB' または '#RRGGBBAA' または 'RRGGBB' を RGBA タプルに変換する。"""
    s = hex_str.strip().lstrip("#")
    if len(s) == 6:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
    if len(s) == 8:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16))
    raise ValueError(f"Invalid hex color format: {hex_str!r}")


class Palette:
    """名前付きカラーキーおよびHEXリストを管理するパレットクラス。"""

    def __init__(
        self,
        colors: Mapping[str, Union[str, Sequence[int]]] | None = None,
        ramps: Mapping[str, Sequence[str]] | None = None,
        chroma_key: str | None = "#FF00FF",
    ) -> None:
        self.colors: dict[str, RGBA] = {}
        self.ramps: dict[str, list[str]] = {k: list(v) for k, v in (ramps or {}).items()}
        self.chroma_rgba: RGBA | None = parse_hex_color(chroma_key) if chroma_key else None

        if colors:
            for key, val in colors.items():
                self.colors[key] = self._coerce_rgba(val)

    @staticmethod
    def _coerce_rgba(val: Union[str, Sequence[int]]) -> RGBA:
        if isinstance(val, str):
            return parse_hex_color(val)
        if len(val) == 3:
            return (int(val[0]), int(val[1]), int(val[2]), 255)
        if len(val) == 4:
            return (int(val[0]), int(val[1]), int(val[2]), int(val[3]))
        raise ValueError(f"Unsupported color specification: {val!r}")

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Palette":
        p = Path(path)
        if p.suffix.lower() == ".json":
            data = json.loads(p.read_text(encoding="utf-8"))
            return cls(
                colors=data.get("colors", {}),
                ramps=data.get("ramps", {}),
                chroma_key=data.get("transparent_chroma", "#FF00FF"),
            )
        if p.suffix.lower() == ".hex":
            colors: dict[str, str] = {}
            idx = 0
            for raw_line in p.read_text(encoding="utf-8").splitlines():
                line = raw_line.split(";")[0].split("//")[0].strip()
                if not line:
                    continue
                colors[f"c_{idx:03d}"] = line
                idx += 1
            return cls(colors=colors)
        raise ValueError(f"Unsupported palette file extension: {p.suffix}")

    def resolve(self, color: ColorSpec) -> RGBA:
        if color is None or color == "" or color == ".":
            return TRANSPARENT
        if isinstance(color, str):
            if color in self.colors:
                return self.colors[color]
            return parse_hex_color(color)
        return self._coerce_rgba(color)

    def allowed_rgb_set(self) -> set[tuple[int, int, int]]:
        return {(r, g, b) for (r, g, b, a) in self.colors.values() if a > 0}


class PixelCanvas:
    """等倍(1x)ピクセルアートをコードで組み立てるためのキャンバス。"""

    def __init__(self, width: int, height: int, palette: Palette | None = None) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Canvas width and height must be positive integers.")
        self.width = int(width)
        self.height = int(height)
        self.palette = palette or Palette()
        self.image = Image.new("RGBA", (self.width, self.height), TRANSPARENT)
        self._px = self.image.load()

    def clone(self) -> "PixelCanvas":
        c = PixelCanvas(self.width, self.height, self.palette)
        c.image = self.image.copy()
        c._px = c.image.load()
        return c

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_px(self, x: int, y: int) -> RGBA:
        if not self.in_bounds(x, y):
            return TRANSPARENT
        return self._px[x, y]

    def set_px(
        self,
        x: int,
        y: int,
        color: ColorSpec,
        *,
        only_empty: bool = False,
        only_opaque: bool = False,
    ) -> None:
        ix, iy = int(x), int(y)
        if not self.in_bounds(ix, iy):
            return
        cur_a = self._px[ix, iy][3]
        if only_empty and cur_a != 0:
            return
        if only_opaque and cur_a == 0:
            return
        self._px[ix, iy] = self.palette.resolve(color)

    # ------------------------------------------------------------------
    # 1. 記号ドットマップ描画 (ASCII / Symbol Grid)
    # ------------------------------------------------------------------
    def draw_ascii_map(
        self,
        x: int,
        y: int,
        ascii_grid: str,
        symbol_map: Mapping[str, ColorSpec],
        *,
        transparent_chars: str = ". ",
    ) -> None:
        """複数行の文字列グリッドを座標 (x, y) を左上として描画する。"""
        dedented = textwrap.dedent(ascii_grid)
        lines = dedented.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        resolved_map = {ch: self.palette.resolve(col) for ch, col in symbol_map.items()}
        for dy, row in enumerate(lines):
            for dx, ch in enumerate(row):
                if ch in transparent_chars:
                    continue
                if ch not in resolved_map:
                    raise KeyError(f"Symbol {ch!r} at ({dx}, {dy}) not found in symbol_map.")
                px_x, px_y = x + dx, y + dy
                if self.in_bounds(px_x, px_y):
                    self._px[px_x, px_y] = resolved_map[ch]

    # ------------------------------------------------------------------
    # 2. 基本整数プリミティブ描画 (アンチエイリアスなし)
    # ------------------------------------------------------------------
    def draw_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: ColorSpec,
        *,
        pixel_perfect: bool = False,
    ) -> list[tuple[int, int]]:
        """ブレゼンハムの整数アルゴリズムで線分を描画する。"""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        pts: list[tuple[int, int]] = []
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        cx, cy = x0, y0

        while True:
            pts.append((cx, cy))
            if cx == x1 and cy == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                cx += sx
            if e2 <= dx:
                err += dx
                cy += sy

        if pixel_perfect and len(pts) >= 3:
            pts = self._filter_l_corners(pts)

        rgba = self.palette.resolve(color)
        for px, py in pts:
            if self.in_bounds(px, py):
                self._px[px, py] = rgba
        return pts

    @staticmethod
    def _filter_l_corners(pts: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
        """1px曲線のL字二重角 (Doubles) を除去してピクセルパーフェクト化する。"""
        out: list[tuple[int, int]] = []
        i = 0
        n = len(pts)
        while i < n:
            if 0 < i < n - 1:
                px, py = out[-1]
                cx, cy = pts[i]
                nx, ny = pts[i + 1]
                if (abs(cx - px) + abs(cy - py) == 1) and (abs(nx - cx) + abs(ny - cy) == 1):
                    if abs(nx - px) == 1 and abs(ny - py) == 1:
                        i += 1
                        continue
            out.append(pts[i])
            i += 1
        return out

    def draw_rect(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        fill: ColorSpec = None,
        outline: ColorSpec = None,
    ) -> None:
        if w <= 0 or h <= 0:
            return
        x0, y0 = int(x), int(y)
        x1, y1 = x0 + int(w) - 1, y0 + int(h) - 1
        if fill is not None:
            fill_rgba = self.palette.resolve(fill)
            for py in range(y0, y1 + 1):
                for px in range(x0, x1 + 1):
                    if self.in_bounds(px, py):
                        self._px[px, py] = fill_rgba
        if outline is not None:
            out_rgba = self.palette.resolve(outline)
            for px in range(x0, x1 + 1):
                if self.in_bounds(px, y0):
                    self._px[px, y0] = out_rgba
                if self.in_bounds(px, y1):
                    self._px[px, y1] = out_rgba
            for py in range(y0, y1 + 1):
                if self.in_bounds(x0, py):
                    self._px[x0, py] = out_rgba
                if self.in_bounds(x1, py):
                    self._px[x1, py] = out_rgba

    def draw_ellipse(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        fill: ColorSpec = None,
        outline: ColorSpec = None,
    ) -> None:
        """左右・上下対称な整数ピクセル楕円を描画する（関節の丸みのりしろ等にも有効）。"""
        if rx <= 0 or ry <= 0:
            return
        min_x = int(cx - rx - 1)
        max_x = int(cx + rx + 1)
        min_y = int(cy - ry - 1)
        max_y = int(cy + ry + 1)

        inside: set[tuple[int, int]] = set()
        # rx, ry >= 2 の場合に上下左右端の1px突起（スパイク）を防ぐドット絵補正項
        pole_smooth = (1.0 / (rx * ry)) if (rx >= 2 and ry >= 2) else 0.0
        threshold = 1.0 + pole_smooth
        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                nx = (px - cx) / rx
                ny = (py - cy) / ry
                if nx * nx + ny * ny <= threshold:
                    inside.add((px, py))

        if fill is not None:
            fill_rgba = self.palette.resolve(fill)
            for px, py in inside:
                if self.in_bounds(px, py):
                    self._px[px, py] = fill_rgba

        if outline is not None:
            out_rgba = self.palette.resolve(outline)
            for px, py in inside:
                if any((px + dx, py + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    if self.in_bounds(px, py):
                        self._px[px, py] = out_rgba

    def draw_circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: ColorSpec = None,
        outline: ColorSpec = None,
    ) -> None:
        self.draw_ellipse(cx, cy, r, r, fill=fill, outline=outline)

    def draw_polygon(
        self,
        points: Sequence[tuple[float, float]],
        fill: ColorSpec = None,
        outline: ColorSpec = None,
    ) -> None:
        """スキャンライン法によるアンチエイリアスなしの多角形塗りつぶし。"""
        if len(points) < 3:
            return
        if fill is not None:
            fill_rgba = self.palette.resolve(fill)
            ys = [p[1] for p in points]
            min_y = max(0, int(min(ys)))
            max_y = min(self.height - 1, int(max(ys)))
            n = len(points)
            for py in range(min_y, max_y + 1):
                scan_y = py + 0.5
                xs: list[float] = []
                for i in range(n):
                    x1, y1 = points[i]
                    x2, y2 = points[(i + 1) % n]
                    if (y1 <= scan_y < y2) or (y2 <= scan_y < y1):
                        t = (scan_y - y1) / (y2 - y1)
                        xs.append(x1 + t * (x2 - x1))
                xs.sort()
                for i in range(0, len(xs) - 1, 2):
                    start_x = max(0, int(round(xs[i])))
                    end_x = min(self.width - 1, int(round(xs[i + 1])) - 1)
                    for px in range(start_x, end_x + 1):
                        self._px[px, py] = fill_rgba

        if outline is not None:
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]
                self.draw_line(round(p1[0]), round(p1[1]), round(p2[0]), round(p2[1]), outline)

    def flood_fill(self, x: int, y: int, color: ColorSpec) -> None:
        """4近傍フラッドフィル（バケツ塗り）。"""
        sx, sy = int(x), int(y)
        if not self.in_bounds(sx, sy):
            return
        target = self._px[sx, sy]
        replacement = self.palette.resolve(color)
        if target == replacement:
            return
        stack = [(sx, sy)]
        while stack:
            cx, cy = stack.pop()
            if not self.in_bounds(cx, cy) or self._px[cx, cy] != target:
                continue
            self._px[cx, cy] = replacement
            stack.extend(((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)))

    # ------------------------------------------------------------------
    # 3. ドット絵専用シェーディング＆アウトライン補助
    # ------------------------------------------------------------------
    def apply_directional_shading(
        self,
        target_color: ColorSpec,
        highlight_color: ColorSpec | None = None,
        shadow_color: ColorSpec | None = None,
        light_dir: tuple[int, int] = (-1, -1),
    ) -> None:
        """
        target_color で塗られた領域のエッジに対し、光源方向側にハイライト、
        反対側に1pxの影を自動付与する（ピローシェーディング防止用）。
        """
        target_rgba = self.palette.resolve(target_color)
        hl_rgba = self.palette.resolve(highlight_color) if highlight_color else None
        sh_rgba = self.palette.resolve(shadow_color) if shadow_color else None
        lx, ly = light_dir

        region = {
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self._px[x, y] == target_rgba
        }
        for x, y in region:
            if hl_rgba and (x + lx, y + ly) not in region:
                self._px[x, y] = hl_rgba
            elif sh_rgba and (x - lx, y - ly) not in region:
                self._px[x, y] = sh_rgba

    def apply_outline(
        self,
        color: ColorSpec = "outline_dark",
        *,
        inside: bool = False,
        omit_boxes: Sequence[tuple[int, int, int, int]] | None = None,
    ) -> None:
        """
        不透明ピクセルの周囲（4近傍）に1pxアウトラインを付与する。
        - inside=False (デフォルト): 不透明領域の1px外側の透明ピクセルに主線を引く（L字二重角になりにくい）。
        - inside=True: 不透明領域の最外周1pxを主線色に置き換える。
        - omit_boxes: [(x0, y0, x1, y1), ...] で指定した矩形内（関節の重なり部など）は主線を省略する。
        """
        out_rgba = self.palette.resolve(color)
        boxes = list(omit_boxes or [])

        def is_omitted(px: int, py: int) -> bool:
            return any(bx0 <= px <= bx1 and by0 <= py <= by1 for bx0, by0, bx1, by1 in boxes)

        opaque = {
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self._px[x, y][3] > 0
        }

        targets: list[tuple[int, int]] = []
        if not inside:
            for y in range(self.height):
                for x in range(self.width):
                    if (x, y) in opaque or is_omitted(x, y):
                        continue
                    if any((x + dx, y + dy) in opaque for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        targets.append((x, y))
        else:
            for x, y in opaque:
                if is_omitted(x, y):
                    continue
                if any((x + dx, y + dy) not in opaque for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    targets.append((x, y))

        for x, y in targets:
            self._px[x, y] = out_rgba

    # ------------------------------------------------------------------
    # 4. 合成・変形・書き出し
    # ------------------------------------------------------------------
    def blit(self, src: "PixelCanvas", offset_x: int = 0, offset_y: int = 0) -> None:
        """別の PixelCanvas をアルファ合成で重ねる。"""
        self.image.alpha_composite(src.image, dest=(int(offset_x), int(offset_y)))
        self._px = self.image.load()

    def flip_horizontal(self) -> "PixelCanvas":
        c = PixelCanvas(self.width, self.height, self.palette)
        c.image = self.image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        c._px = c.image.load()
        return c

    def save(self, path: Union[str, Path]) -> Path:
        """等倍(1x)透過PNGとして保存する。"""
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.image.save(out_path, format="PNG")
        return out_path

    def render_preview_image(
        self,
        *,
        scale: int = 8,
        checker: bool = True,
        grid: bool = False,
        pivots: Iterable[tuple[int, int]] | None = None,
        origin: tuple[int, int] | None = None,
    ) -> Image.Image:
        """確認用の整数倍拡大 Image を生成する（workspace/03_preview/ 用）。"""
        s = max(1, int(scale))
        pw, ph = self.width * s, self.height * s
        bg = Image.new("RGBA", (pw, ph), (42, 44, 52, 255))

        if checker:
            draw_bg = ImageDraw.Draw(bg)
            c1 = (54, 58, 68, 255)
            c2 = (38, 41, 49, 255)
            tile = max(s, s * 2)
            for y in range(0, ph, tile):
                for x in range(0, pw, tile):
                    col = c1 if ((x // tile) + (y // tile)) % 2 == 0 else c2
                    draw_bg.rectangle([x, y, x + tile - 1, y + tile - 1], fill=col)

        upscaled = self.image.resize((pw, ph), resample=Image.Resampling.NEAREST)
        bg.alpha_composite(upscaled)

        overlay_img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        overlay = ImageDraw.Draw(overlay_img)

        if grid and s >= 4:
            grid_col = (255, 255, 255, 38)
            for x in range(0, pw, s):
                overlay.line([(x, 0), (x, ph - 1)], fill=grid_col)
            for y in range(0, ph, s):
                overlay.line([(0, y), (pw - 1, y)], fill=grid_col)

        if origin is not None:
            ox, oy = int(origin[0] * s + s // 2), int(origin[1] * s + s // 2)
            overlay.line([(0, oy), (pw - 1, oy)], fill=(80, 220, 120, 170), width=1)
            overlay.ellipse([ox - 3, oy - 3, ox + 3, oy + 3], outline=(80, 255, 120, 255))

        if pivots:
            for px, py in pivots:
                cx, cy = int(px * s + s // 2), int(py * s + s // 2)
                overlay.line([(cx - 4, cy), (cx + 4, cy)], fill=(255, 60, 220, 255), width=1)
                overlay.line([(cx, cy - 4), (cx, cy + 4)], fill=(255, 60, 220, 255), width=1)

        bg.alpha_composite(overlay_img)
        return bg

    def save_preview(
        self,
        path: Union[str, Path],
        *,
        scale: int = 8,
        checker: bool = True,
        grid: bool = False,
        pivots: Iterable[tuple[int, int]] | None = None,
        origin: tuple[int, int] | None = None,
    ) -> Path:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img = self.render_preview_image(
            scale=scale, checker=checker, grid=grid, pivots=pivots, origin=origin
        )
        img.save(out_path, format="PNG")
        return out_path
