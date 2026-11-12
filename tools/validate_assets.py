#!/usr/bin/env python3
"""
validate_assets.py — assets/ 配下の納品データ品質検証（リンター）スクリプト

検査項目 (guidelines/07_qa_checklist.md 準拠):
1. ファイル・フォルダ命名規則 (小文字 snake_case)
2. PNG画像のアルファ二値性 (Alpha 0 または 255 のみ、明示許可時を除く)
3. クロマキー予約色 (#FF00FF) の抜き残しゼロ
4. マスターパレット準拠チェック (--palette 指定時または meta.json 内 palette 参照時)
5. パーツ分割メタデータ (*_meta.json) のファイル存在・キャンバスサイズ一致・親子循環参照・ピボット範囲
6. スプライトシート定義 (*.json) の画像サイズ・フレーム範囲整合性
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image

from pixel_canvas import Palette, parse_hex_color

SNAKE_CASE_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)?$")
IGNORED_FILES = {".gitkeep", "README.md"}
REQUIRED_PHASE1_DOCS: tuple[str, ...] = (
    "docs/01_art_direction_and_world.md",
    "docs/02_color_palette_spec.md",
    "docs/03_character_list.md",
)


class Validator:
    def __init__(
        self,
        root_dir: Path,
        default_palette: Palette | None = None,
        chroma_hex: str = "#FF00FF",
        allow_semitransparent: bool = False,
        skip_docs_check: bool = False,
    ) -> None:
        self.root_dir = root_dir
        self.default_palette = default_palette
        self.chroma_rgb = parse_hex_color(chroma_hex)[:3]
        self.allow_semitransparent = allow_semitransparent
        self.skip_docs_check = skip_docs_check
        self.errors: list[str] = []
        self.checked_pngs = 0
        self.checked_jsons = 0

    def err(self, path: Path, msg: str) -> None:
        rel = path.relative_to(self.root_dir) if path.is_relative_to(self.root_dir) else path
        self.errors.append(f"{rel}: {msg}")

    def check_naming(self, path: Path) -> None:
        if path.name in IGNORED_FILES:
            return
        if not SNAKE_CASE_RE.match(path.name):
            self.err(path, f"Naming violation '{path.name}' (must be lowercase snake_case).")

    def check_png(
        self,
        png_path: Path,
        *,
        palette: Palette | None = None,
        semitransparent_ok: bool = False,
    ) -> None:
        self.checked_pngs += 1
        try:
            img = Image.open(png_path).convert("RGBA")
        except Exception as exc:
            self.err(png_path, f"Failed to read PNG: {exc}")
            return

        pal = palette or self.default_palette
        allowed_rgbs = pal.allowed_rgb_set() if pal else None
        px = img.load()
        w, h = img.size

        semi_count = 0
        chroma_count = 0
        off_palette_samples: set[str] = set()

        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                if a != 255 and not (self.allow_semitransparent or semitransparent_ok):
                    semi_count += 1
                if (r, g, b) == self.chroma_rgb:
                    chroma_count += 1
                if allowed_rgbs is not None and (r, g, b) not in allowed_rgbs:
                    if len(off_palette_samples) < 5:
                        off_palette_samples.add(f"#{r:02X}{g:02X}{b:02X}")

        if semi_count > 0:
            self.err(png_path, f"Found {semi_count} semi-transparent pixel(s) (Alpha must be 0 or 255).")
        if chroma_count > 0:
            self.err(png_path, f"Found {chroma_count} unremoved chroma-key pixel(s) (#FF00FF).")
        if off_palette_samples:
            sample_str = ", ".join(sorted(off_palette_samples))
            self.err(png_path, f"Contains color(s) outside master palette (e.g. {sample_str}).")

    def check_rig_meta(self, meta_path: Path, data: dict) -> None:
        base_dir = meta_path.parent
        cw, ch = data.get("canvas_size", [0, 0])
        if cw <= 0 or ch <= 0:
            self.err(meta_path, f"Invalid canvas_size: {data.get('canvas_size')}")
            return

        if "origin" in data:
            ox, oy = data["origin"]
            if not (0 <= ox <= cw and 0 <= oy <= ch):
                self.err(meta_path, f"origin {data['origin']} is outside canvas_size {[cw, ch]}.")

        part_mode = data.get("part_mode", "canvas_aligned")
        parts = data.get("parts", [])
        part_ids = {p.get("id") for p in parts if "id" in p}
        parent_map: dict[str, str | None] = {}

        for p in parts:
            pid = p.get("id", "<missing_id>")
            parent = p.get("parent")
            parent_map[pid] = parent
            if parent is not None and parent not in part_ids:
                self.err(meta_path, f"Part '{pid}' references unknown parent '{parent}'.")

            files_to_check = [("base", p.get("file", ""))]
            for vk, vf in p.get("variants", {}).items():
                files_to_check.append((f"variant:{vk}", vf))

            for label, rel_f in files_to_check:
                fp = base_dir / rel_f
                if not rel_f or not fp.exists():
                    self.err(meta_path, f"Part '{pid}' ({label}) missing image file '{rel_f}'.")
                    continue
                if part_mode == "canvas_aligned":
                    with Image.open(fp) as im:
                        if list(im.size) != [cw, ch]:
                            self.err(
                                meta_path,
                                f"Part '{pid}' ({label}) size {list(im.size)} != canvas_size {[cw, ch]} in canvas_aligned mode.",
                            )

            piv = p.get("pivot")
            if piv is not None and part_mode == "canvas_aligned":
                if not (0 <= piv[0] <= cw and 0 <= piv[1] <= ch):
                    self.err(meta_path, f"Part '{pid}' pivot {piv} is outside canvas_size {[cw, ch]}.")

        # 親子関係の循環参照チェック
        for pid in part_ids:
            visited: set[str] = set()
            cur: str | None = pid
            while cur is not None:
                if cur in visited:
                    self.err(meta_path, f"Cycle detected in part parent hierarchy starting at '{pid}'.")
                    break
                visited.add(cur)
                cur = parent_map.get(cur)

    def check_spritesheet_meta(self, meta_path: Path, data: dict) -> None:
        img_rel = data.get("image")
        if not img_rel:
            self.err(meta_path, "Spritesheet JSON missing 'image' field.")
            return
        img_path = meta_path.parent / img_rel
        if not img_path.exists():
            self.err(meta_path, f"Spritesheet image not found: '{img_rel}'.")
            return

        with Image.open(img_path) as im:
            sheet_rgba = im.convert("RGBA")
            actual_size = list(sheet_rgba.size)

        declared_size = data.get("sheet_size")
        if declared_size != actual_size:
            self.err(meta_path, f"sheet_size {declared_size} != actual image size {actual_size}.")

        cw, ch = data.get("cell_size", [0, 0])
        pad = int(data.get("padding", 0))
        if cw <= 0 or ch <= 0:
            self.err(meta_path, f"Invalid cell_size: {data.get('cell_size')}")
            return

        is_character = ("characters" in meta_path.parts) or meta_path.name.startswith("chr_")

        for anim_name, anim in data.get("animations", {}).items():
            row = int(anim.get("row", 0))
            start_col = int(anim.get("start_col", 0))
            frames = int(anim.get("frames", 0))
            if frames <= 0:
                self.err(meta_path, f"Animation '{anim_name}' must have frames >= 1.")
                continue
            req_w = (start_col + frames) * cw + max(0, start_col + frames - 1) * pad
            req_h = (row + 1) * ch + max(0, row) * pad
            if req_w > actual_size[0] or req_h > actual_size[1]:
                self.err(
                    meta_path,
                    f"Animation '{anim_name}' exceeds sheet bounds ({req_w}x{req_h} > {actual_size[0]}x{actual_size[1]}).",
                )
                continue

            if frames >= 2:
                cell_bytes: list[bytes] = []
                for idx in range(frames):
                    col = start_col + idx
                    x0 = col * (cw + pad)
                    y0 = row * (ch + pad)
                    cell_bytes.append(sheet_rgba.crop((x0, y0, x0 + cw, y0 + ch)).tobytes())

                if len(set(cell_bytes)) == 1:
                    self.err(
                        meta_path,
                        f"Animation '{anim_name}' has {frames} frames, but all frames are pixel-identical (no motion).",
                    )
                elif (
                    is_character
                    and anim_name.startswith(("walk", "run"))
                    and frames >= 4
                    and frames % 2 == 0
                    and cell_bytes[: frames // 2] == cell_bytes[frames // 2 :]
                ):
                    self.err(
                        meta_path,
                        f"Animation '{anim_name}' repeats a 2-frame cycle twice (frame 0==2 & frame 1==3: one-legged hop). "
                        f"Alternate left/right foot stride between frame 0 and frame 2 (see: py tools/character_blueprints.py --walk sfc_16x24 right).",
                    )

    def _check_phase1_docs(self) -> None:
        if self.skip_docs_check or (self.checked_pngs == 0 and self.checked_jsons == 0):
            return
        proj_root = self.root_dir.resolve().parent
        docs_dir = proj_root / "docs"
        if not docs_dir.is_dir():
            return
        missing: list[str] = []
        for rel_doc in REQUIRED_PHASE1_DOCS:
            dp = proj_root / rel_doc
            if not dp.is_file() or dp.stat().st_size < 80:
                missing.append(rel_doc)
        if missing:
            self.errors.insert(
                0,
                f"Phase 1 spec gate violation: create specification docs BEFORE generating assets (missing/incomplete: {', '.join(missing)}).",
            )

    def run(self) -> int:
        if not self.root_dir.exists():
            print(f"[ERROR] Target directory does not exist: {self.root_dir}", file=sys.stderr)
            return 1

        palettes_dir = self.root_dir / "palettes" if (self.root_dir / "palettes").exists() else self.root_dir.parent / "palettes"

        for path in sorted(self.root_dir.rglob("*")):
            self.check_naming(path)
            if path.is_dir():
                continue
            # palettes/ 内のパレット定義ファイル自体はアセット検証から除外
            if "palettes" in path.parts and path.suffix.lower() in {".json", ".hex", ".gpl"}:
                continue

            if path.suffix.lower() == ".png":
                is_vfx = "vfx" in path.parts
                self.check_png(path, semitransparent_ok=is_vfx)
            elif path.suffix.lower() == ".json":
                self.checked_jsons += 1
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception as exc:
                    self.err(path, f"Invalid JSON syntax: {exc}")
                    continue

                if "parts" in data and "canvas_size" in data:
                    self.check_rig_meta(path, data)
                    if "palette" in data and self.default_palette is None:
                        pal_candidate = self.root_dir / data["palette"]
                        if not pal_candidate.exists() and palettes_dir.exists():
                            pal_candidate = palettes_dir / Path(data["palette"]).name
                        if pal_candidate.exists():
                            pal_obj = Palette.from_file(pal_candidate)
                            for part in data.get("parts", []):
                                fp = path.parent / part.get("file", "")
                                if fp.exists():
                                    self.check_png(fp, palette=pal_obj)
                                    self.checked_pngs -= 1
                elif "animations" in data and "cell_size" in data:
                    self.check_spritesheet_meta(path, data)

        self._check_phase1_docs()

        if self.errors:
            print(f"[FAIL] Found {len(self.errors)} validation error(s) in '{self.root_dir}':")
            for e in self.errors:
                print(f"  - {e}")
            return 1

        print(
            f"[PASS] Asset validation succeeded for '{self.root_dir}' "
            f"({self.checked_pngs} PNGs, {self.checked_jsons} JSONs checked, 0 errors)."
        )
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate game-ready 1x pixel art assets and metadata.")
    parser.add_argument("target", nargs="?", type=Path, default=Path("assets"), help="Target directory to validate (default: assets)")
    parser.add_argument("--palette", type=Path, help="Master palette (.json or .hex) to enforce across all PNGs")
    parser.add_argument("--allow-semitransparent", action="store_true", help="Allow semi-transparent alpha globally")
    parser.add_argument("--skip-docs-check", action="store_true", help="Skip Phase 1 docs/01..03 existence check")
    args = parser.parse_args()

    pal = Palette.from_file(args.palette) if args.palette else None
    validator = Validator(
        root_dir=args.target,
        default_palette=pal,
        allow_semitransparent=args.allow_semitransparent,
        skip_docs_check=args.skip_docs_check,
    )
    return validator.run()


if __name__ == "__main__":
    sys.exit(main())
