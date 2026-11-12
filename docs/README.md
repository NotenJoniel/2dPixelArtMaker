# docs/ — プロジェクト固有のアート設定集格納フォルダ

このフォルダには、`../templates/` 内のテンプレートファイルをコピー（`.template` を除去）し、**現在開発するゲーム固有の確定仕様**を記述して保存します。

---

## 推奨構成

```text
docs/
├── README.md                          # 本ファイル
├── 01_art_direction_and_world.md      # [必須] 世界観・視点・解像度・頭身・光源の定義
├── 02_color_palette_spec.md           # [必須] マスターパレット・カラーランプ設計
├── 03_character_list.md               # キャラクター・モンスターの一覧台帳
├── 06_item_ui_vfx_spec.md             # アイテム・UI・エフェクトの仕様定義
├── characters/                        # 個別キャラクター・モンスター仕様書
│   └── chr_001_hero.md                # (templates/04_character_detail_spec.template.md から作成)
└── environments/                      # ステージ・バイオーム別環境仕様書
    └── env_01_forest.md               # (templates/05_environment_tileset_spec.template.md から作成)
```

## 運用ルール

1. アセットの描画コードを書く前に、必ず対象アセットの仕様をここに記載・確定させます。
2. 制作途中でキャンバスサイズやパレット色、パーツ分割構成を変更した場合は、コードと合わせて `docs/` 側の仕様書も最新状態に更新し、仕様と実データの乖離を防ぎます。
