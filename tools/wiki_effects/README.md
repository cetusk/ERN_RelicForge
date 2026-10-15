# 効果データの Wiki 照合ツール

攻略 Wiki（[ELDEN RING NIGHTREIGN 攻略 Wiki の「遺物効果」ページ](https://kamikouryaku.net/nightreign_eldenring/?%E9%81%BA%E7%89%A9%E5%8A%B9%E6%9E%9C)）と
`resources/effects_data.json` の **重ね掛け（`stackable`）・備考（`stackNotes` / `stackNotesFull`）** を照合し、
差分をレビューページで確認してからデータに反映する。

ゲームのアップデートや Wiki の更新があったときに実行する。

## 使い方

```bash
# 1. Wiki を取得して照合し、レビューページを作成（データは変更しない）
python tools/wiki_effects/sync.py

# 2. debugs/effects_review/index.html をブラウザで開いて差分を確認
#    （「重複が変わる」「要約が変わる」「要確認の印あり」で絞り込める）

# 3. 問題なければ反映
python tools/wiki_effects/sync.py --offline --apply
```

| オプション | 説明 |
|---|---|
| `--offline` | Wiki を取得せず、前回保存した `debugs/effects_review/wiki.html` を使う |
| `--apply` | 照合結果を `resources/effects_data.json` に反映する |
| `--saves FILE ...` | 「セーブに出現した効果」の判定に使うセーブファイル（既定: `debugs/*.sl2`） |
| `--out-dir DIR` | 出力先（既定: `debugs/effects_review`、Git 管理外） |

反映後は `python -m unittest discover -s tests` と `node --test tests/*.test.js` を実行し、
重ね掛けの変更でビルド探索の期待値が変わった場合は `python tests/fixtures/generate.py` で再生成する。

## 照合の仕組み

- **対象**: 遺物に付く効果（ID が 20 万未満の固有遺物の効果、深層 600 万台、通常 700 万台）
- **Wiki の表**: 「効果 / 重ね掛け / (デメリット) / 備考」の表と、キャラクター固有の表（同じ効果は重ね掛け不可）
- **名前の照合**: 完全一致 → 対応表（`rules.py`）→「○○」を含む汎用行のパターン →
  節の説明で決まる効果（戦技の変更）の順。`+0~2` のような段階のまとめ書きは段階ごとに展開する
- **通常と深層**: 同名でも別の効果があるため、ID の範囲で Wiki の節（通常 / 深層）を選ぶ。
  深層の表で「既存効果」とだけ書かれた備考は、通常の表の同名効果の備考を使う
- **重ね掛け**: ◯ → 可、✕ → 不可、※ →「+値・武器種が違えば可」なら同じ効果どうしは不可（×）、
  それ以外は条件付き（△）、－（未検証）→ 現在の値のまま「重複は未検証」と記載
- **要約（`stackNotes`）**: 段階付きの効果はその段階の値（例: `+0~2: +4%/+5%/+6%` の +1 → `+5%`）。
  既存の要約が Wiki の全文と矛盾しなければ維持し、それ以外は全文の 1 行目から自動で作る。
  自動で作れないものは `rules.py` の `SUMMARY_OVERRIDES` に手書きする
- **全文（`stackNotesFull`）**: Wiki の備考（行区切りは ` / `）。ページ内の別の場所を指す記述は除く

## ファイル

| ファイル | 内容 |
|---|---|
| `sync.py` | 実行コマンド（取得 → 照合 → レビューページ → 反映） |
| `wiki.py` | Wiki ページの取得と表の解析（結合セルの展開） |
| `match.py` | 照合と更新案（重ね掛け・要約・全文）の作成 |
| `rules.py` | **手で確認したルール**（名前の対応表、手書きの要約、整形ルール） |
| `report.py` | レビューページの作成 |

## 照合できない効果が出たとき

実行時に `WARNING: ... effects seen in saves have no wiki row` が出た場合は、
セーブに出現する効果が Wiki のどの行にも対応していない。レビューページの「候補」列を参考に
Wiki 側の名前を確認し、`rules.py` の `NAME_ALIASES`（または `NAME_REWRITES`）に追加して再実行する。
