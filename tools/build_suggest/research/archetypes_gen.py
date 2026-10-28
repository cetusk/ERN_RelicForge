#!/usr/bin/env python3
"""Render archetypes.md (型ごとの説明と遺物効果の対応) from archetypes_content.py.

Effect names are pulled verbatim from resources/effects_data.json via keys. Effects marked
"unreleased" there are never output (spoilers).

  python tools/build_suggest/research/archetypes_gen.py [effects_data.json] [out.md]
"""
import json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "resources", "effects_data.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "archetypes.md")
CONTENT = os.path.join(HERE, "archetypes_content.py")
HEAD = os.path.join(HERE, "archetypes_head.md")
TAIL = os.path.join(HERE, "archetypes_tail.md")
eff = json.load(open(DATA, encoding="utf-8"))["effects"]
# 未公開の効果（effects_data.json の "unreleased"）: 一切出力しない
UNREL = [{"id": int(k), "key": v["key"], "name_ja": v["name_ja"]} for k, v in eff.items() if v.get("unreleased")]
UNREL_IDS = {int(u["id"]) for u in UNREL}
UNREL_KEYS = set()

def is_relic(i):
    i = int(i)
    return i < 200000 or 6000000 <= i <= 7399999

relic_by_key = collections.OrderedDict()
non_by_key = collections.OrderedDict()
for k, v in eff.items():
    if int(k) in UNREL_IDS:
        UNREL_KEYS.add(v["key"])
        continue
    d = relic_by_key if is_relic(k) else non_by_key
    d.setdefault(v["key"], []).append((int(k), v))
# 未実装 id と同じ key・同じ名前の効果は、遺物外（付帯効果など）であっても出力しない
UNREL_NAMES = {u["name_ja"] for u in UNREL}
for dct in (relic_by_key, non_by_key):
    for key in list(dct):
        if key in UNREL_KEYS or any(v["name_ja"] in UNREL_NAMES for _, v in dct[key]):
            del dct[key]

unreleased_refs = []

missing = []

def fam(*prefixes_or_keys):
    return list(prefixes_or_keys)

def render(keys, nonrelic=False):
    src = non_by_key if nonrelic else relic_by_key
    out = []
    seen = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        if key in UNREL_KEYS:
            unreleased_refs.append(key)
            continue
        if key not in src:
            missing.append((key, nonrelic))
            out.append(f"- ⚠ `{key}`（ファイルに無し）")
            continue
        items = sorted(src[key], key=lambda t: t[0])
        names = []
        for i, v in items:
            n = v["name_ja"]
            if n not in names:
                names.append(n)
        ids = ",".join(str(i) for i, _ in items)
        deep = any(v.get("deepOnly") for _, v in items)
        nondeep = any(not v.get("deepOnly") for _, v in items)
        tag = ""
        if deep and not nondeep:
            tag = "［深層のみ］"
        elif deep and nondeep:
            tag = "［通常/深層あり］"
        note = items[0][1].get("stackNotes", "")
        note = f" — {note}" if note else ""
        out.append(f"- {' / '.join(names)}（`{key}`, id {ids}）{tag}{note}")
    return "\n".join(out) if out else "- （該当なし）"

# ---------- key families ----------
def plus(base, n_from=1, n_to=2, cap=True):
    ks = [base]
    for n in range(n_from, n_to + 1):
        ks.append(f"{base}Plus{n}")
    return ks

PHYS = ["physicalAttackUp", "physicalAttackUpPlus1", "physicalAttackUpPlus2", "physicalAttackUpPlus3", "physicalAttackUpPlus4"]
MAG = ["magicAttackPowerUp", "magicAttackPowerUpPlus1", "magicAttackPowerUpPlus2", "magicAttackPowerUpPlus3", "magicAttackPowerUpPlus4"]
FIRE = ["fireAttackPowerUp", "fireAttackPowerUpPlus1", "fireAttackPowerUpPlus2", "fireAttackPowerUpPlus3", "fireAttackPowerUpPlus4"]
LIT = ["lightningAttackPowerUp", "lightningAttackPowerUpPlus1", "lightningAttackPowerUpPlus2", "lightningAttackPowerUpPlus3", "lightningAttackPowerUpPlus4"]
HOLY = ["holyAttackPowerUp", "holyAttackPowerUpPlus1", "holyAttackPowerUpPlus2", "holyAttackPowerUpPlus3", "holyAttackPowerUpPlus4"]
AFF = ["improvedAffinityAttackPower", "improvedAffinityAttackPowerPlus1", "improvedAffinityAttackPowerPlus2"]
SORC = ["improvedSorceries", "improvedSorceriesPlus1", "improvedSorceriesPlus2"]
INC = ["improvedIncantations", "improvedIncantationsPlus1", "improvedIncantationsPlus2"]
UNIV = ["attackPowerUpAfterDefeatingANightInvader", "attackPowerPermanentlyIncreasedForEachEvergaolPrisonerDefeated"]
STR = ["strengthPlus1", "strengthPlus2", "strengthPlus3"]
DEX = ["dexterityPlus1", "dexterityPlus2", "dexterityPlus3"]
INT = ["intelligencePlus1", "intelligencePlus2", "intelligencePlus3"]
FAI = ["faithPlus1", "faithPlus2", "faithPlus3"]
ARC = ["arcanePlus1", "arcanePlus2", "arcanePlus3"]
VIG = ["vigorPlus1", "vigorPlus2", "vigorPlus3", "increasedMaximumHP"]
MIND = ["mindPlus1", "mindPlus2", "mindPlus3", "increasedMaximumFP"]
END = ["endurancePlus1", "endurancePlus2", "endurancePlus3", "increasedMaximumStamina"]
STAMREC = ["staminaRecoveryUponLandingAttacks", "staminaRecoveryUponLandingAttacksPlus1"]
POISE = ["poisePlus1", "poisePlus2", "poisePlus3"]
CUTP = ["improvedPhysicalDamageNegation", "improvedPhysicalDamageNegationPlus1", "improvedPhysicalDamageNegationPlus2"]
CUTA = ["improvedAffinityDamageNegation", "improvedAffinityDamageNegationPlus1", "improvedAffinityDamageNegationPlus2"]
SKILLCD = ["characterSkillCooldownReductionPlus1", "characterSkillCooldownReductionPlus2", "characterSkillCooldownReductionPlus3"]
ARTCHG = ["ultimateArtAutoChargePlus1", "ultimateArtAutoChargePlus2", "ultimateArtAutoChargePlus3"]
ARTKILL = ["defeatingEnemiesFillsMoreOfTheArtGauge", "defeatingEnemiesFillsMoreOfTheArtGaugePlus1"]
REGAIN = ["partialHpRestorationUponPostDamageAttacks", "partialHPRestorationUponPostDamageAttacksPlus1", "partialHPRestorationUponPostDamageAttacksPlus2"]
FPSUST = ["reducedFPConsumption", "continuousFpRecovery"]
CRIT = ["improvedCriticalHits", "improvedCriticalHitsPlus1"]
CRITSIDE = ["criticalHitBoostsStaminaRecoverySpeed", "criticalHitBoostsStaminaRecoverySpeedPlus1",
            "artGaugeFillsModeratelyUponCriticalHit", "artGaugeFillsModeratelyUponCriticalHitPlus1",
            "criticalHitsEarnRunes"]
EVADE_DEMERIT = ["moreDamageTakenAfterEvasion", "repeatedEvasionsLowerDamageNegation"]
ATK_DEMERIT = ["lowerAttackWhenBelowMaxHP"]

WT = {  # weapon type -> CamelName used in keys
    "短剣": "Dagger", "直剣": "StraightSword", "大剣": "Greatsword", "特大剣": "ColossalSword", "曲剣": "CurvedSword",
    "大曲剣": "CurvedGreatsword", "刀": "Katana", "両刃剣": "Twinblade", "刺剣": "ThrustingSword", "重刺剣": "HeavyThrustingSword",
    "斧": "Axe", "大斧": "Greataxe", "槌": "Hammer", "大槌": "GreatHammer", "フレイル": "Flail", "槍": "Spear", "大槍": "GreatSpear",
    "斧槍": "Halberd", "鎌": "Reaper", "拳": "Fist", "爪": "Claw", "鞭": "Whip", "特大武器": "ColossalWeapon", "弓": "Bow",
}
PLURAL = {"Katana": "Katana", "Axe": "Axes", "Greataxe": "Greataxes", "Hammer": "Hammers", "GreatHammer": "GreatHammers",
          "Flail": "Flails", "Spear": "Spears", "GreatSpear": "GreatSpears", "Halberd": "Halberds", "Reaper": "Reapers",
          "Fist": "Fists", "Claw": "Claws", "Whip": "Whips", "ColossalWeapon": "ColossalWeapons", "Bow": "Bows",
          "Dagger": "Daggers", "StraightSword": "StraightSwords", "Greatsword": "Greatswords", "ColossalSword": "ColossalSwords",
          "CurvedSword": "CurvedSwords", "CurvedGreatsword": "CurvedGreatswords", "Twinblade": "Twinblades",
          "ThrustingSword": "ThrustingSwords", "HeavyThrustingSword": "HeavyThrustingSwords"}

def wt_keys(jp, which=("atk", "3plus", "find", "hp", "fp")):
    c = WT[jp]
    p = PLURAL[c]
    ks = []
    if "atk" in which: ks.append(f"improved{c}AttackPower")
    if "3plus" in which: ks.append(f"improvedAttackPowerWith3Plus{p}Equipped")
    if "find" in which: ks.append(f"dormantPowerHelpsDiscover{p}")
    if "hp" in which: ks.append(f"hpRestorationUpon{c}Attacks")
    if "fp" in which: ks.append(f"fpRestorationUpon{c}Attacks")
    return ks

def wt_many(jps, which=("atk", "3plus", "find")):
    ks = []
    for j in jps:
        ks += wt_keys(j, which)
    return ks

# ---------- archetype definitions ----------
# each: dict(id, cat, name, aliases, desc, chars, core, good, opt, avoid, nonrelic, notes, sources)
A = []
def add(**kw):
    A.append(kw)

exec(open(CONTENT, encoding="utf-8").read())  # archetype content file

# ---------- render ----------
L = []
L.append(open(HEAD, encoding="utf-8").read().rstrip() + "\n")
cats = []
for a in A:
    if a["cat"] not in cats:
        cats.append(a["cat"])
L.append("## 目次\n")
for c in cats:
    L.append(f"- **{c}**: " + "、".join(f"{a['name']}" for a in A if a["cat"] == c))
L.append("")
for c in cats:
    L.append(f"\n# {c}\n")
    for a in A:
        if a["cat"] != c:
            continue
        L.append(f"## {a['name']}\n")
        L.append(f"- **標準名**: {a['name']}")
        L.append(f"- **別名・表記ゆれ**: {a['aliases']}")
        if a.get("axis"):
            L.append(f"- **軸**: `{a['axis']}`（型ではなく別軸の参考項目）")
        L.append(f"- **信頼度**: {a.get('conf','中')}\n")
        L.append(f"### 説明（ナイトレインでの意味）\n{a['desc'].strip()}\n")
        L.append(f"### 向いているキャラ\n{a['chars'].strip()}\n")
        L.append("### 関連する遺物効果\n")
        L.append("**中核**\n" + render(a.get("core", [])) + "\n")
        L.append("**相性良**\n" + render(a.get("good", [])) + "\n")
        L.append("**任意**\n" + render(a.get("opt", [])) + "\n")
        L.append("**避けたい**\n" + render(a.get("avoid", [])) + "\n")
        if a.get("nonrelic"):
            L.append("**参考：遺物ではない（付帯効果・潜在など、id が遺物範囲外）が、この型で重要な効果**\n" + render(a["nonrelic"], nonrelic=True) + "\n")
        if a.get("missing_note"):
            L.append("**コミュニティ推奨だがファイルに遺物効果として無いもの**\n" + a["missing_note"].strip() + "\n")
        L.append(f"### 注意点\n{a['notes'].strip()}\n")
        L.append(f"### 出典\n{a['sources'].strip()}\n")
L.append(open(TAIL, encoding="utf-8").read().rstrip() + "\n")
open(OUT, "w", encoding="utf-8").write("\n".join(L))
if missing:
    print("MISSING:", missing)
    sys.exit(1)
if unreleased_refs:
    print("UNRELEASED KEY REFERENCED:", sorted(set(unreleased_refs)))
    sys.exit(1)
# 出力全文に未実装効果名が無いか（実装済み効果名の一部として含まれる場合は除外して判定）
text = "\n".join(L)
masked = text
released_names = sorted({v["name_ja"] for k, v in eff.items() if int(k) not in UNREL_IDS}, key=len, reverse=True)
for n in released_names:
    if n not in UNREL_NAMES and any(u in n for u in UNREL_NAMES):
        masked = masked.replace(n, "＿")
hits = sorted({u for u in UNREL_NAMES if u in masked})
if hits:
    print("UNRELEASED NAME IN OUTPUT:", hits)
    for h in hits:
        for ln in masked.split("\n"):
            if h in ln:
                print("  ", h, "=>", ln[:160])
    sys.exit(1)
print("ok", len(A), "archetypes")
