# AGENTS.md — AIエージェント行動指針（2Dピクセルアート標準制作環境）

このリポジトリで作業するAIエージェントは、仕様策定・コードによるピクセル描画・パーツ分割・スプライトシート生成・品質検証のいずれを行う場合も、必ず本ドキュメントの原則と手順に従ってください。

---

## 1. 基本方針・最優先原則（Golden Rules）

1. **特定エンジンに依存しない汎用出力**
   - 最終出力は**等倍（1x）の透過PNG（RGBA）**と、標準化された**汎用JSONメタデータ**（パーツ階層・ピボット座標・Z順・アニメーション定義）で構成する。特定エンジン固有のバイナリや独自形式にロックインさせない。
2. **基本は「コードによるピクセル描画」＋「視覚フィードバック改善」**
   - アセット生成の基本手法は、Pythonスクリプト（`tools/pixel_canvas.py` 等の描画ヘルパーや記号ドットマップ）による**プログラマティックなピクセル描画**とする。
   - **重要**: 単純な矩形（`rect`）や楕円（`ellipse`）を並べただけの平坦な「プログラマーアート」にしてはならない。必ずシルエットの抑揚、1px単位の輪郭制御（ジャギー除去）、共通光源に基づくシェーディング（ハイライト・影・色相シフト）、選択的アウトライン（Sel-Out）を施すこと。
   - 描画スクリプト実行後は、必ず `workspace/03_preview/` に拡大プレビュー画像を出力し、**AI自身が画像読み取りツールで目視確認して最低1回以上のディテール改善イテレーションを行うこと**。
3. **設定なき生成の禁止**
   - `docs/01_art_direction_and_world.md` および `docs/02_color_palette_spec.md` が未作成の状態で、いきなりアセットを描画してはならない。未作成の場合は `templates/` を元にユーザーと設定集を作成すること。
4. **`workspace/` と `assets/` の厳格な分離**
   - 描画スクリプト（`gen_*.py`）や元データは `workspace/01_raw/` に保存し、いつでも再生成・色替え・微調整ができる状態を保つ。
   - 途中出力画像は `workspace/02_work/`、人間・AI確認用の整数倍拡大画像（グリッド・チェッカー背景・ピボット可視化）は `workspace/03_preview/` に出力する。
   - `assets/` には、**検収を通過した等倍（1x）PNGと汎用メタデータJSONのみ**を配置する。拡大プレビュー画像を `assets/` に混在させてはならない。

---

## 2. 作業開始時の必読ガイドライン順序

タスクに応じて、作業前に以下の `guidelines/` を必ず読み込むこと。

| 作業内容 | 必読ガイドライン |
| :--- | :--- |
| 全体フロー・新規プロジェクト開始 | `guidelines/00_workflow_overview.md`, `guidelines/01_worldbuilding_and_style.md` |
| パレット設計・配色決定 | `guidelines/03_color_and_palette.md` |
| コードによるドット描画全般 | `guidelines/02_pixel_art_fundamentals.md`, `guidelines/06_output_structure_and_naming.md` |
| キャラクターのパーツ分割（顔・体・手・足等） | `guidelines/04_part_separation_and_rig.md` |
| アニメーション・スプライトシート作成 | `guidelines/05_animation_and_spritesheet.md` |
| 最終出力・検収 | `guidelines/07_qa_checklist.md` |

---

## 3. 標準制作ワークフロー（AI実行手順）

### Phase 1: 仕様確認・定義
1. `docs/` を確認し、対象アセットのキャンバスサイズ、頭身、光源、使用パレット（`assets/palettes/`）、分割パーツ構成を確認する。
2. 個別仕様書（例: `docs/characters/chr_001_hero.md`）が未作成なら、`templates/04_character_detail_spec.template.md` から作成する。

### Phase 2: コードによるピクセル描画（`workspace/01_raw/` → `workspace/02_work/`）
1. `workspace/01_raw/<asset_id>/gen_<asset_id>.py` を作成する。
2. `tools/pixel_canvas.py` を活用し、以下の手法を組み合わせて描画する：
   - **記号グリッド（ASCII Pixel Map）**: 顔パーツ、髪房、手、小サイズアイコン（`16x16`〜`32x32`）など、1ドット単位の造形美が重要な箇所は2次元テキストマップで精密に定義する。
   - **レイヤー＆プリミティブ構築**: 中〜大サイズ（`48x48`〜`128x128`）や体幹・背景プロップは、シルエット構築 → 明暗シェーディング → 1pxアウトライン付与の3パス構造で組み立てる。
3. パーツ分割キャラクターの場合、各パーツ（`head_base`, `eyes`, `torso_upper`, `arm_upper_l` 等）を独立した関数・レイヤーとして描画し、関節部分に円形の「のりしろ（Joint Overlap）」を確保した上で `workspace/02_work/<asset_id>/parts/` に個別出力する。

### Phase 3: 合成プレビュー生成と視覚セルフレビュー（`workspace/03_preview/`）
1. `<char_id>_meta.json` にパーツの `z_index`、`parent`、`pivot`、`variants` を出力する。
2. `tools/preview_rig_composite.py`（単体画像の場合は `PixelCanvas.save_preview()`）で8倍拡大プレビュー（通常合成＋ピボット表示＋パーツ一覧シート）を `workspace/03_preview/` に出力する。
3. **生成したプレビュー画像を必ず `read_file` で視覚確認する**。頭身崩れ、ジャギー（L字の2px角）、ピローシェーディング、パーツ接続部の隙間や主線の違和感があればスクリプトを修正して再生成する。

### Phase 4: `assets/` への配置と自動バリデーション
1. 完成した等倍PNG群・スプライトシート・メタデータJSONを `assets/` の所定パスへ出力する。
2. `tools/validate_assets.py` を実行し、全チェック項目（サイズ、二値アルファ、パレット準拠、命名規則、JSON整合性）がパスすることを確認する。

---

## 4. コマンド実行時の注意

- Windows環境では `python` がストア誘導エイリアスになっている場合があるため、`py` ランチャー（例: `py tools/validate_assets.py`）または環境で有効な `python3` を使用すること。
