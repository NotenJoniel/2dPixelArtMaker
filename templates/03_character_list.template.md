# キャラクター・モンスター一覧台帳

<!-- 使い方: このファイルを docs/03_character_list.md にコピーし、ゲームに登場する全キャラクター・NPC・エネミーを管理します。 -->
<!-- 個別のパーツ設計や外見詳細は templates/04_character_detail_spec.template.md から docs/characters/<ID>.md を作成してリンクしてください。 -->

## 1. プレイアブル＆主要キャラクター（`chr_` — `role: hero / party`）

| アセットID | 名前 | 役割ランク (`role`) | サイズ区分 (`scale`) | 基準キャンバス | 表現方式 | 必要アニメ数 | 仕様書リンク | 進捗 |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :--- | :---: |
| `chr_001_hero` | `[例: アレン]` | `hero`（主人公） | `M` | `32 x 32` | 単一コマ打ち（4方向） | 2種 (`idle`, `walk`) | `[characters/chr_001_hero.md]` | 未着手 |
| `chr_002_partner` | `[例: リナ]` | `party`（仲間） | `M` | `32 x 32` | 単一コマ打ち（4方向） | 2種 (`idle`, `walk`) | `[characters/chr_002_partner.md]` | 未着手 |
| `chr_003_heavy` | `[例: ガルド]` | `party`（大型仲間） | `L` | `48 x 48` | 単一コマ打ち（4方向） | 2種 (`idle`, `walk`) | `[characters/chr_003_heavy.md]` | 未着手 |

---

## 2. サブキャラクター・街モブNPC（`chr_` — `role: mob`）

| アセットID | 名前 | 役割ランク (`role`) | サイズ区分 (`scale`) | 基準キャンバス | 表現方式 | 必要アニメ数 | 仕様書リンク | 進捗 |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :--- | :---: |
| `chr_101_blacksmith` | `[例: 鍛冶屋ドワーフ]` | `mob`（店主） | `M` | `32 x 32` | 単一コマ打ち | 2種 (`idle`, `work`) | `[characters/chr_101_blacksmith.md]` | 未着手 |
| `chr_102_villager_a` | `[例: 街の住人A]` | `mob`（街モブ） | `M` | `32 x 32` | 単一コマ打ち | 2種 (`idle`, `walk`) | `-` | 未着手 |

---

## 3. モンスター・ボス一覧（`mon_` — `role: enemy / midboss / boss`）

| アセットID | 名前 | 役割ランク (`role`) | サイズ区分 (`scale`) | 基準キャンバス | 表現方式 | 色替え派生（パレット違い） | 仕様書リンク | 進捗 |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :---: |
| `mon_001_slime` | `[例: コアスライム]` | `enemy`（小型ザコ） | `S` | `32 x 32` | 単一コマ打ち | `mon_002_ember_slime` (琥珀パレット) | `[characters/mon_001_slime.md]` | 未着手 |
| `mon_010_goblin` | `[例: 森の斥候鬼]` | `enemy`（標準ザコ） | `M` | `32 x 32` | 単一コマ打ち | 武器差分 | `[characters/mon_010_goblin.md]` | 未着手 |
| `mon_050_ogre` | `[例: 鉄槌のオーガ]` | `midboss`（中ボス） | `L` | `48 x 48` | 単一コマ打ち | 狂暴化赤肌パレット | `[characters/mon_050_ogre.md]` | 未着手 |
| `mon_101_guardian` | `[例: 遺跡の魔竜]` | `boss`（大ボス） | `XL` | `64 x 64` | 簡易レイヤー分割 | 発狂時コア発光差分 | `[characters/mon_101_guardian.md]` | 未着手 |

---

## 4. 進捗ステータス凡例

- `未着手`: 台帳登録のみ
- `仕様確定`: 個別詳細仕様書（`docs/characters/<id>.md`）記入完了
- `作業中`: `workspace/` にてコード描画・プレビュー調整中
- `検収済`: `assets/` 出力および `validate_assets.py` パス完了
