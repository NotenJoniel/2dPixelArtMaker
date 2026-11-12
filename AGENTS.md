# AGENTS.md — AIエージェント行動指針（2Dピクセルアート標準制作環境）

このリポジトリで作業するAIエージェントは、どのAIモデルであっても毎回一貫した日本式2Dゲームのピクセルアート品質を再現できるよう、初期ヒアリング・仕様策定・コード描画・品質検証のすべてにおいて必ず本ドキュメントの原則と手順に従ってください。

---

## 1. 基本方針・最優先原則（Golden Rules）

1. **特定エンジンに依存しない汎用出力**
   - 最終出力は**等倍（1x）の透過PNG（RGBA）**と、標準化された**汎用JSONメタデータ**（パーツ階層・ピボット座標・Z順・アニメーション定義）で構成する。特定エンジン固有のバイナリや独自形式にロックインさせない。
2. **「素体ブループリント起点のコード描画」＋「自動スタイル検査＆視覚フィードバック」による再現性保証**
   - アセット生成の基本手法は、Pythonスクリプト（`tools/pixel_canvas.py` 等）による**プログラマティックなピクセル描画**とする。
   - **白紙からの目分量描画の禁止（最重要）**: 人型キャラクターを描く際は、いきなり空のキャンバスに目分量で矩形やASCIIマップを書いてはならない。必ず `tools/character_blueprints.py`（`py tools/character_blueprints.py --info <size> <taste>` / `--show <size> <taste> <dir>`）から該当する**サイズ規格×テイストの検証済み素体（頭:体:足のピクセル配分・コア胴体幅・目配置）**を参照してベース構造を継承すること。
   - **日本式2Dキャラ造形5原則の徹底**:
     1. 髪型は左右対称のお椀・きのこ型を禁止し、斜め分けや外ハネ毛束で非対称なシルエットを作る。
     2. デフォルメ頭身（`2頭身`・`2.5頭身`）では**絶対に細い首（縦の隙間）を描かず**、顎の下端ラインを肩・襟の上端へ `0px` 直結させる（首表現は `high_32x56` 等の `5頭身` のみ）。
     3. 胴体のコア幅は頭幅の約半分（`sfc_16x24` で `6〜8px`）に絞ってくびれさせ、寸胴な箱型化を防ぐ。
     4. 短い胴体を水平な黒線で輪切りにせず、V字襟・斜めベルト・Aラインマント等で動きを出し、内部境界は同系色の暗色シェード（色トレス／Sel-Out）で繋ぐ。
     5. 頬の横余白を最小（1px）に抑え、目のすぐ外側にもみあげを添えて小顔にまとめる。
   - 描画後は必ず **① `tools/lint_character_style.py` による数値・造形スタイル検査** と **② `workspace/03_preview/` の拡大プレビュー画像の `read_file` によるAI自身の目視確認（最低1回以上の改善イテレーション）** の両方を実施すること。
3. **初期ヒアリング（サイズ規格 × テイスト選択）なき生成の禁止**
   - `docs/01_art_direction_and_world.md` および `docs/02_color_palette_spec.md` が未作成の状態で、いきなりアセットを描画してはならない。
   - プロジェクト開始時は必ず **Phase 0（初期方針決定）** から開始し、`docs/00_project_brief.md` を読み取るか、必須項目（視点・世界観・**サイズ規格**・**デザインテイスト**・分割方針・初回スコープ）と任意項目を分けたアンケートを実施すること。
4. **`workspace/` と `assets/` の厳格な分離**
   - 描画スクリプト（`gen_*.py`）は `workspace/01_raw/` に保存し、途中画像は `workspace/02_work/`、確認用の整数倍拡大画像は `workspace/03_preview/` に出力する。
   - `assets/` には、**検収を通過した等倍（1x）PNGと汎用メタデータJSONのみ**を配置する。

---

## 2. 作業開始時の必読ガイドライン順序

タスクに応じて、作業前に以下の `guidelines/` を必ず読み込むこと。

| 作業内容 | 必読ガイドライン |
| :--- | :--- |
| 全体フロー・新規プロジェクト開始 | `guidelines/00_workflow_overview.md`, `guidelines/01_worldbuilding_and_style.md` |
| パレット設計・配色決定 | `guidelines/03_color_and_palette.md` |
| コードによるドット描画・素体活用 | `guidelines/02_pixel_art_fundamentals.md`, `guidelines/06_output_structure_and_naming.md` |
| キャラクターのパーツ分割（顔・体・手・足等） | `guidelines/04_part_separation_and_rig.md` |
| アニメーション・スプライトシート作成 | `guidelines/05_animation_and_spritesheet.md` |
| 最終出力・スタイルリンター・検収 | `guidelines/07_qa_checklist.md` |

---

## 3. 標準制作ワークフロー（AI実行手順）

### Phase 0: 初期方針ヒアリング（Kickoff Brief）
1. `docs/00_project_brief.md` の有無と記入状態を確認する。
2. **未作成または必須項目が未記入の場合**:
   - `templates/00_project_brief.template.md` に従い、以下の **【必須6項目】** と **【任意項目（空欄＝AIおまかせ可）】** をアンケート（`ask_question` 等）で確認し、`docs/00_project_brief.md` を作成・保存する：
     1. **ジャンル・カメラ視点**（横視点 / 見下ろし3/4［4方向］ / クォータービュー / 正面一枚絵）
     2. **世界観・モチーフ**
     3. **サイズ・世代規格（`size_preset`）**: `fc_16x16`（ファミコン風） / `sfc_16x24`（スーファミ王道JRPG風・推奨） / `hd2d_18x32`（モダンHD-2D風） / `high_32x56`（ハイレゾ5頭身風）
     4. **デザインテイスト・雰囲気（`taste_preset`）**: `cute`（かわいい系） / `cool`（かっこいい系） / `retro_classic`（レトロ王道系） / `dark_serious`（ダーク・シリアス系）
     5. **パーツ分割・アニメ方針**（サイズ規格に応じた推奨方式を提示）
     6. **初回制作スコープ**

### Phase 1: 詳細仕様書への展開・定義（`docs/`）
1. `docs/00_project_brief.md` と `tools/character_blueprints.py` の定量仕様をもとに、`templates/` から以下を作成する：
   - `docs/01_art_direction_and_world.md`（確定した `size_preset`・`taste_preset`・画面解像度・タイルpx・主線・光源等）
   - `docs/02_color_palette_spec.md` および `assets/palettes/master_palette.json`
   - 対象アセットの台帳・個別仕様書（例: `docs/03_character_list.md`, `docs/characters/chr_001_hero.md`）

### Phase 2: 素体ブループリントに基づくコード描画（`workspace/01_raw/` → `workspace/02_work/`）
1. キャラクター制作時は最初に `py tools/character_blueprints.py --info <size_preset> <taste_preset>` および `--show <size_preset> <taste_preset> down` を実行し、基準素体のピクセル寸法と行構造を確認する。
2. `workspace/01_raw/<asset_id>/gen_<asset_id>.py` を作成し、`tools/pixel_canvas.py`（行幅不一致の自動検出機能付き `draw_ascii_map` や3パス構築）を用いて描画する。
3. トップダウン3/4見下ろしRPGの歩行キャラは、原則として **4方向（`down`, `up`, `right`, `left`）** を揃えて設計する。

### Phase 3: 自動スタイル検査と拡大プレビュー視覚セルフレビュー（`workspace/03_preview/`）
1. `py tools/lint_character_style.py <output.png> --size <size_preset> --taste <taste_preset>` を実行し、実身長逸脱・横幅肥大・首伸び・左右完全対称のきのこ頭・内部黒横線・色数超過がないことを確認する。
2. `workspace/03_preview/` に8倍拡大プレビューを出力し、**必ず `read_file` で画像を視覚確認する**。違和感があればスクリプトを修正して再生成する。

### Phase 4: `assets/` への配置とフォーマット自動検証
1. 完成した等倍PNG群・スプライトシート・メタデータJSONを `assets/` の所定パスへ出力する。
2. `py tools/validate_assets.py assets --palette assets/palettes/master_palette.json` を実行し、全チェックがパスすることを確認する。

---

## 4. コマンド実行時の注意

- Windows環境では `python` がストア誘導エイリアスになっている場合があるため、`py` ランチャー（例: `py tools/validate_assets.py`）または環境で有効な `python3` を使用すること。
