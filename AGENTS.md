# AGENTS.md — AIエージェント行動指針（2Dピクセルアート標準制作環境）

このリポジトリで作業するAIエージェントは、どのAIモデルであっても毎回一貫した日本式2Dゲームのピクセルアート品質を再現できるよう、初期ヒアリング・仕様策定・コード描画・品質検証のすべてにおいて必ず本ドキュメントの原則と手順に従ってください。

---

## 1. 基本方針・最優先原則（Golden Rules）

1. **特定エンジンに依存しない汎用出力**
   - 最終出力は**等倍（1x）の透過PNG（RGBA）**と、標準化された**汎用JSONメタデータ**（パーツ階層・ピボット座標・Z順・アニメーション定義）で構成する。特定エンジン固有のバイナリや独自形式にロックインさせない。
2. **「素体ブループリント起点のコード描画」＋「自動スタイル検査＆視覚フィードバック」による再現性保証**
   - アセット生成の基本手法は、Pythonスクリプト（`tools/pixel_canvas.py` 等）による**プログラマティックなピクセル描画**とする。
   - **白紙からの目分量描画の禁止（最重要）**: 人型キャラクターを描く際は、いきなり空のキャンバスに目分量で矩形やASCIIマップを書いてはならない。必ず `tools/character_blueprints.py`（`py tools/character_blueprints.py --info <size> <taste> --scale <S/M/L/XL> --role <role>` / `--show <size> <taste> <dir>`）から該当する**サイズ規格×テイスト×サイズ区分×役割ランクの検証済み素体・定量仕様**を参照してベース構造を継承すること。
   - **日本式2Dキャラ造形7原則の徹底**:
     1. 髪型は左右対称のお椀・きのこ型を禁止し、斜め分けや外ハネ毛束で非対称なシルエットを作る。
     2. デフォルメ頭身（`2頭身`・`2.5頭身`）では**絶対に細い首（縦の隙間）を描かず**、顎の下端ラインを肩・襟の上端へ `0px` 直結させる（首表現は `high_32x56` 等の `5頭身` のみ）。
     3. 胴体のコア幅は頭幅の約半分（`sfc_16x24` で `6〜8px`）に絞ってくびれさせ、寸胴な箱型化を防ぐ。
     4. 短い胴体を水平な黒線で輪切りにせず、V字襟・斜めベルト・肩ケープ等で**2層の重ね着感**を出し、内部境界は同系色の暗色シェード（色トレス／Sel-Out）で繋ぐ（単色1枚布のモブ化禁止）。
     5. 頬の横余白を最小（1px）に抑え、**16-bit以上の主役・仲間（`hero/party`）は `1×2` 黒棒目にせず必ず「白目1px＋瞳1px」で視線を作る**（逆に街人 `mob` はシンプルな黒目・控えめ色数に抑えて主役を引き立てる）。
     6. **兜の縁・帽子のつば・鉢巻を「真横の水平一直線」に引かない**（眉間1px食い込みV字ブリッジ・斜め被り・前髪の覗きを入れてヘルメット／三角コーン化を防ぐ）。
     7. **斜め武器・背負い剣の軸一致**: 背中に斜め45度（`/`）で背負う剣や杖の柄・鍔だけを垂直・水平（`⊥`）に折れ曲がらせず、刀身の斜め45度延長線上に柄を伸ばし、鍔は直交する逆45度で描く。
   - 描画後は必ず **① `tools/lint_character_style.py` による数値・造形スタイル検査（キャラ・モンスター・S/M/L/XL共通）** と **② `tools/preview_sheet.py` 等による `workspace/03_preview/` の拡大・4地形・サイズ対比画像の `read_file` 目視確認（最低1回以上の改善イテレーション）** の両方を実施すること。
3. **初期ヒアリング（サイズ規格 × テイスト選択）なき生成の禁止**
   - `docs/01_art_direction_and_world.md` および `docs/02_color_palette_spec.md` が未作成の状態で、いきなりアセットを描画してはならない。
   - プロジェクト開始時は必ず **Phase 0（初期方針決定）** から開始し、`docs/00_project_brief.md` を読み取るか、必須項目（視点・世界観・**サイズ規格**・**デザインテイスト**・分割方針・初回スコープ）と任意項目を分けたアンケートを実施すること。
4. **`workspace/` と `assets/` の厳格な分離**
   - 描画スクリプト（`gen_*.py`）は `workspace/01_raw/` に保存し、途中画像は `workspace/02_work/`、確認用の整数倍拡大画像は `workspace/03_preview/` に出力する。
   - `assets/` には、**検収を通過した等倍（1x）PNGと汎用メタデータJSONのみ**を配置する。
5. **既存ゲームIPキャラクターへの固有デザイン酷似の厳禁（オリジナリティ原則）**
   - 「ファミコン風」「スーファミJRPG風」等のハード世代テイストや頭身比率・技法を参照することは推奨するが、**既存の商用ゲーム作品に登場する特定キャラクターやモンスターと「形状（シルエット）× 配色 × 顔つき・象徴パーツ」の組み合わせが酷似するデザインを生成してはならない**。
   - 特にAIが無意識に再現しやすい著名アイコン（例：『ドラクエ』の「水色・玉ねぎしずく型・丸い白黒目・赤い笑顔口」のスライム、特定作品の看板マスコット、固有の帽子・兜・衣装配色の完全一致など）は厳禁とする。
   - 一般名詞のモンスターや職業（スライム、ゴブリン、剣士、魔法使い等）を描く際は、必ず**独自のシルエット・色・モチーフ（例：スライムなら不定形ドーム状＋内部に浮かぶ結晶コア＋別色にする等）**を設計し、一目で特定他社タイトルのキャラを連想させないオリジナルデザインにすること。

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

### Phase 0: 初期方針・制作ロスターヒアリング（Kickoff Brief & Roster）
1. `docs/00_project_brief.md` および（細かく指定したい人向けの専用設定ファイル）`docs/00_roster_spec.md` の有無を確認する。
2. **未作成または必須項目が未記入の場合**:
   - `templates/00_project_brief.template.md` に従い、以下の **【必須6項目】** と **【任意項目（空欄＝AIおまかせ可）】** をアンケート（`ask_question` 等）で確認し、`docs/00_project_brief.md` を作成・保存する：
     1. **ジャンル・カメラ視点**（横視点 / 見下ろし3/4［4方向］ / クォータービュー / 正面一枚絵）
     2. **世界観・モチーフ**
     3. **サイズ・世代規格（`size_preset`）**: `fc_16x16`（ファミコン風） / `sfc_16x24`（スーファミ王道JRPG風・推奨） / `hd2d_18x32`（モダンHD-2D風） / `high_32x56`（ハイレゾ5頭身風）
     4. **デザインテイスト・雰囲気（`taste_preset`）**: `cute`（かわいい系） / `cool`（かっこいい系） / `retro_classic`（レトロ王道系） / `dark_serious`（ダーク・シリアス系）
     5. **パーツ分割・アニメ方針**（サイズ規格に応じた推奨方式を提示）
     6. **制作対象ロスター（キャラ数・敵数・モブ／ボス・サイズ区分 `S/M/L/XL`）の指定方法**:
        - **おまかせ派**: 最小セット（主人公M＋小型ザコS）、基本RPGセット（主人公M＋仲間M＋街モブM＋ザコS＋大型ボスL/XL）、または「味方○体・モブ○体・ザコ○体・ボス○体（普通M／大型Lなど）」の人数内訳だけ聞いてAIが企画提案する。
        - **細かく指定したい派**: `templates/00_roster_spec.template.md` を `docs/00_roster_spec.md` にコピーしてユーザーに記入してもらう（または既に記入済みの `docs/00_roster_spec.md` を読み込む）。

### Phase 1: 詳細仕様書への展開・定義（`docs/`）
1. `docs/00_project_brief.md`（および `docs/00_roster_spec.md`）と `tools/character_blueprints.py` の定量仕様をもとに、`templates/` から以下を作成する：
   - `docs/01_art_direction_and_world.md`（確定した `size_preset`・`taste_preset`・`S/M/L/XL` サイズ区分基準・光源等）
   - `docs/02_color_palette_spec.md` および `assets/palettes/master_palette.json`
   - 対象アセットの台帳 `docs/03_character_list.md`（各アセットの `role`［`hero/party/mob/enemy/midboss/boss`］と `scale`［`S/M/L/XL`］を明記）および個別仕様書（`docs/characters/<id>.md`）

### Phase 2: 素体ブループリントに基づくコード描画（`workspace/01_raw/` → `workspace/02_work/`）
1. 制作時は最初に `py tools/character_blueprints.py --info <size_preset> <taste_preset> --scale <S/M/L/XL> --role <role>` および（人型Mの場合は）`--show <size_preset> <taste_preset> down` を実行し、キャンバス寸法・接地原点 `origin`・ピクセル配分を確認する。
2. `workspace/01_raw/<asset_id>/gen_<asset_id>.py` を作成し、`tools/pixel_canvas.py` を用いて描画する。
3. トップダウン3/4見下ろしRPGの歩行キャラは、原則として **4方向（`down`, `up`, `right`, `left`）** を同じ接地Y座標（`origin[1] - 1`）で揃えて設計する。

### Phase 3: 自動スタイル検査と拡大プレビュー視覚セルフレビュー（`workspace/03_preview/`）
1. `py tools/lint_character_style.py <output.png> --size <size_preset> --taste <taste_preset> --scale <S/M/L/XL> --role <role> --check-ground` を実行し、実寸逸脱・接地ズレ・首伸び・きのこ頭・水平一直線ヘルメット・内部黒横線・色数超過がないことを確認する。
2. `py tools/preview_sheet.py --sheet <sheet.json> --out-dir workspace/03_preview`（複数体制作時は `--lineup assets` も併用）で拡大グリッド・シルエット・4地形コントラスト・サイズ対比シートを出力し、**必ず `read_file` で画像を視覚確認する**。違和感があればスクリプトを修正して再生成する。

### Phase 4: `assets/` への配置とフォーマット自動検証
1. 完成した等倍PNG群・スプライトシート・メタデータJSONを `assets/` の所定パスへ出力する。
2. `py tools/validate_assets.py assets --palette assets/palettes/master_palette.json` を実行し、全チェックがパスすることを確認する。

---

## 4. コマンド実行時の注意

- Windows環境では `python` がストア誘導エイリアスになっている場合があるため、`py` ランチャー（例: `py tools/validate_assets.py`）または環境で有効な `python3` を使用すること。
