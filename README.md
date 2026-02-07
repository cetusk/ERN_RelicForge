# ERN_RelicForge

Elden Ring: Nightreign のセーブファイルから遺物情報を抽出するツール

## Folder Structure

```
ERN_RelicForge/
├── README.md                    # このファイル
├── LICENSE                      # MIT License
├── requirements.txt             # Python依存関係
├── .gitignore                   # Git除外設定
│
├── src/
│   └── relic_parser.py         # メインパーサー
│
├── resources/
│   ├── items_data.json         # アイテムデータ（1003アイテム）
│   └── effects_data.json       # エフェクトデータ（1117エフェクト）
│
└── examples/
    └── sample_output.json      # サンプル出力（参考用）
```

## Features

- ✅ `.sl2` セーブファイルの復号化
- ✅ 遺物・遺物効果の抽出
- 🔜 日本語対応（Coming Soon）
- 🔜 組み合わせ検索機能（Coming Soon）

## Requirements

- Python 3.7 以上
- pycryptodome

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/relic_parser.py your_save_file.sl2
```

### Options

```bash
python src/relic_parser.py <save_file.sl2> [options]

Options:
  -o, --output FILE       出力ファイル名 (default: output.json)
  --items FILE           アイテムデータファイル (default: resources/items_data.json)
  --effects FILE         エフェクトデータファイル (default: resources/effects_data.json)
```

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
      "itemColor": "Green",
      "itemType": "Relic",
      "effects": [
        [
          {
            "id": 7034500,
            "key": "executorUnlockingCursedSwordRestoresHP",
            "name": "Executor Unlocking Cursed Sword Restores HP"
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

- `id`: Relic の一意なID
- `itemId`: アイテムID
- `itemKey`: アイテムのキー名
- `itemColor`: アイテムの色 (Red/Blue/Yellow/Green)
- `itemType`: アイテムタイプ (Relic/UniqueRelic/DeepRelic)
- `effects`: エフェクトのリスト (各エフェクトは id/key/name を含む)
- `coordinates`: 全体での座標 [row, column]
- `coordinatesByColor`: 色別での座標 [row, column]
- `sortKey`: ソートキー（取得順序）

## License

MIT License

## Reference

このプロジェクトは以下のリポジトリを参考にしています：

- [nightreign-relic-browser](https://github.com/metinc/nightreign-relic-browser) - TypeScript implementation