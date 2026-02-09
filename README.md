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
│   ├── effects_data.json        # エフェクトデータ (1117件, 日英名称・重複可否・備考付き)
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

### セーブファイル解析
- `.sl2` セーブファイルの復号化・遺物抽出
- 遺物の ID、色、タイプ、効果、座標などを JSON 出力

### 遺物組み合わせ最適化
- 献器スロット色制約に基づく 6 スロット（通常 3 ＋ 深層 3）一括最適化
- 効果の重複可否を考慮したスコアリング
- 集中ボーナス: 同一遺物に望ましい効果が複数ある場合にスコア加算
- 除外条件: 特定の効果を含む組み合わせを除外可能
- 全献器の比較と最高スコアの自動選出

### GUI ビューアー
- 日本語 / English 対応（テーブル、詳細パネル、インスペクターすべてに反映）
- 効果名のテキスト検索（日英両対応、サジェスト付き）
- 色・タイプフィルター
- テーブルのカラムヘッダークリックによるソート
- 行クリックで詳細パネル表示（効果一覧・備考情報を含む）
- VS Code 風ミニマップ（色反映・ドラッグスクロール対応）

### 高度な検索（インスペクター）
- 効果がカテゴリー別にグループ化（全 15 カテゴリー: 能力値, 攻撃力, スキル／アーツ, 魔術, アクション, 回復, カット率, 耐性, マップ環境, チームメンバー, 夜の力, 出撃時, デメリット, キャラクター固有, その他）
- **AND グループフィルタリング**: 3 つの独立した条件グループ（グループ内は OR、グループ間は AND）
  - 例: 条件 1 で攻撃力系、条件 2 で回復系を指定 → 両方を満たす遺物のみ表示

### ビルド探索（GUI 内最適化）
- キャラクター・献器選択による一括最適化
- 通常 + 深層 6 スロット統合モード
- 効果の優先度指定（必須 / 推奨 / 任意）
- 除外条件の指定（除外:必須 / 除外:推奨 / 除外:任意）
- タブ形式の結果表示

### エフェクトデータ
- Wiki 準拠のカテゴリー自動分類（`classifyEffect`）
- 結晶雫・芳香類を含む全出撃時アイテム名の Wiki 準拠修正
- 備考欄（倍率、個数、発動条件、持続時間等）を収録

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
| `exclude_required` | 必ず除外 | -100 |
| `exclude_preferred` | なるべく除外 | -10 |
| `exclude_nice_to_have` | できれば除外 | -1 |

#### スコアリング

- **スタック可能な効果**: 重み × 遺物数（重複で恩恵あり）
- **スタック不可な効果**: 重み × 1（重複しても1回のみ）
- **集中ボーナス**: 1 つの遺物に望ましい効果が複数含まれる場合、追加スコアを加算
- required 充足の組み合わせがスコアに関わらず優先される

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
  - 効果がカテゴリー別にグループ化、カテゴリー全選択チェックボックス付き
  - AND グループ（条件1〜3）によるクロスフィルタリング

#### ビルド探索

- ツールバーの「ビルド探索」ボタンからパネルを開く
- キャラクター・献器を選択し、効果に優先度（必須/推奨/任意）または除外条件を設定
- 「探索開始」で最適な遺物組み合わせを算出、結果はタブ形式で比較可能

#### 詳細表示

テーブルの行をクリックすると右側に詳細パネルが開き、基本情報と効果一覧（備考情報を含む）を確認できる

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

このプロジェクトは以下のリポジトリおよび情報源を参考にしています:

- [nightreign-relic-browser](https://github.com/metinc/nightreign-relic-browser) - TypeScript implementation
- [ELDEN RING NIGHTREIGN 攻略 Wiki (kamikouryaku.net)](https://kamikouryaku.net/nightreign_eldenring/) - 遺物効果のカテゴリー分類、効果名称、備考情報
