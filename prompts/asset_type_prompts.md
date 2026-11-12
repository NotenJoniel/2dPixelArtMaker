# アセット種別 AI制作依頼プロンプト集

人間がAIエージェント（どのAIモデルでも可）に対して初期ヒアリング、仕様策定、および再現性の高いピクセルアート制作を依頼する際の定型プロンプト集です。

---

## 0. 新規プロジェクトを対話アンケートから始める（一番簡単な開始方法）

```text
新しい2Dゲーム用のピクセルアート制作を始めたいです。
`AGENTS.md` の Phase 0 に従い、必須項目（視点、世界観、サイズ規格［FC風/SFC風/HD-2D風/5頭身風］、デザインテイスト［かわいい系/かっこいい系等］、分割方針、初回スコープ）と任意項目に分けてアンケートを実施してください。
回答後に `docs/00_project_brief.md` を作成し、続けて `docs/01_art_direction_and_world.md` と `docs/02_color_palette_spec.md`（および `assets/palettes/master_palette.json`）を提案してください。
```

---

## 1. 記入済みの `docs/00_project_brief.md` から詳細設定集を展開させる

```text
`docs/00_project_brief.md` に初期方針を記入しました。
内容と `tools/character_blueprints.py` の定量基準を読み取り、「おまかせ（空欄）」の任意項目には最適な技術仕様を補完した上で、`docs/01_art_direction_and_world.md`、`docs/02_color_palette_spec.md`（および `assets/palettes/master_palette.json`）、`docs/03_character_list.md` を作成してください。
```

---

## 2. キャラクター（4方向立ち絵＋歩行スプライトシート）をコード描画させる【見下ろしRPG標準】

```text
`guidelines/`（特に `01_worldbuilding_and_style.md` と `02_pixel_art_fundamentals.md`）および `docs/` の共通仕様に従い、キャラクター `[例: chr_001_hero]` を制作してください。

1. まず `py tools/character_blueprints.py --info [sfc_16x24] [cool]` と `--show [sfc_16x24] [cool] down`（および `up`, `right`, `left`）を実行し、検証済み素体のピクセル寸法（頭:体:足比率・コア胴体幅・目配置）を確認してください。白紙からの目分量描画は行わないでください。
2. `docs/characters/[chr_001_hero].md` に仕様をまとめた上で、`workspace/01_raw/[chr_001_hero]/gen_[chr_001_hero].py` を実装し、4方向（`down`, `up`, `right`, `left`）の立ち絵と歩行アニメーションを生成してください。
   - 日本式2Dキャラ造形5原則（非対称毛束、首0px直結、コア胴体6〜8pxくびれ、V字・斜めラインと内部色トレス、頬余白1pxの小顔）を徹底してください。
   - 既存商用ゲームIPの特定キャラクターと「シルエット×配色×象徴モチーフ」が酷似しないよう、オリジナルデザインにしてください。
3. 出力画像に対して必ず `py tools/lint_character_style.py <sheet.png> --frame [32x32] --size [sfc_16x24] --taste [cool] --strict` を実行してエラー・警告が 0 件であることを確認し、さらに `workspace/03_preview/` の拡大プレビュー画像を視覚確認して微調整してください。
4. 完成データを `assets/characters/[chr_001_hero]/` に出力し、`py tools/validate_assets.py assets --palette assets/palettes/master_palette.json` をパスさせてください。
```

---

## 3. 多関節ボーン分割キャラクター（`high_32x56` 等）をコード描画させる

```text
`guidelines/04_part_separation_and_rig.md` と `docs/` の仕様に従い、多関節パーツ分割キャラクター `[例: chr_001_knight]` を制作してください。

1. `py tools/character_blueprints.py --info high_32x56 cool` で縦比率と色数基準を確認し、`docs/characters/[chr_001_knight].md` にパーツ構成・Z順・ピボットを定義してください。
2. 各関節に回転しても隙間が空かない円形のりしろ（半径2〜4px）を確保し、連続部位の関節内アウトラインを省略して `workspace/02_work/[chr_001_knight]/parts/` に出力してください。
3. `py tools/preview_rig_composite.py` で8倍合成プレビューを `workspace/03_preview/` に生成し、`py tools/lint_character_style.py` と目視確認の両方をクリアした上で `assets/` へ納品・検証してください。
```

---

## 4. タイルセット・アイテムアイコン・UIパーツを制作させる

```text
`docs/02_color_palette_spec.md` のパレットと `guidelines/` に従い、以下のアセットを `tools/pixel_canvas.py`（行幅厳密チェック付き記号ドットマップ）で作成してください。

- 対象アセット: `[例: itm_potion_red (16x16), itm_sword_iron (16x16), env_01_grassland (16x16 3x3タイル)]`
- `workspace/03_preview/` に8〜12倍拡大プレビュー（キャラとのサイズ対比モック含む）を出力して視覚確認・改善したのち、`assets/` に配置して `py tools/validate_assets.py assets --palette assets/palettes/master_palette.json` を実行してください。
```

---

## 5. モンスター（敵キャラクター）を既存ゲームIP非酷似のオリジナル造形で制作させる

```text
`guidelines/01_worldbuilding_and_style.md`（特に「4. 既存ゲームIPへの酷似禁止とオリジナリティ設計ルール」）および `docs/` の仕様に従い、モンスター `[例: mon_001_slime]` を制作してください。

1. 一般名詞のモンスター（スライム、ゴブリン、ドラゴン等）であっても、既存有名タイトルの固有デザイン（例：水色・玉ねぎしずく型・丸目・赤い笑顔口のスライム等）に絶対に酷似させないでください。「シルエット形状」「配色」「核・顔つきモチーフ」のうち最低2要素以上を独自設計し、`docs/characters/[mon_001_slime].md` の「既存IP非酷似・オリジナリティ設計メモ」に明記してください。
2. `workspace/01_raw/[mon_001_slime]/gen_[mon_001_slime].py` で `idle` と `attack_01` のアニメーションシートを描画し、`workspace/03_preview/` の拡大プレビューを視覚確認・改善した上で `assets/monsters/[mon_001_slime]/` に出力・検証してください。
```
