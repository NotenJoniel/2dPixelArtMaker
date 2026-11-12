# 06. 出力ファイル構成・命名規則・メタデータ仕様

本ドキュメントでは、ゲームエンジン側へのインポートや自動化スクリプト連携をスムーズに行うためのディレクトリ構造、ファイル命名規則、および汎用JSONメタデータのスキーマを定めます。

---

## 1. ディレクトリ責務と出力先のルール

```text
workspace/                 ← 制作途中・再生成用（ゲーム本体には含めない）
├── 01_raw/<asset_id>/     ← 描画スクリプト (gen_<asset_id>.py)、ASCII設計図、元ラフ
├── 02_work/<asset_id>/    ← 作業中の単体パーツ・フレームPNG、一時ファイル
└── 03_preview/            ← 4x/8x拡大確認用PNG、グリッド/ピボット可視化画像

assets/                    ← 最終納品物（すべて等倍1x・検証済み・ゲーム導入可能）
├── palettes/              ← パレット定義 (.json, .hex, _1x.png)
├── characters/<char_id>/  ← プレイヤー・NPC・人型キャラ
├── monsters/<mon_id>/     ← モンスター・ボス
├── environments/<env_id>/ ← タイルセット・遠景背景・マップ配置オブジェクト
├── items/                 ← アイテム・スキル・装備アイコン
├── ui/                    ← ウィンドウ枠・ゲージ・カーソル・UIパーツ
└── vfx/                   ← 攻撃軌跡・爆発・魔法などのエフェクトシート
```

> **鉄則**: `assets/` 配下には、`4x` や `8x` に拡大されたプレビュー画像、チェッカー背景焼き込み画像、`.py` スクリプトを一切置かないこと。

---

## 2. ファイル・ID命名規則

1. **使用可能文字**: 半角英小文字（`a-z`）、数字（`0-9`）、アンダースコア（`_`）のみ（`snake_case`）。スペース、ハイフン、大文字、日本語ファイル名は `assets/` 内では使用禁止。
2. **カテゴリ接頭辞（Asset ID Prefix）**:
   - `chr_` : キャラクター（例: `chr_001_hero`, `chr_002_merchant`）
   - `mon_` : モンスター（例: `mon_001_slime`, `mon_010_dragon_boss`）
   - `env_` : 環境・ステージ（例: `env_01_forest`, `env_02_dungeon`）
   - `prp_` : マップ配置プロップ（例: `prp_chest_wood`, `prp_torch_wall`）
   - `itm_` : アイテムアイコン（例: `itm_potion_red`, `itm_sword_iron`）
   - `ui_`  : UI要素（例: `ui_window_frame_main`, `ui_hp_bar`）
   - `vfx_` : エフェクト（例: `vfx_slash_light`, `vfx_hit_spark`）
3. **連番のゼロ埋め**: ID連番は3桁（`001`）または2桁（`01`）、アニメーションフレーム連番は2桁ゼロ埋め（`_00`, `_01`, `_02`）に統一する。

---

## 3. カテゴリ別の `assets/` 内部ファイル構成例

### 3.1 パーツ分割キャラクターの例（`assets/characters/chr_001_hero/`）
```text
assets/characters/chr_001_hero/
├── chr_001_hero_meta.json                # リグ階層・Z順・ピボット・差分定義メタデータ
├── chr_001_hero_base.png                 # デフォルト立ち絵の1枚統合等倍PNG（一覧・サムネイル用）
├── parts/                                # 個別パーツPNG群
│   ├── chr_001_hero_hair_back.png
│   ├── chr_001_hero_head_base.png
│   ├── chr_001_hero_eyes_normal.png
│   ├── chr_001_hero_eyes_blink.png
│   ├── chr_001_hero_mouth_closed.png
│   ├── chr_001_hero_hair_front.png
│   ├── chr_001_hero_torso_lower.png
│   ├── chr_001_hero_torso_upper.png
│   ├── chr_001_hero_arm_upper_l.png
│   ├── chr_001_hero_arm_lower_l.png
│   ├── chr_001_hero_hand_l.png
│   └── ...
├── spritesheets/                         # ベイク済みアニメシートが必要な場合
│   ├── chr_001_hero_sheet.png
│   └── chr_001_hero_sheet.json
└── portraits/                            # 会話ウィンドウ用顔グラが必要な場合
    ├── chr_001_hero_portrait_normal.png
    └── chr_001_hero_portrait_smile.png
```

### 3.2 環境・タイルセットの例（`assets/environments/env_01_forest/`）
```text
assets/environments/env_01_forest/
├── tilesets/
│   ├── env_01_forest_ground_tiles.png    # 地形タイルセット画像
│   └── env_01_forest_ground_tiles.json   # タイルサイズ・当たり判定属性等の定義
├── backgrounds/
│   ├── env_01_forest_bg_00_sky.png       # 最遠景（固定または極低速スクロール）
│   ├── env_01_forest_bg_01_far.png       # 遠景の木々
│   └── env_01_forest_bg_02_mid.png       # 中景の木々
└── props/
    ├── prp_forest_tree_large.png
    └── prp_forest_signpost.png
```

---

## 4. 汎用メタデータJSONスキーマ仕様

特定ゲームエンジンに依存せず、どの言語・エンジンでも数十行のインポータで読み込めるJSON形式を採用します。座標系はすべて **画像左上を `(0, 0)` とするピクセル座標（Xは右プラス、Yは下プラス）** で統一します。

### 4.1 キャラクター・パーツリグ定義（`<asset_id>_meta.json`）

```json
{
  "schema_version": "1.0",
  "asset_id": "chr_001_hero",
  "category": "character",
  "canvas_size": [64, 64],
  "tile_unit_px": 16,
  "default_facing": "right",
  "part_mode": "canvas_aligned",
  "palette": "palettes/master_palette.json",
  "origin": [32, 60],
  "parts": [
    {
      "id": "torso_lower",
      "file": "parts/chr_001_hero_torso_lower.png",
      "parent": null,
      "z_index": 35,
      "offset": [0, 0],
      "pivot": [32, 42],
      "variants": {}
    },
    {
      "id": "torso_upper",
      "file": "parts/chr_001_hero_torso_upper.png",
      "parent": "torso_lower",
      "z_index": 50,
      "offset": [0, 0],
      "pivot": [32, 38],
      "variants": {}
    },
    {
      "id": "head_base",
      "file": "parts/chr_001_hero_head_base.png",
      "parent": "torso_upper",
      "z_index": 60,
      "offset": [0, 0],
      "pivot": [32, 26],
      "variants": {}
    },
    {
      "id": "eyes",
      "file": "parts/chr_001_hero_eyes_normal.png",
      "parent": "head_base",
      "z_index": 68,
      "offset": [0, 0],
      "pivot": [34, 20],
      "variants": {
        "blink": "parts/chr_001_hero_eyes_blink.png",
        "angry": "parts/chr_001_hero_eyes_angry.png"
      }
    }
  ],
  "presets": {
    "default": {},
    "blink": {
      "eyes": "blink"
    },
    "angry": {
      "eyes": "angry"
    }
  }
}
```

#### フィールド定義
- `canvas_size`: `[width, height]` — キャラクター全体の基準キャンバスサイズ（px）。
- `tile_unit_px`: プロジェクトの1ユニット（1タイル）あたりのピクセル数（例: `16` または `32`）。エンジンの PPU（Pixels Per Unit）設定にそのまま対応する。
- `origin`: `[x, y]` — ゲーム内でのキャラクター足元接地基準点（当たり判定や座標基準の原点）。
- `part_mode`: `"canvas_aligned"`（全パーツが `canvas_size` と同サイズで `offset: [0, 0]`）または `"trimmed"`（余白切り抜き済みで `offset` に配置左上座標を持つ）。
- `parts[].z_index`: 昇順描画（小さい値が奥、大きい値が手前）。
- `parts[].pivot`: 回転軸となる関節座標 `[x, y]`（`canvas_aligned` の場合はキャンバス座標系、`trimmed` の場合はパーツ画像内ローカル座標系）。
- `parts[].variants`: 表情や手・装備の差し替えファイル辞書（相対パスは `<asset_id>_meta.json` のあるフォルダ基準）。

---

### 4.2 スプライトシート定義（`<sheet_name>.json`）

```json
{
  "schema_version": "1.0",
  "asset_id": "chr_001_hero",
  "image": "chr_001_hero_sheet.png",
  "sheet_size": [384, 192],
  "cell_size": [64, 64],
  "origin": [32, 60],
  "padding": 0,
  "animations": {
    "idle": {
      "row": 0,
      "start_col": 0,
      "frames": 4,
      "fps": 6,
      "loop": true
    },
    "walk": {
      "row": 1,
      "start_col": 0,
      "frames": 6,
      "fps": 10,
      "loop": true
    },
    "attack_01": {
      "row": 2,
      "start_col": 0,
      "frames": 5,
      "fps": 12,
      "loop": false
    }
  }
}
```

### 4.3 9スライスUI枠定義（`assets/ui/<ui_id>.json`、任意）
ウィンドウ枠などの伸縮UIパーツには、`slice_margins`（左・右・上・下の非伸縮固定ピクセル幅）を記録します：
```json
{
  "schema_version": "1.0",
  "asset_id": "ui_window_frame_main",
  "image": "ui_window_frame_main.png",
  "size": [24, 24],
  "slice_9_margins": { "left": 6, "right": 6, "top": 6, "bottom": 6 }
}
```
