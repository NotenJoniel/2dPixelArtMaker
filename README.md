# 2dPixelArtMaker — 2Dピクセルアート作成用 標準プロジェクト

AIによる**コードベースのピクセル描画（プログラマティック・ピクセルアート生成）**を主軸として、特定ゲームエンジンに依存しない汎用2Dピクセルアート（ドット絵）アセットを一貫した世界観・規格・品質で制作するための**標準プロジェクト**です。

AIに無秩序にドット絵コードを書かせると発生しがちな「単調な矩形・楕円だけのチープな描画（プログラマーアート化）」「モデルごとの頭身・デザイン品質のバラつき」「既存有名ゲームIPキャラへの意図しない酷似」「パーツ回転時の関節の隙間」を防ぐため、**選択式のサイズ規格（FC風 / SFC風 / HD-2D風 / 5頭身風）× デザインテイスト（かわいい系 / かっこいい系等）・検証済み素体ブループリント（`tools/character_blueprints.py`）・造形スタイル自動リンター（`tools/lint_character_style.py`）・既存IP非酷似オリジナリティ規約** を組み込み、どのAIモデルが使っても毎回安定した日本式2Dゲームのオリジナルクオリティを再現できる構造にしています。

---

## ディレクトリ構成

```text
2dPixelArtMaker/
├── README.md                  # 本ドキュメント（プロジェクト概要・利用手順）
├── AGENTS.md                  # AIエージェント向けの行動指針・コード描画ワークフロー定義
├── guidelines/                # [規約] 世界観設計・ドット絵技術・配色・パーツ分割・アニメ・出力仕様
├── templates/                 # [雛形] 初期ヒアリングシート(00)および詳細仕様書(01〜06)のテンプレート
├── docs/                      # [設定集] 当該ゲームの初期方針および確定仕様書の格納先
├── prompts/                   # [指示雛形] AIへ制作を依頼する際のプロンプトテンプレート集
├── workspace/                 # [作業用] 描画スクリプト(01_raw)・途中画像(02_work)・拡大確認(03_preview)
├── assets/                    # [納品用] エンジン非依存の等倍(1x)PNG ＋ 汎用メタデータJSON
└── tools/                     # [ツール] ドット描画コアAPI・パーツ合成確認・シート結合・品質検証ツール
```

---

## 新規ゲーム向けアセット制作の進め方（クイックスタート）

### Step 0: 初期方針＆制作キャラリストの決定（おまかせ派・こだわり派の両対応）
最初から細かいピクセル数やパレットコードを悩む必要はありません。以下のスタイルに合わせてスタートできます。

- **方法A（チャット対話で手軽に始める・おまかせ派）**：AIに「新しいプロジェクトを始めたいのでヒアリングして」と話しかけます。AIが必須6項目（視点・世界観・**サイズ規格**・**デザインテイスト**・分割方針・**作りたいキャラ＆敵の人数セット**）を選択式アンケートで確認し、`docs/00_project_brief.md` を自動作成します。「味方2人・街モブ1人・小型ザコ2体・大型ボス1体をおまかせで」といった人数指定も可能です。
- **方法B（専用設定ファイルで細かく指定して始める・こだわり派）**：
  1. `templates/00_project_brief.template.md` を `docs/00_project_brief.md` にコピーして必須項目にチェックを入れます。
  2. さらに `templates/00_roster_spec.template.md` を **`docs/00_roster_spec.md`** にコピーし、作りたい**主人公・仲間・モブNPC・ザコ敵・中ボス・大ボスの名前、役割ランク（`hero / party / mob / enemy / midboss / boss`）、サイズ区分（小型 `S` / 普通 `M` / 大型 `L` / 特大 `XL`）、外見モチーフ**を記入してAIに読み込ませます（一部の列だけ空欄＝AIおまかせにすることも可能です）。

### Step 1: 詳細設定集（`docs/`）への展開
`docs/00_project_brief.md` の内容をもとに、AIが `templates/` から専門的な仕様書を自動設計して `docs/` に出力します。
1. `docs/01_art_direction_and_world.md` — 画面解像度・基準タイルサイズ・頭身・主線・共通光源の確定
2. `docs/02_color_palette_spec.md` — カラーランプ設計（実体JSONは `assets/palettes/` へ配置）
3. `docs/03_character_list.md` / `docs/characters/<char_id>.md` — キャラ一覧と個別パーツ分割仕様

### Step 2: コードによるピクセル描画・パーツ分割・目視確認（`workspace/`）
1. AIは `docs/` の仕様に基づき、`tools/pixel_canvas.py` を用いた描画スクリプトを `workspace/01_raw/` に作成し、パーツ・フレーム画像を `workspace/02_work/` に出力します。
2. `tools/preview_rig_composite.py` 等で4倍〜8倍の拡大プレビュー（グリッド線・透過チェッカー背景・ピボット位置表示付き）を `workspace/03_preview/` に出力し、AIおよび人間が目視確認してディテールを磨き込みます。

### Step 3: 品質検証と最終出力（`assets/`）
`guidelines/07_qa_checklist.md` の基準を満たした等倍（1x）PNGと汎用JSONメタデータを `assets/` 配下に配置し、`tools/validate_assets.py` でサイズ・アルファ境界・パレット準拠・命名規則・リグ整合性を検証します。

---

## 補助ツールの実行環境

`tools/` 配下のスクリプト・ライブラリは **Python 3.10+** および **Pillow (`PIL`)** のみで動作します（特定ゲームエンジンへの依存はありません）。

```powershell
# Windows (Python Launcher 利用時)
py tools/validate_assets.py --help

# macOS / Linux / py ランチャー非搭載のサンドボックス環境
python3 tools/validate_assets.py --help
python tools/validate_assets.py --help
```

各スクリプトや描画API（`pixel_canvas.py`）の使い方は `tools/README.md` を参照してください。
