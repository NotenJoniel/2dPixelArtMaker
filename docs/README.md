# docs/ — プロジェクト固有のアート設定集格納フォルダ

このフォルダには、`../templates/` をもとに作成する**現在開発するゲーム固有の初期方針・確定仕様書**を保存します。

---

## 推奨構成

```text
docs/
├── README.md                          # 本ファイル
├── 00_project_brief.md                # [最初に作成] 初期ヒアリングシート（必須5項目＋任意こだわり）
├── 01_art_direction_and_world.md      # [必須] 世界観・視点・解像度・頭身・光源の技術定義
├── 02_color_palette_spec.md           # [必須] マスターパレット・カラーランプ設計
├── 03_character_list.md               # キャラクター・モンスターの一覧台帳
├── 06_item_ui_vfx_spec.md             # アイテム・UI・エフェクトの仕様定義
├── characters/                        # 個別キャラクター・モンスター仕様書
│   └── chr_001_hero.md                # (templates/04_character_detail_spec.template.md から作成)
└── environments/                      # ステージ・バイオーム別環境仕様書
    └── env_01_forest.md               # (templates/05_environment_tileset_spec.template.md から作成)
```

## 立ち上げ手順

1. **まず `00_project_brief.md` から開始します**：
   - `../templates/00_project_brief.template.md` をコピーして必須5項目を埋めるか、AIに「新規プロジェクトの初期ヒアリングをして」と依頼して対話アンケートで作成します。
2. 続いて `00_project_brief.md` をもとに、AIと一緒に `01_art_direction_and_world.md` および `02_color_palette_spec.md` を確定させます。
3. 制作途中でキャンバスサイズやパレット色、パーツ分割構成を変更した場合は、コードと合わせて `docs/` 側の仕様書も最新状態に更新します。
