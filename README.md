# ERN_RelicForge

Elden Ring: Nightreign のセーブファイル (.sl2) から遺物情報を抽出・閲覧するツール。
CLI パーサーと Electron ベースの GUI ビューアーを提供。

## Folder Structure

```
ERN_RelicForge/
├── README.md
├── LICENSE
├── requirements.txt             # Python 依存関係
├── .gitignore
│
├── src/
│   └── relic_parser.py          # セーブファイル解析パーサー
│
├── resources/
│   ├── items_data.json          # アイテムデータ (1003件, 日英名称付き)
│   └── effects_data.json        # エフェクトデータ (1117件, 日英名称付き)
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
├── debugs/                      # 開発用スクリプト
│   └── translate_items.py
│
└── examples/
    └── sample_output.json       # サンプル出力
```

## Features

- `.sl2` セーブファイルの復号化・遺物抽出
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
