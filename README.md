# 2dPixelArtMaker — 2Dピクセルアート作成用 標準プロジェクト

AIによる**コードベースのピクセル描画（プログラマティック・ピクセルアート生成）**を主軸として、特定ゲームエンジンに依存しない汎用2Dピクセルアート（ドット絵）アセットを一貫した世界観・規格・品質で制作するための**標準プロジェクト**です。

AIに無秩序にドット絵コードを書かせると発生しがちな「単調な矩形・楕円だけのチープな描画（プログラマーアート化）」「キャラクターごとの頭身・光源・パレットの不統一」「パーツ回転時の関節の隙間」を防ぐため、**制作規約（`guidelines/`）・事前設定集（`templates/` → `docs/`）・描画支援ライブラリ＆検証ツール（`tools/`）・作業領域（`workspace/`）・最終納品データ（`assets/`）** を体系化しています。

---

## ディレクトリ構成

```text
2dPixelArtMaker/
├── README.md                  # 本ドキュメント（プロジェクト概要・利用手順）
├── AGENTS.md                  # AIエージェント向けの行動指針・コード描画ワークフロー定義
├── guidelines/                # [規約] 世界観設計・ドット絵技術・配色・パーツ分割・アニメ・出力仕様
├── templates/                 # [雛形] 制作開始前に記入する設定集・仕様書のテンプレート群
├── docs/                      # [設定集] templatesから複製して作成する当該ゲームの確定仕様
├── prompts/                   # [指示雛形] AIへアセット制作を依頼する際のプロンプトテンプレート集
├── workspace/                 # [作業用] 描画スクリプト(01_raw)・途中画像(02_work)・拡大確認(03_preview)
├── assets/                    # [納品用] エンジン非依存の等倍(1x)PNG ＋ 汎用メタデータJSON
└── tools/                     # [ツール] ドット描画コアAPI・パーツ合成確認・シート結合・品質検証ツール
```

---

## 新規ゲーム向けアセット制作の進め方（クイックスタート）

### Step 1: 規約の把握
`guidelines/00_workflow_overview.md` から順に制作ルールと出力仕様を確認します（AIエージェントに依頼する場合、`AGENTS.md` の指示に従いAIが自動で参照します）。

### Step 2: 事前設定集（`docs/`）の作成
ドット絵を描き始める前に、`templates/` 内のテンプレートを `docs/` にコピー（`.template` を除去）し、ゲームの視覚仕様を確定します。

1. `docs/01_art_direction_and_world.md` — 世界観・視点・基準タイルサイズ・頭身・主線・共通光源を確定
2. `docs/02_color_palette_spec.md` — マスターパレットと色相シフト方針を確定（パレット定義ファイルは `assets/palettes/` へ配置）
3. `docs/03_character_list.md` — 制作するキャラクター・モンスターの一覧とサイズ区分を整理
4. `docs/characters/<char_id>.md` — 個別キャラのモチーフ・配色・分割パーツ構成・必要アニメを定義
5. 必要に応じて環境（`05_environment_tileset_spec`）やアイテム・UI・VFX（`06_item_ui_vfx_spec`）の仕様書を作成

> `prompts/` 内の依頼テンプレートを使い、「〇〇風の2Dゲームを作りたいので、`templates/` をもとに `docs/` の初期設定案を作成して」とAIに指示するとスムーズに立ち上げられます。

### Step 3: コードによるピクセル描画・パーツ分割・目視確認（`workspace/`）
1. AIは `docs/` の仕様に基づき、`tools/pixel_canvas.py`（ドット描画支援ライブラリ：ASCIIドットマップ、ブレゼンハム線分、整数楕円、自動アウトライン、シェーディング補助等）を用いた描画スクリプトを `workspace/01_raw/` に作成します。
2. 生成されたパーツ単体・フレーム単体データを `workspace/02_work/` に出力します。
3. `tools/preview_rig_composite.py` 等で4倍〜8倍の拡大プレビュー（グリッド線・透過チェッカー背景・ピボット位置表示付き）を `workspace/03_preview/` に出力し、AIおよび人間が目視確認してディテールを磨き込みます。

### Step 4: 品質検証と最終出力（`assets/`）
`guidelines/07_qa_checklist.md` の基準を満たした等倍（1x）PNGと汎用JSONメタデータを `assets/` 配下に配置し、`tools/validate_assets.py` でサイズ・アルファ境界・パレット準拠・命名規則・リグ整合性を検証します。

---

## 補助ツールの実行環境

`tools/` 配下のスクリプト・ライブラリは **Python 3.10+** および **Pillow (`PIL`)** のみで動作します（特定ゲームエンジンへの依存はありません）。

```powershell
# Windows (Python Launcher 利用時)
py tools/validate_assets.py --help

# macOS / Linux / 標準 python コマンド環境
python3 tools/validate_assets.py --help
```

各スクリプトや描画API（`pixel_canvas.py`）の使い方は `tools/README.md` を参照してください。
