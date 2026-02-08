#!/usr/bin/env python3
"""
items_data.json に name_en (英語表示名) と name_ja (日本語公式名) を追加するスクリプト
"""
import json
import re
import os

ITEMS_FILE = os.path.join(os.path.dirname(__file__), '..', 'resources', 'items_data.json')

# === key → name_ja マッピング ===
# GameWith, Game8, Gamerch 等の日本語wikiから取得した公式名
KEY_TO_JA = {
    # Misc / Currency
    "sovereignSigil": "王の証",
    "scenicFlatstone": "景色の原石",
    "largeScenicFlatstone": "大きな景色の原石",
    "nightShard": "夜の欠片",

    # Standard Scene Relics - Burning (燃える景色)
    "delicateBurningScene": "繊細な燃える景色",
    "polishedBurningScene": "端正な燃える景色",
    "grandBurningScene": "壮大な燃える景色",

    # Standard Scene Relics - Drizzly (滴る景色)
    "delicateDrizzlyScene": "繊細な滴る景色",
    "polishedDrizzlyScene": "端正な滴る景色",
    "grandDrizzlyScene": "壮大な滴る景色",

    # Standard Scene Relics - Luminous (輝く景色)
    "delicateLuminousScene": "繊細な輝く景色",
    "polishedLuminousScene": "端正な輝く景色",
    "grandLuminousScene": "壮大な輝く景色",

    # Standard Scene Relics - Tranquil (静まる景色)
    "delicateTranquilScene": "繊細な静まる景色",
    "polishedTranquilScene": "端正な静まる景色",
    "grandTranquilScene": "壮大な静まる景色",

    # Deep Scene Relics - Burning
    "deepDelicateBurningScene": "繊細な燃える景色（深層）",
    "deepPolishedBurningScene": "端正な燃える景色（深層）",
    "deepGrandBurningScene": "壮大な燃える景色（深層）",

    # Deep Scene Relics - Drizzly
    "deepDelicateDrizzlyScene": "繊細な滴る景色（深層）",
    "deepPolishedDrizzlyScene": "端正な滴る景色（深層）",
    "deepGrandDrizzlyScene": "壮大な滴る景色（深層）",

    # Deep Scene Relics - Luminous
    "deepDelicateLuminousScene": "繊細な輝く景色（深層）",
    "deepPolishedLuminousScene": "端正な輝く景色（深層）",
    "deepGrandLuminousScene": "壮大な輝く景色（深層）",

    # Deep Scene Relics - Tranquil
    "deepDelicateTranquilScene": "繊細な静まる景色（深層）",
    "deepPolishedTranquilScene": "端正な静まる景色（深層）",
    "deepGrandTranquilScene": "壮大な静まる景色（深層）",

    # Night Lord Boss Relics (夜の王ドロップ)
    "nightOfTheBeast": "獣の夜",
    "nightOfTheBaron": "爵の夜",
    "nightOfTheChampion": "狩人の夜",
    "nightOfTheDemon": "魔の夜",
    "nightOfTheFathom": "深海の夜",
    "nightOfTheLord": "王の夜",
    "nightOfTheMiasma": "霞の夜",
    "nightOfTheWise": "識の夜",

    # Dark Night Relics (常夜の王ドロップ)
    "darkNightOfTheBaron": "爵の暗き夜",
    "darkNightOfTheBeast": "獣の暗き夜",
    "darkNightOfTheChampion": "狩人の暗き夜",
    "darkNightOfTheDemon": "魔の暗き夜",
    "darkNightOfTheFathom": "深海の暗き夜",
    "darkNightOfTheMiasma": "霞の暗き夜",
    "darkNightOfTheWise": "識の暗き夜",

    # Special Night / Boss Relics
    "theNightOfDregs": "瓦礫の夜",
    "vestigeOfNight": "夜の痕跡",
    "theWillOfTheBalance": "安寧者の遺志",
    "theWillOfTheBalancers": "安寧の意志",

    # Tutorial / Misc Relics
    "fellOmenFetish": "忌み鬼の呪物",
    "besmirchedFrame": "薄汚れたフレーム",
    "oldPocketwatch": "古びた懐中時計",

    # Wylder (追跡者) Journal
    "slateWhetstone": "にび色の砥石",
    "silverTear": "銀の雫",
    "theWyldersEarring": "追跡者の耳飾り",

    # Guardian (守護者) Journal
    "stoneStake": "石の杭",
    "thirdVolume": "三冊目の本",
    "witchsBrooch": "魔女のブローチ",
    "crackedWitchsBrooch": "砕けた魔女のブローチ",

    # Iron Eye (鉄の目) Journal
    "fineArrowhead": "細い矢尻",
    "crackedSealingWax": "割れた封蝋",
    "edgeOfOrder": "聖律の刃",

    # Duchess (レディ) Journal
    "goldenDew": "金色の露",
    "crownMedal": "頭冠のメダル",
    "blessedIronCoin": "祝福された鉄貨",

    # Raider (無頼漢) Journal
    "tornBraidedCord": "ちぎれた組み紐",
    "blackClawNecklace": "黒爪の首飾り",

    # Revenant (復讐者) Journal
    "bladeOfNightFragment": "夜の刃片",
    "smallMakeupBrush": "小さな化粧道具",
    "oldPortrait": "古びたミニアチュール",

    # Recluse (隠者) Journal
    "boneLikeStone": "骨のような石",

    # Executor (執行者) Journal
    "blessedFlowers": "祝福された花",
    "goldenShell": "黄金の殻",
    "goldenSprout": "黄金の萌芽",

    # Scholar (学者) Journal (DLC)
    "cleansingTear": "清浄の雫",
    "noteMyDearSuccessor": "記録「後継者へ」",

    # Undertaker (葬儀屋) Journal (DLC)
    "leatherMonocleCase": "片眼鏡の革袋",
    "glassNecklace": "ガラスの首飾り",
}


def camel_to_title(key):
    """camelCase を Title Case に変換 (e.g. 'delicateBurningScene' -> 'Delicate Burning Scene')"""
    words = re.sub(r'([A-Z])', r' \1', key).strip()
    return words[0].upper() + words[1:]


def main():
    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']
    updated = 0
    missing = []

    for item_id, item_info in items.items():
        key = item_info['key']
        name_en = camel_to_title(key)
        name_ja = KEY_TO_JA.get(key)

        if name_ja is None:
            missing.append((item_id, key))
            name_ja = name_en  # Fallback to English

        item_info['name_en'] = name_en
        item_info['name_ja'] = name_ja
        updated += 1

    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f"Updated: {updated} items")
    print(f"Missing JA translations: {len(missing)}")
    for item_id, key in missing:
        print(f"  ID {item_id}: {key}")


if __name__ == '__main__':
    main()
