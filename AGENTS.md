# AGENTS.md — AIエージェント行動指針（2Dピクセルアート標準制作環境）

このリポジトリで作業するAIエージェントは、どのAIモデルであっても毎回一貫した日本式2Dゲームのピクセルアート品質を再現できるよう、初期ヒアリング・仕様策定・コード描画・品質検証のすべてにおいて必ず本ドキュメントの原則と手順に従ってください。

---

## 1. 基本方針・最優先原則（Golden Rules）

1. **特定エンジンに依存しない汎用出力**
   - 最終出力は**等倍（1x）の透過PNG（RGBA）**と、標準化された**汎用JSONメタデータ**（パーツ階層・ピボット座標・Z順・アニメーション定義）で構成する。特定エンジン固有のバイナリや独自形式にロックインさせない。
2. **「素体ブループリント起点のコード描画」＋「自動スタイル検査＆視覚フィードバック」による再現性保証**
   - アセット生成の基本手法は、Pythonスクリプト（`tools/pixel_canvas.py` 等）による**プログラマティックなピクセル描画**とする。
   - **白紙からの目分量描画の禁止（最重要）**: キャラクターや大型ボスを描く際は、いきなり空のキャンバスに目分量で矩形やASCIIマップを書いてはならない。必ず `tools/character_blueprints.py`（`--info` / `--mannequin` / `--show` / `--walk`）から該当する**サイズ規格×テイスト×サイズ区分×役割ランクの検証済み素体・歩行サイクル・定量仕様**を参照してベース構造を継承すること。
     - **素体・歩行ブループリントの使い分け**:
       - 独自の髪型・帽子を起こすキャラや仲間（`party`）・街人（`mob`）には、武器・外ハネ髪・帽子を含まず頭部が肌色で塗られた **`--mannequin <size> <dir> --role <role>`（`get_mannequin()`）** をベースにする。
       - 大型（`L`）・特大ボス（`XL`）には、角兜・肩装甲・コア胴体・外套・分離籠手・グリーヴが構造分離された **`--mannequin <size> down --scale <L|XL> --role <midboss|boss>`** をベースにし、肩・胸・腕が単色の塊になるのを防ぐ。
       - テイスト別の髪・衣装完成例は `--show <size> <taste> <dir>`（デフォルト武器なし）、45度軸一致の背負い剣付き構造は `--equipped`、**SFC王道4フレーム歩行サイクル（直立横立ち＋交互踏み出し＋1px沈み）**は **`--walk <size> <dir>`（`get_walk_frames()`）** を参照する。
   - **日本式2Dキャラ造形7原則の徹底**:
     1. 髪型は左右対称のお椀・きのこ型を禁止し、斜め分けや外ハネ毛束で非対称なシルエットを作る。
     2. デフォルメ頭身（`2頭身`・`2.5頭身`）では**絶対に細い首（縦の隙間）を描かず**、顎の下端ラインを肩・襟の上端へ `0px` 直結させる（首表現は `high_32x56` 等の `5頭身` のみ）。
     3. 胴体のコア幅は頭幅の約半分（`sfc_16x24` で `6〜8px`）に絞ってくびれさせ、寸胴な箱型化を防ぐ。
     4. 短い胴体を水平な黒線で輪切りにせず、V字襟・斜めベルト・肩ケープ等で**2層の重ね着感**を出し、内部境界は同系色の暗色シェード（色トレス／Sel-Out）で繋ぐ（単色1枚布のモブ化禁止）。
     5. 頬の横余白を最小（1px）に抑え、**16-bit以上の主役・仲間（`hero/party`）は `1×2` 黒棒目にせず必ず「白目1px＋瞳1px」で視線を作る**。その際、**上下2行の白目・瞳のX座標を必ず垂直に一致させ**、ASCIIマップ編集時の1列ズレ（寄り目・斜視崩れ）を起こさないこと（街人 `mob` はシンプルな黒目・控えめ色数に抑える）。
     6. **兜の縁・帽子のつば・鉢巻を「真横の水平一直線」に引かない**（眉間1px食い込みV字ブリッジ・斜め被り・前髪の覗きを入れてヘルメット／三角コーン化を防ぐ）。
     7. **斜め武器・背負い剣の軸一致と密着**: 背中に斜め45度（`/`）で背負う剣や杖は、柄頭→鍔→鞘→石突まで単一の45度延長線上に揃え、肩・髪の外周に隙間なく密着させる（宙に浮かせたり柄だけ折れ曲がらせない）。
   - 描画後は必ず **① `tools/lint_character_style.py` による数値・造形スタイル検査（キャラ・モンスター・S/M/L/XL共通）** と **② `tools/preview_sheet.py` 等による `workspace/03_preview/` の拡大・4地形・サイズ対比画像の `read_file` 目視確認（最低1回以上の改善イテレーション）** の両方を実施すること。
3. **初期ヒアリングおよび「仕様書先行ゲート（Spec-Before-Code）」の厳守**
   - **`docs/01_art_direction_and_world.md`・`docs/02_color_palette_spec.md`・`docs/03_character_list.md`（および個別仕様 `docs/characters/<id>.md`）を作成する前に、`workspace/01_raw/` の描画スクリプトや画像ファイルを先に作成してはならない**（描画後に仕様書を後付けする順序逆転は厳禁。リンターおよびバリデータが `docs/01〜03` 未作成をエラーとしてブロックする）。
   - プロジェクト開始時は必ず **Phase 0（初期方針決定）→ Phase 1（仕様書・パレットJSON確定）→ Phase 2（コード描画）** の順を守ること。
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

### Phase 1: 詳細仕様書への展開・定義（`docs/` — **描画前の完了必須ゲート**）
1. **【順序厳守】`workspace/01_raw/` にコードを1行でも書く前に**、`docs/00_project_brief.md`（および `docs/00_roster_spec.md`）と `tools/character_blueprints.py` の定量仕様をもとに、`templates/` から以下を作成して保存する（未作成のまま描画に進むと `lint_character_style.py` / `validate_assets.py` がゲート違反エラーを出す）：
   - `docs/01_art_direction_and_world.md`（確定した `size_preset`・`taste_preset`・`S/M/L/XL` サイズ区分基準・光源等）
   - `docs/02_color_palette_spec.md` および `assets/palettes/master_palette.json`
   - 対象アセットの台帳 `docs/03_character_list.md`（各アセットの `role`［`hero/party/mob/enemy/midboss/boss`］と `scale`［`S/M/L/XL`］を明記）および個別仕様書（`docs/characters/<id>.md`）

### Phase 2: 素体・歩行ブループリントに基づくコード描画（`workspace/01_raw/` → `workspace/02_work/`）
1. 制作時は最初に `tools/character_blueprints.py --info <size_preset> <taste_preset> --scale <S/M/L/XL> --role <role>` を実行し、キャンバス寸法・接地原点 `origin`・ピクセル配分を確認する。
   - 標準 `M` キャラ: `--mannequin <size_preset> <dir> --role <role>`（髪・帽子・武器なし素体）または `--show <size_preset> <taste_preset> <dir>`（`--equipped` で45度背負い剣）を参照する。横向き立ち絵（`right`/`left`）は足を前後に大股開きさせず、**頭・胴・重なり脚が垂直に揃ったSFC直立横顔ポーズ**にする。
   - 大型 `L` / 特大 `XL` ボス: `--mannequin <size_preset> down --scale <L|XL> --role <midboss|boss>` の立体構造マネキンを起点にする。
   - 4方向歩行アニメ（`walk`）: 必ず `--walk <size_preset> <dir>` を参照し、**`[Frame 0: 踏み出しA（体+1px下沈み）, Frame 1: 直立通過, Frame 2: 踏み出しB（体+1px下沈み）, Frame 3: 直立通過]`** の左右交互ストライド＋逆位相の腕振りで組む（`Frame 0 == Frame 2` かつ `Frame 1 == Frame 3` の2コマ反復ケンケン歩きは禁止）。
2. `workspace/01_raw/<asset_id>/gen_<asset_id>.py` を作成し、`tools/pixel_canvas.py` を用いて描画する。
3. トップダウン3/4見下ろしRPGの歩行キャラは、原則として **4方向（`down`, `up`, `right`, `left`）** を同じ接地Y座標（`origin[1] - 1`）で揃えて設計する。

### Phase 3: 自動スタイル検査と拡大プレビュー視覚セルフレビュー（`workspace/03_preview/`）
1. `tools/lint_character_style.py <output.png> --size <size_preset> --taste <taste_preset> --scale <S/M/L/XL> --role <role> --check-ground` を実行し、**Phase 1 仕様書ゲート・内部透過ピンホール（前髪や背負い柄と髪の境界隙間）・上下行の白目X座標ズレ（寄り目崩れ）**・実寸逸脱・接地ズレ・首伸び・きのこ頭・水平一直線ヘルメット・内部黒横線・色数超過がないことを確認する。
2. `tools/preview_sheet.py --sheet <sheet.json> --out-dir workspace/03_preview`（複数体制作時は `--lineup assets` も併用）で拡大グリッド・シルエット・4地形コントラスト・サイズ対比シートを出力し、**必ず `read_file` で画像を視覚確認する**。違和感があればスクリプトを修正して再生成する。

### Phase 4: `assets/` への配置とフォーマット自動検証
1. 完成した等倍PNG群・スプライトシート・メタデータJSONを `assets/` の所定パスへ出力する。
2. `tools/validate_assets.py assets --palette assets/palettes/master_palette.json` を実行し、命名・二値アルファ・パレット準拠・**4フレーム歩行の左右交互ストライド検査**・仕様書ゲートを含む全チェックがパスすることを確認する。

---

## 4. コマンド実行時の注意（Pythonランタイム解決）

- Windows環境では `python` がストア誘導エイリアスになっている場合があり、逆に一部のAIサンドボックス実行環境では `py` ランチャーが存在しない場合がある。
- 作業開始時に **`py` → `python3` → `python`（または既存の `.venv` / システムPythonパス）** の順で `import PIL` が通る有効なPython実行コマンドを1つ特定し、以降のツール実行で一貫して使用すること。
