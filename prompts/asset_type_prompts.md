# アセット種別 AI制作依頼プロンプト集

人間がAIエージェントに対して初期ヒアリング、設定集の作成、コードによるピクセルアート制作を依頼する際の定型プロンプト集です。

---

## 0. 新規プロジェクトを対話アンケートから始める（一番簡単な開始方法）

```text
新しい2Dゲーム用のピクセルアート制作を始めたいです。
`AGENTS.md` の Phase 0 に従い、必須項目と任意項目に分けて初期ヒアリング（アンケート）を実施してください。
回答後に `docs/00_project_brief.md` を作成し、続けて `docs/01_art_direction_and_world.md` と `docs/02_color_palette_spec.md`（および `assets/palettes/master_palette.json`）の提案まで進めてください。
```

---

## 1. 記入済みの `docs/00_project_brief.md` から詳細設定集を展開させる

```text
`docs/00_project_brief.md` に初期方針を記入しました。
内容を読み取り、「おまかせ（空欄）」の任意項目には最適な技術仕様を補完した上で、`templates/` をもとに `docs/01_art_direction_and_world.md`、`docs/02_color_palette_spec.md`（および `assets/palettes/master_palette.json`）、`docs/03_character_list.md` を作成してください。
```

---

## 2. パーツ分割キャラクター（顔・体・手・足）をコード描画させる

```text
`guidelines/`（特に `02_pixel_art_fundamentals.md` と `04_part_separation_and_rig.md`）および `docs/` の共通仕様に従い、キャラクター `[例: chr_001_hero]` を制作してください。

1. まず `docs/characters/[chr_001_hero].md` が未作成なら `templates/04_character_detail_spec.template.md` をもとに仕様を作成してください。
   - モチーフ・特徴: [例: 青い旅装束に赤いスカーフ、茶髪のツンツン頭、片手剣を装備]
2. `workspace/01_raw/[chr_001_hero]/gen_[chr_001_hero].py` に `tools/pixel_canvas.py` を使った描画スクリプトを実装してください。
   - 単純な四角・楕円の組み合わせにせず、シルエットの抑揚・色相シフトした3階調シェーディング・L字ジャギーのない1pxアウトラインを徹底してください。
   - 関節（首・肩・肘・股・膝・足首）には回転しても隙間が空かない円形のりしろを持たせ、奥側の腕・脚（`_r`）は手前側より少し暗めのトーンで奥行きを出してください。
   - 目の差分（`normal`, `blink`, `angry`, `damage`）も一緒に出力してください。
3. `tools/preview_rig_composite.py` で8倍拡大プレビュー（通常合成＋ピボット表示＋パーツ展開シート）を `workspace/03_preview/` に生成し、必ず画像を視覚確認してバランスの違和感やジャギーを手直ししてください。
4. 完成データを `assets/characters/[chr_001_hero]/` に出力し、`tools/validate_assets.py` で検証してください。
```

---

## 3. キャラクターのアニメーション＆スプライトシートを生成させる

```text
`assets/characters/[chr_001_hero]/` のパーツ構造（および `workspace/01_raw/[chr_001_hero]/` の描画コード）をベースに、`guidelines/05_animation_and_spritesheet.md` に従って以下のアニメーションを作成し、スプライトシートとして書き出してください。

- 作成するステート: `[idle (4f), walk (6f), attack_01 (5f)]`
- 注意点:
  - 接地ライン（`origin`）がブレないようにし、歩行の上下動やスカーフ・髪の1フレーム遅れ追従（フォロースルー）を入れてください。
  - 攻撃モーションには1フレームの溜め（予備動作）と、振り抜き時の白い斬撃残像（スメア）を入れてください。
- `workspace/03_preview/` に全フレームを並べた拡大確認シートを出力して視覚チェックした上で、`tools/pack_spritesheet.py` 形式で `assets/characters/[chr_001_hero]/spritesheets/` に格納し、`validate_assets.py` を実行してください。
```

---

## 4. タイルセット・背景プロップをコード描画させる

```text
`docs/` の世界観・パレット仕様と `guidelines/` に従い、環境アセット `[例: env_01_forest]` を制作してください。

1. `docs/environments/[env_01_forest].md` に仕様を整理してください。
2. コード描画にて以下を作成してください：
   - 踏める地面タイルセット（`3x3` 基本ブロック＋内角4種、上下左右シームレス接続、上面エッジの視認性強調）
   - 背景プロップ: `[例: 木製宝箱(開閉2種)、壁掛け松明(4fアニメ)]`
3. 実際にタイルを敷き詰めたモックアップ画面（主人公サイズ比較付き）を `workspace/03_preview/` に出力して視認性を確認し、問題なければ `assets/environments/[env_01_forest]/` へ出力・検証してください。
```

---

## 5. アイテムアイコン・UIパーツを一括制作させる

```text
`docs/02_color_palette_spec.md` のパレットと `guidelines/` に従い、以下の `[16x16]` アイテムアイコンおよびUI枠をコード描画（記号ドットマップ活用）で作成してください。

- アイテム: `[例: itm_potion_red, itm_sword_iron, itm_shield_wood, itm_key_gold]`
  - 長物は45度対角線配置、1px濃色アウトライン＋ハイライトで小さくても何のアイテムか即座に判別できるようにしてください。
- UI: `[例: ui_window_main (24x24, 9スライス余白6px)]`
- 8倍拡大の一覧プレビューを `workspace/03_preview/` に出して視覚確認・微調整した後、`assets/items/` および `assets/ui/` に配置して `validate_assets.py` を通してください。
```
