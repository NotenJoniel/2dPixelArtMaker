# アセット種別 AI制作依頼プロンプト集

人間がAIエージェント（どのAIモデルでも可）に対して初期ヒアリング、仕様策定、および再現性の高いピクセルアート制作を依頼する際の定型プロンプト集です。

---

## 0. 新規プロジェクトを対話アンケートから始める（おまかせ派・手軽スタート）

```text
新しい2Dゲーム用のピクセルアート制作を始めたいです。
`AGENTS.md` の Phase 0 に従い、必須6項目（視点、世界観、サイズ規格［FC風/SFC風/HD-2D風/5頭身風］、デザインテイスト、分割方針、および制作対象ロスターの人数・セット内訳）と任意項目に分けてアンケートを実施してください。
回答後に `docs/00_project_brief.md` を作成し、続けて `docs/01_art_direction_and_world.md`、`docs/02_color_palette_spec.md`（および `assets/palettes/master_palette.json`）、`docs/03_character_list.md` を提案してください。
```

---

## 1. 記入済みの `docs/00_project_brief.md`（＋任意で `docs/00_roster_spec.md`）から始める（こだわり指定派）

```text
`docs/00_project_brief.md`（および制作対象リスト `docs/00_roster_spec.md`）を記入しました。
記載した役割ランク（`hero` / `party` / `mob` / `enemy` / `midboss` / `boss`）とサイズ区分（`S` / `M` / `L` / `XL`）、および `tools/character_blueprints.py` の定量基準を読み取り、「おまかせ（空欄）」の項目には最適な仕様を補完した上で、詳細設定集（`docs/01〜03` および個別仕様書）を展開して初回制作対象の描画〜検収まで進めてください。
```

---

## 2. キャラクター（4方向立ち絵＋歩行スプライトシート）をコード描画させる【見下ろしRPG標準】

```text
`guidelines/`（特に `01_worldbuilding_and_style.md` と `02_pixel_art_fundamentals.md`）および `docs/` の共通仕様に従い、キャラクター `[例: chr_001_hero]`（役割: `[hero/party/mob]`、サイズ区分: `[M/L]`）を制作してください。

1. まず `py tools/character_blueprints.py --info [sfc_16x24] [retro_classic] --scale [M] --role [hero]` と `--show [sfc_16x24] [retro_classic] down`（および `up`, `right`, `left`）を実行し、検証済み素体のピクセル寸法・接地原点 `origin` を確認してください。
2. `docs/characters/[chr_001_hero].md` に仕様をまとめた上で、`workspace/01_raw/[chr_001_hero]/gen_[chr_001_hero].py` を実装し、4方向（`down`, `up`, `right`, `left`）の立ち絵と歩行アニメーションを生成してください。
   - 日本式2Dキャラ造形7原則（非対称毛束、首0px直結、コア胴体6〜8pxくびれ、2層重ね着と内部色トレス、16-bit主役の白目＋瞳、兜・帽子つばの水平一直線禁止、背負い剣等の斜め45度軸一致）を徹底してください。
   - 既存商用ゲームIPの特定キャラクターと「シルエット×配色×象徴モチーフ」が酷似しないよう、オリジナルデザインにしてください。
3. 出力画像に対して必ず `py tools/lint_character_style.py <base.png> --size [sfc_16x24] --taste [retro_classic] --scale [M] --role [hero] --check-ground --strict` を実行してエラー・警告 0 件を確認し、さらに `py tools/preview_sheet.py --sheet <sheet.json> --out-dir workspace/03_preview` の拡大・シルエット・4地形プレビュー画像を視覚確認して微調整してください。
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

## 5. モンスター・中ボス・大ボス（`S / M / L / XL`）を既存IP非酷似のオリジナル造形で制作させる

```text
`guidelines/01_worldbuilding_and_style.md`（特に「2.5 サイズ区分と役割ランク」および「4. 既存ゲームIPへの酷似禁止」）および `docs/` の仕様に従い、モンスター `[例: mon_001_slime (scale=S, role=enemy) / mon_101_dragon (scale=XL, role=boss)]` を制作してください。

1. `py tools/character_blueprints.py --info [sfc_16x24] [retro_classic] --scale [S/M/L/XL] --role [enemy/midboss/boss]` で該当サイズ区分のキャンバスサイズ・実寸範囲・標準接地原点 `origin`・色数上限を確認してください。
2. 一般名詞のモンスター（スライム、ゴブリン、ドラゴン等）であっても、既存有名タイトルの固有デザイン（水色しずく型スライム等）に絶対に酷似させないでください。「シルエット形状」「配色」「核・顔つきモチーフ」のうち最低2要素以上を独自設計し、`docs/characters/<id>.md` の「既存IP非酷似・オリジナリティ設計メモ」に明記してください。
3. `workspace/01_raw/<id>/gen_<id>.py` で `idle` と `attack_01` のアニメーションシートを描画し、`py tools/lint_character_style.py <base.png> --category monster --size [sfc_16x24] --taste [retro_classic] --scale [S/M/L/XL] --check-ground` をパスさせ、`py tools/preview_sheet.py --sheet <sheet.json> --lineup assets --out-dir workspace/03_preview` の拡大・4地形・サイズ対比シートを視覚確認した上で納品・検証してください。
```
