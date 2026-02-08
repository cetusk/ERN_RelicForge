# ERN_RelicForge

Elden Ring: Nightreign のセーブファイル (.sl2) から遺物情報を抽出・閲覧・最適化するツール。
CLI パーサー、遺物組み合わせ最適化ツール、Electron ベースの GUI ビューアーを提供。

## Folder Structure

```
ERN_RelicForge/
├── README.md
├── LICENSE
├── requirements.txt             # Python 依存関係
├── .gitignore
│
├── src/
│   ├── relic_parser.py          # セーブファイル解析パーサー
│   └── relic_optimizer.py       # 遺物組み合わせ最適化ツール
│
├── resources/
│   ├── items_data.json          # アイテムデータ (1003件, 日英名称付き)
│   ├── effects_data.json        # エフェクトデータ (1117件, 日英名称・重複可否付き)
│   └── vessels_data.json        # 献器データ (全10キャラ・4汎用献器)
│
├── gui/                         # Electron GUI アプリ
│   ├── package.json
│   ├── main.js                  # メインプロセス
│   ├── preload.js               # IPC ブリッジ
│   └── renderer/
│       ├── index.html
│       ├── app.js               # UI ロジック
│       └── style.css            # ダークテーマスタイル
│
└── examples/
    ├── sample_output.json       # パーサーサンプル出力
    ├── sample_effects_config.json  # 効果指定サンプル
    └── test_wylder_effects.json    # 追跡者テスト用効果指定
```

## Features

- `.sl2` セーブファイルの復号化・遺物抽出
- 遺物組み合わせ最適化
  - 献器スロット色制約に基づく6スロット（通常3＋深層3）一括最適化
  - 効果の重複可否を考慮したスコアリング
  - 全献器の比較と最高スコアの自動選出
- 日本語 / English 対応
- Electron GUI ビューアー
  - 効果名のテキスト検索
  - 高度な検索

## Requirements

- Python 3.7 以上
- [pycryptodome](https://pypi.org/project/pycryptodome/)
- Node.js (GUI を使う場合)

## Installation

```bash
# Python 依存パッケージ
pip install -r requirements.txt

# GUI 依存パッケージ
cd gui
npm install
```

## Usage

### CLI

```bash
python src/relic_parser.py <save_file.sl2> [options]
```

| オプション | 説明 | デフォルト |
|---|---|---|
| `-o, --output FILE` | 出力ファイル名 | `output.json` |
| `--items FILE` | アイテムデータファイル | `resources/items_data.json` |
| `--effects FILE` | エフェクトデータファイル | `resources/effects_data.json` |

```bash
# 例
python src/relic_parser.py path/to/NR0000.sl2 -o result.json
```

### 遺物最適化ツール

```bash
python src/relic_optimizer.py --input <parser_output.json> --effects <effects_config.json> [options]
```

| オプション | 説明 | デフォルト |
|---|---|---|
| `--input FILE` | relic_parser 出力の JSON ファイル | (必須) |
| `--effects FILE` | 効果指定ファイル (JSON) | なし |
| `-o, --output FILE` | 出力ファイル名 | `combinations.json` |
| `--character NAME` | キャラクター名 (例: `追跡者`, `Wylder`) | なし (全キャラ) |
| `--vessel TYPE` | 献器タイプ, カンマ区切り (例: `urn,chalice`) | なし (全献器) |
| `--combined` | 通常3＋深層3の6スロット一括最適化 | off |
| `--deep` | 深層遺物スロットを使用 (非combined時) | off |
| `--color COLOR` | 遺物の色 (献器未使用時) | なし (全色) |
| `--types TYPES` | 遺物タイプ, カンマ区切り | `Relic` |
| `--top N` | 献器あたりの出力候補数 | `10` |
| `--candidates N` | スロットあたりの候補数 | `30` |

```bash
# 例: 追跡者向け、全献器で通常+深層の一括最適化
python src/relic_optimizer.py --input output.json \
  --effects examples/test_wylder_effects.json \
  --character 追跡者 --combined -o result.json

# 例: 特定献器のみ
python src/relic_optimizer.py --input output.json \
  --effects examples/sample_effects_config.json \
  --character 追跡者 --combined --vessel chalice
```

#### 効果指定ファイル

欲しい効果とその優先度を記述する JSON ファイル:

```json
{
  "effects": [
    { "key": "physicalAttackUpPlus4", "priority": "required" },
    { "key": "improvedSkillAttackPower", "priority": "preferred" },
    { "key": "increasedRuneAcquisitionForSelfAndAllies", "priority": "nice_to_have" }
  ]
}
```

| 優先度 | 意味 | スコア重み |
|---|---|---|
| `required` | 必須 | 100 |
| `preferred` | あれば嬉しい | 10 |
| `nice_to_have` | あったら良い | 1 |

#### 出力構造

```json
{
  "bestResult": {
    "parameters": { "vessel": {...}, ... },
    "result": { "rank": 1, "score": 810, "requiredMet": true, ... }
  },
  "allResults": [
    {
      "parameters": { "vessel": {...}, ... },
      "results": [ { "rank": 1, ... }, { "rank": 2, ... }, ... ]
    }
  ]
}
```

- `bestResult` — 全献器中の最高スコア1件
- `allResults` — 全献器の top N 件

#### スコアリング

- **スタック可能な効果** (例: `physicalAttackUpPlus4`): 重み × 遺物数（重複で恩恵あり）
- **スタック不可な効果** (例: `changesCompatible...`): 重み × 1（重複しても1回のみ）
- required 充足の組み合わせがスコアに関わらず優先される

### GUI

```bash
cd gui
npm start
```

#### 基本操作

1. **ファイルを開く** - 起動後、「ファイルを開く」ボタンから `.sl2` セーブファイルを選択
2. ヘッダーにプレイヤー名、遺物数、読み込みファイル名が表示される
3. 遺物一覧テーブルが表示される

#### フィルター・検索

- **色フィルター** - ツールバーの「色」ドロップダウンで Red / Blue / Yellow / Green を選択
- **タイプフィルター** - 「タイプ」ドロップダウンで通常 / 深層 / 固有 を選択
- **テキスト検索** - 検索ボックスに効果名やアイテム名を入力（日英両対応、サジェスト付き）
- **高度な検索** - ツールバーの「高度な検索」ボタンでインスペクターパネルを開く
  - 効果がカテゴリー別 (能力値, 攻撃力, スキル／アーツ, etc.) にグループ化
  - カテゴリーは折りたたみ可能、ヒット数を表示
  - チェックボックスで複数効果を選択し「適用」で OR フィルター

#### ソート

テーブルのカラムヘッダー (#, 色, タイプ, アイテム) をクリックで昇順・降順の切替

#### 詳細表示

テーブルの行をクリックすると右側に詳細パネルが開き、基本情報と効果一覧を確認できる

#### 言語切替

ツールバーの「言語」ドロップダウンで日本語 / English を切替。テーブル、詳細パネル、インスペクターすべてに反映される

#### ミニマップ

テーブル右端に VS Code 風のミニマップを表示。遺物の色が反映され、ドラッグやクリックで高速スクロールが可能

## Output Example

```json
{
  "file": "NR0000.sl2",
  "characterName": "cetusk",
  "totalRelics": 1633,
  "relics": [
    {
      "id": 3229615531,
      "itemId": 132,
      "itemKey": "grandTranquilScene",
      "itemNameEn": "Grand Tranquil Scene",
      "itemNameJa": "壮大な静まる景色",
      "itemColor": "Green",
      "itemType": "Relic",
      "effects": [
        [
          {
            "id": 7034500,
            "key": "executorUnlockingCursedSwordRestoresHP",
            "name_en": "Executor Unlocking Cursed Sword Restores HP",
            "name_ja": "【執行者】呪剣解放時、HP回復"
          }
        ]
      ],
      "coordinates": [0, 0],
      "coordinatesByColor": [0, 0],
      "sortKey": 65350
    }
  ]
}
```

## Output Fields

| フィールド | 説明 |
|---|---|
| `id` | 遺物の一意な ID |
| `itemId` | アイテム ID |
| `itemKey` | アイテムのキー名 |
| `itemNameEn` | 英語表示名 |
| `itemNameJa` | 日本語表示名 |
| `itemColor` | 色 (Red / Blue / Yellow / Green) |
| `itemType` | タイプ (Relic / DeepRelic / UniqueRelic) |
| `effects` | 効果リスト (各効果は id / key / name_en / name_ja を含む) |
| `coordinates` | 全体での座標 [row, column] |
| `coordinatesByColor` | 色別での座標 [row, column] |
| `sortKey` | ソートキー (取得順序) |

## License

MIT License

## Reference

このプロジェクトは以下のリポジトリを参考にしています:

- [nightreign-relic-browser](https://github.com/metinc/nightreign-relic-browser) - TypeScript implementation
