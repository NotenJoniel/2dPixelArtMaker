# tools/ — ドット絵コード描画・プレビュー・検証ツール群

本ディレクトリには、特定ゲームエンジンに依存しない2Dピクセルアートを **Python (`Pillow`) によるコード描画**で高品質かつ確実に制作・検証するためのコアライブラリとCLIスクリプトを格納しています。

> **実行コマンドの注意**: 環境により有効なPythonコマンドが異なります。`py`（Windows Python Launcher）→ `python3` → `python` の順で `Pillow (PIL)` がインポート可能なランタイムを確認して実行してください（例: `py -c "import PIL"` が使えないサンドボックス環境では `python3` や仮想環境の `python` を直接指定）。

---

## 収録ファイル一覧

| ファイル名 | 種別 | 役割 |
| :--- | :--- | :--- |
| `pixel_canvas.py` | Pythonライブラリ | 整数ピクセル描画コアAPI（行幅一致検査付き記号ドットマップ、ブレゼンハム線分、対称楕円、塗り漏れピンホールなしの整数多角形、方向性シェーディング、関節抜き対応1pxアウトライン、拡大プレビュー生成） |
| `character_blueprints.py` | ライブラリ / CLI | **AI再現性の核**: サイズ規格×テイスト×サイズ区分（`S/M/L/XL`）×役割ランク（`hero/party/mob/enemy/midboss/boss`）の定量仕様と、**装備・髪なしのクリーン素体マネキン（`--mannequin`）・武器なし標準素体（`--show`）・分離済み装備オーバーレイ（`--equipped`）**を提供する |
| `lint_character_style.py` | CLIツール | **造形品質リンター（キャラ・モンスター・S/M/L/XL対応）**: **内部の透過ピンホール（前髪と顔の境界隙間・塗り漏れ穴）**・実寸逸脱・接地ラインずれ・首伸び・左右対称きのこ頭・兜や帽子の水平一直線バンド・内部黒横線・色数超過を自動検出する |
| `preview_sheet.py` | CLIツール | **多角的プレビュー＆サイズ対比生成**: スプライトシートから拡大グリッド・黒塗りシルエット・4地形（草/土/石/暗所）視認性モック・アニメGIF、および全キャラ＆ボスの共通接地 `scale_lineup_4x.png` を一括出力する |
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

### サイズ規格 × テイスト × サイズ区分(S/M/L/XL) × 役割ランク別の仕様・素体マップ確認
```powershell
py tools/character_blueprints.py --list
py tools/character_blueprints.py --info sfc_16x24 retro_classic --scale M --role hero
py tools/character_blueprints.py --mannequin sfc_16x24 down --role mob
py tools/character_blueprints.py --show sfc_16x24 cool down
py tools/character_blueprints.py --show sfc_16x24 cool down --equipped
py tools/character_blueprints.py --verify
```

### キャラクター＆モンスターの造形スタイル・サイズ区分・接地ライン検査
```powershell
# 主人公・仲間キャラ (Mサイズ)
py tools/lint_character_style.py assets/characters/chr_001_hero/chr_001_hero_base.png --size sfc_16x24 --taste retro_classic --role hero --check-ground --strict

# 小型モンスター(S) / 大型ボス(XL)
py tools/lint_character_style.py assets/monsters/mon_001_slime/mon_001_slime_base.png --category monster --size sfc_16x24 --taste retro_classic --scale S --check-ground
py tools/lint_character_style.py assets/monsters/mon_101_dragon/mon_101_dragon_base.png --category monster --size sfc_16x24 --taste dark_serious --scale XL --role boss --check-ground
```

### スプライトシート拡大・シルエット・4地形モック・アニメGIF・全体サイズ対比シート生成
```powershell
py tools/preview_sheet.py --sheet assets/characters/chr_001_hero/spritesheets/chr_001_hero_sheet.json --out-dir workspace/03_preview
py tools/preview_sheet.py --lineup assets --out-dir workspace/03_preview
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
