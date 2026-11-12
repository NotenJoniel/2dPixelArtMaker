# tools/ — ドット絵コード描画・プレビュー・検証ツール群

本ディレクトリには、特定ゲームエンジンに依存しない2Dピクセルアートを **Python (`Pillow`) によるコード描画**で高品質かつ確実に制作・検証するためのコアライブラリとCLIスクリプトを格納しています。

> **実行コマンドの注意**: Windows環境では `py tools/<script>.py`、macOS/Linux環境では `python3 tools/<script>.py` を使用してください。

---

## 収録ファイル一覧

| ファイル名 | 種別 | 役割 |
| :--- | :--- | :--- |
| `pixel_canvas.py` | Pythonライブラリ | 整数ピクセル描画コアAPI（行幅一致検査付き記号ドットマップ、ブレゼンハム線分、対称楕円、多角形、方向性シェーディング、関節抜き対応1pxアウトライン、拡大プレビュー生成） |
| `character_blueprints.py` | ライブラリ / CLI | **AI再現性の核**: サイズ規格（`fc_16x16`, `sfc_16x24`, `hd2d_18x32`, `high_32x56`）× テイスト（`cute`, `cool`, `retro_classic`, `dark_serious`）の定量ピクセル仕様と、検証済み4方向素体ASCIIマップを提供する |
| `lint_character_style.py` | CLIツール | **造形品質リンター**: 生成されたキャラクターPNGを解析し、実身長の間延び・横幅肥大・首なし規格での首伸び・左右完全対称のきのこ頭・内部の黒横線輪切り・色数超過を自動検出する |
| `preview_rig_composite.py` | CLIツール | `<asset_id>_meta.json` と分割パーツPNG群を読み込み、拡大合成ビュー・ピボット＆グリッド確認ビュー・個別パーツ一覧シートを1枚の画像として `workspace/03_preview/` に出力する |
| `pack_spritesheet.py` | CLIツール | アニメーションの連番フレームPNG群を等間隔グリッドの1枚のスプライトシートPNGに結合し、汎用フレーム定義JSONを同時出力する |
| `validate_assets.py` | CLIツール | `assets/` 配下のファイル命名規則（`snake_case`）、二値アルファ（半透明ゴミなし）、クロマキー残りなし、マスターパレット準拠、リグ／シートJSONの整合性を一括検証する |
| `quantize_and_snap.py` | CLI補助ツール | 外部ラフ画像などを取り込む際、等倍解像度への縮小・クロマキー背景透過・指定パレットへの減色を行う |

---

## 1. `pixel_canvas.py` を使ったコード描画の基本例

`workspace/01_raw/<asset_id>/gen_<asset_id>.py` からインポートして使用します。

```python
import sys
from pathlib import Path

# tools/ を import パスに追加
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from pixel_canvas import Palette, PixelCanvas

palette = Palette.from_file("assets/palettes/master_palette.json")
canvas = PixelCanvas(16, 16, palette)

# 記号ドットマップによる精密描画 ('.' は透明)
POTION_GRID = """
......KKKK......
.....KwwwwK.....
......KddK......
.....KnnnnK.....
...KKnWWWWnKK...
..KnWWrrrrrrnK..
.KnWrrrrrrrrrnK.
.KnWLLrrrrrrdnK.
KnWLLrrrrrrrrdnK
KnWLrrrrrrrrddnK
KnrrrrrrrrrrddnK
.KnrrrrrrrrddnK.
..KnddddddddnK..
...KKnnnnnnKK...
.....KKKKKK.....
"""

canvas.draw_ascii_map(0, 1, POTION_GRID, {
    "K": "outline_dark",
    "w": "wood_light",
    "d": "wood_shadow",
    "n": "neutral_base",
    "W": "white_pure",
    "L": "red_light",
    "r": "red_base",
})

# 1. 確認用 8x 拡大プレビューを workspace/03_preview/ に出力
canvas.save_preview("workspace/03_preview/itm_potion_red_8x.png", scale=8, grid=True)

# 2. ゲーム実装用 等倍(1x) PNG を assets/items/ に出力
canvas.save("assets/items/itm_potion_red.png")
```

---

## 2. 主なCLIコマンド使用例

### サイズ規格 × テイスト別の定量仕様・検証済み素体マップの確認
```powershell
py tools/character_blueprints.py --list
py tools/character_blueprints.py --info sfc_16x24 cool
py tools/character_blueprints.py --show sfc_16x24 cool down
```

### キャラクタードット絵のプロポーション・造形スタイル検査
```powershell
py tools/lint_character_style.py assets/characters/chr_001_hero/spritesheets/chr_001_hero_sheet.png --frame 32x32 --size sfc_16x24 --taste cool --strict
```

### 分割パーツの合成確認シート作成＋等倍ベース立ち絵保存
```powershell
py tools/preview_rig_composite.py assets/characters/chr_001_hero/chr_001_hero_meta.json --scale 8 --save-base
```

### スプライトシートの結合出力
```powershell
py tools/pack_spritesheet.py --frames-dir workspace/02_work/mon_001_slime/idle --asset-id mon_001_slime --anim-name idle --fps 6 --out assets/monsters/mon_001_slime/spritesheets/mon_001_slime_sheet.png
```

### 納品アセットの自動品質検証（QAチェック）
```powershell
py tools/validate_assets.py assets --palette assets/palettes/master_palette.json
```
