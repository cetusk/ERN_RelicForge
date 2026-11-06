#!/usr/bin/env python3
"""
ビルド提案（試験的）のデータ resources/build_suggest.json を作る

  python tools/build_suggest/build_data.py           # 作成（build_suggest.json と、キャラ図鑑の character_profiles.json）
  python tools/build_suggest/build_data.py --check   # 作り直した結果が今のファイルと同じか確認（テスト用）

入力（すべて神攻略wiki の調査を手で整理したもの）:
  research/archetypes_content.py  型ごとの遺物効果の対応（research/archetypes_gen.py の関数を使う）
  research/characters_gen.py      キャラ別のビルドと、キャラごとの定番の効果

効果は resources/effects_data.json のキーで指定する。存在しない効果や、未公開
（"unreleased"）の効果が含まれていたら停止する（未公開の効果はネタバレになるため出さない）。
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RESEARCH = os.path.join(HERE, 'research')
EFFECTS_PATH = os.path.join(ROOT, 'resources', 'effects_data.json')
VESSELS_PATH = os.path.join(ROOT, 'resources', 'vessels_data.json')
OUT_PATH = os.path.join(ROOT, 'resources', 'build_suggest.json')
PROFILES_PATH = os.path.join(ROOT, 'resources', 'character_profiles.json')
FORMAT = 1

effects = json.load(open(EFFECTS_PATH, encoding='utf-8'))['effects']
characters = list(json.load(open(VESSELS_PATH, encoding='utf-8'))['characters'])


def is_relic(effect_id):
    effect_id = int(effect_id)
    return effect_id < 200000 or 6000000 <= effect_id < 7400000


# key -> relic effect ids (only keys that exist on relics)
relic_ids = {}
for i, v in effects.items():
    if is_relic(i):
        relic_ids.setdefault(v['key'], []).append(int(i))
UNRELEASED_KEYS = {k for k, ids in relic_ids.items() if all(effects[str(i)].get('unreleased') for i in ids)}
NAME_BY_KEY = {k: effects[str(ids[0])]['name_ja'] for k, ids in relic_ids.items()}
errors = []


def keys_of(seq, where):
    """Keep relic effect keys in order (deduplicated); report unknown / unreleased keys."""
    out = []
    for k in seq:
        if k in out:
            continue
        if k not in relic_ids:
            errors.append(f'{where}: unknown relic effect key {k}')
        elif k in UNRELEASED_KEYS:
            errors.append(f'{where}: unreleased effect {k} {NAME_BY_KEY[k]}')
        else:
            out.append(k)
    return out


# ---------------------------------------------------------------- archetypes (型)

def load_archetypes():
    """Run archetypes_content.py inside archetypes_gen.py's helpers (key families such as PHYS)."""
    src = open(os.path.join(RESEARCH, 'archetypes_gen.py'), encoding='utf-8').read()
    src = src[:src.index('exec(open(CONTENT')]
    ns = {'__file__': os.path.join(RESEARCH, 'archetypes_gen.py'), '__name__': 'archetypes_gen'}
    argv, sys.argv = sys.argv, [sys.argv[0]]
    try:
        exec(src, ns)
        exec(open(os.path.join(RESEARCH, 'archetypes_content.py'), encoding='utf-8').read(), ns)
    finally:
        sys.argv = argv
    return ns['A'], ns


# Where each 型 goes in the input screen (axis), from the research category
AXIS = {'攻撃パターン系': 'style', '武器系': 'style', '魔術・祈祷系': 'magic',
        '状態異常・属性系': 'status', '役割系': 'role'}
# 型 that are not offered as a choice of their own (owner decisions, 2026-10-28)
NOT_A_CHOICE = {
    '武器種特化': '武器種は独立した軸（weapons）で選ぶ',
    '刀・出血': '武器種「刀」＋状態異常「出血」の組み合わせとして扱う（combos）',
    '特定戦技固定': '「戦技」を選んだあとの詳細設定にする予定（未実装）',
    '特定術の固定': '魔術・祈祷を選んだあとの詳細設定にする予定（未実装）',
}
COMBOS = {'刀・出血': {'weapons': ['刀'], 'types': ['出血']}}


def first_sentence(text):
    text = re.sub(r'\*\*', '', text.strip()).split('\n')[0]
    m = re.match(r'(.+?。)', text)
    return (m.group(1) if m else text)[:160]


def aliases_of(text):
    parts = re.split(r'[、,，]', re.sub(r'（[^）]*）', '', text or ''))
    return [p.strip() for p in parts if p.strip()]


def wiki_urls(text):
    return list(dict.fromkeys(re.findall(r'https?://[^\s）)]+', text or '')))


archetypes, ns = load_archetypes()
types = []
for a in archetypes:
    if a['name'] in NOT_A_CHOICE:
        continue
    where = f'型「{a["name"]}」'
    types.append({
        'id': a['name'],
        'axis': AXIS[a['cat']],
        'aliases': aliases_of(a.get('aliases', '')),
        'confidence': a.get('conf', '中'),
        'summary': first_sentence(a.get('desc', '')),
        'core': keys_of(a.get('core', []), where),
        'good': keys_of(a.get('good', []), where),
        'opt': keys_of(a.get('opt', []), where),
        'avoid': keys_of(a.get('avoid', []), where),
        # important for the style but not available on relics (weapon passives etc.): shown as a note
        'notOnRelics': [effects[str(min(int(i) for i, v in effects.items() if v['key'] == k))]['name_ja']
                        for k in dict.fromkeys(a.get('nonrelic', []))
                        if any(v['key'] == k for v in effects.values())],
        'sources': [u for u in wiki_urls(a.get('sources', '')) if 'kamikouryaku.net' in u],
    })

# ---------------------------------------------------------------- weapon types (武器種)

WEAPON_ORDER = ['短剣', '直剣', '大剣', '特大剣', '刺剣', '重刺剣', '曲剣', '大曲剣', '刀', '両刃剣', '斧', '大斧',
                '槌', 'フレイル', '大槌', '特大武器', '槍', '大槍', '斧槍', '鎌', '鞭', '拳', '爪', '弓', '大弓',
                'クロスボウ', 'バリスタ', '杖', '聖印', '小盾', '中盾', '大盾']
weapons = {}
for k, name in NAME_BY_KEY.items():
    if k in UNRELEASED_KEYS:
        continue
    for kind, pattern in (('attack', r'^(.+)の攻撃力上昇$'), ('three', r'^(.+)を3つ以上装備していると攻撃力上昇$'),
                          ('find', r'^潜在する力から、(.+)を見つけやすくなる$')):
        m = re.match(pattern, name)
        if m and m.group(1) in WEAPON_ORDER:
            weapons.setdefault(m.group(1), {'attack': [], 'three': [], 'find': []})[kind].append(k)
weapons = [{'id': w, **weapons[w]} for w in WEAPON_ORDER if w in weapons]

# 潜在する力から出やすい武器種（キャラごと）。神攻略wiki「潜在する力」の出現内容の詳細と各キャラページの得意武器:
#   基本は得意武器と同じ。隠者は杖、復讐者は聖印（図録の得意武器は「なし」）。追跡者の小盾・守護者の大盾は出やすくない。
#   無頼漢は 3 種が均等。「潜在する力から、○○を見つけやすくなる」はこの武器種を置き換える
#   （元から出やすい武器種を指定しても効果はない。無頼漢は 3 種から 1 種に絞る効果がある）
FAVORED_WEAPONS = {
    '追跡者': ['大剣'], '守護者': ['斧槍'], '鉄の目': ['弓'], 'レディ': ['短剣'], '無頼漢': ['大斧', '大槌', '特大武器'],
    '復讐者': ['聖印'], '隠者': ['杖'], '執行者': ['刀'], '学者': ['刺剣'], '葬儀屋': ['槌'],
}
for ch, ws in FAVORED_WEAPONS.items():
    if ch not in characters:
        errors.append(f'出やすい武器種: unknown character {ch}')
    errors.extend(f'出やすい武器種: unknown weapon type {w} ({ch})' for w in ws if all(x['id'] != w for x in weapons))

# ---------------------------------------------------------------- generic effects for the 火力 ↔ 生存 slider

GENERIC = {
    'offense': keys_of(ns['PHYS'] + ns['UNIV'], '汎用の火力'),
    'survival': keys_of(ns['VIG'] + ns['CUTP'] + ns['CUTA'] + ns['POISE'] + ns['REGAIN'], '汎用の生存'),
}

# ---------------------------------------------------------------- mode: 封牢バフ vs 侵入バフ
# 神攻略wiki（用語集「封牢バフ」「侵入バフ」、封牢・災域ページ、遺物効果）:
#   封牢の囚を倒す度 … 封牢 1 か所ごとに 5%。通常モードで人気。深き夜では封牢のボスが変異体になることがあり、
#                      大空洞には封牢が無いため採用率が大きく低下
#   夜の侵入者を倒す度 … 災域の罪人 1 体につき 7%。通常モードでは災域が発生しないことがあり人気が無かったが、
#                      深き夜では災域が必ず 1 か所以上発生し、変異体も出ないため相対的に価値が上がった
# 深層の遺物は深き夜でしか使えないので、「通常+深層」を深き夜、「通常のみ」を通常モードとみなす。
# first はモードで優先する方、second はもう一方（first より 1 段下げる）
EVERGAOL = 'attackPowerPermanentlyIncreasedForEachEvergaolPrisonerDefeated'
INVADER = 'attackPowerUpAfterDefeatingANightInvader'
MODE_PREFERENCE = {
    'normal': {'label': '通常モード', 'first': keys_of([EVERGAOL], '通常モード'), 'second': keys_of([INVADER], '通常モード')},
    'combined': {'label': '深き夜', 'first': keys_of([INVADER], '深き夜'), 'second': keys_of([EVERGAOL], '深き夜')},
}

# ---------------------------------------------------------------- character builds and staples

sys.path.insert(0, RESEARCH)
import characters_gen as cg  # noqa: E402


def entry_keys(entries, where):
    keys = []
    for x in entries:
        if isinstance(x, tuple) and x and x[0] in ('NOTE', 'MISSING'):
            continue
        ids = x[0] if isinstance(x, tuple) else x
        ids = (ids,) if isinstance(ids, int) else ids
        keys.extend(effects[str(i)]['key'] for i in ids)
    return keys_of(keys, where)


def by_tier(tiers):
    """Keep each key only in its first (highest) tier: the same key can come from two ids, e.g. 最大HP上昇 on deep
    relics (+10%) and the fixed +100 of a unique relic, which would show one effect name twice"""
    seen = set()
    for t, keys in tiers.items():
        tiers[t] = [k for k in keys if k not in seen]
        seen.update(keys)
    return tiers


def char_id(label):
    name = label.split(' (')[0]
    if name not in characters:
        errors.append(f'unknown character {label}')
    return name


def src_urls(codes):
    return [cg.SRC[c][1] for c in codes if c in cg.SRC]


builds = []
for label, items in cg.CH:
    ch = char_id(label)
    for n, b in enumerate(items, 1):
        where = f'{ch}「{b["name"]}」'
        builds.append({
            'id': f'{ch}-{n:02d}', 'character': ch, 'name': b['name'], 'aim': b.get('aim', ''),
            'mode': b.get('mode', ''), 'target': b.get('target', ''), 'vessel': b.get('vessel', ''),
            **by_tier({t: entry_keys(b.get(t, []), where) for t in ('must', 'rec', 'opt', 'avoid')}),
            'sources': src_urls(b.get('src', [])),
        })

staples = {}
for label, v in cg.STAPLES.items():
    ch = char_id(label)
    where = f'{ch} の定番'
    staples[ch] = by_tier({t: entry_keys(v.get(t, []), where) for t in ('rec', 'opt', 'avoid')})

# 深層デメリットのうち、神攻略wiki の考察で「避ける」とされるもの（全体で除外: 任意）
demerits = {'avoid': entry_keys(cg.AVOID_COMMON, '避けたい深層デメリット')}

# ---------------------------------------------------------------- per-character evaluations (research/character_effects.py)

import character_effects as ce  # noqa: E402

TIER_PRIORITY = {'body': 'preferred', 'comment': 'nice_to_have'}   # 除外の重み: 本文 = 推奨、コメント = 任意


def id_keys(ids, where):
    missing = [i for i in ids if str(i) not in effects]
    if missing:
        errors.append(f'{where}: unknown effect ids {missing}')
    return keys_of([effects[str(i)]['key'] for i in ids if str(i) in effects], where)


character_rules = {}
for ch in characters:
    avoid, useless = [], []
    for x in ce.DEMERITS.get(ch, []):
        where = f'{ch} のデメリット評価'
        if x['verdict'] != 'avoid' or x['tier'] not in TIER_PRIORITY:
            errors.append(f'{where}: unsupported {x["verdict"]} / {x["tier"]}')
        avoid += [{'key': k, 'priority': TIER_PRIORITY[x['tier']], 'tier': x['tier'], 'why': x['why']}
                  for k in id_keys(x['ids'], where)]
    for x in ce.USELESS.get(ch, []):
        useless += [{'key': k, 'why': x['why']} for k in id_keys(x['ids'], f'{ch} の意味のない効果')]
    if avoid or useless:
        character_rules[ch] = {'avoid': avoid, 'useless': useless}
for ch in set(ce.DEMERITS) | set(ce.USELESS):
    if ch not in characters:
        errors.append(f'character_effects: unknown character {ch}')

if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)

data = {
    'format': FORMAT,
    'about': 'ビルド提案（試験的）の変換ルール。出典は神攻略wiki。tools/build_suggest/build_data.py で生成（手で編集しない）',
    'types': types,
    'combos': COMBOS,
    'weapons': weapons,
    'favoredWeapons': FAVORED_WEAPONS,
    'generic': GENERIC,
    'modePreference': MODE_PREFERENCE,
    'builds': builds,
    'staples': staples,
    'demerits': demerits,
    'characters': character_rules,
}
text = json.dumps(data, ensure_ascii=False, indent=1) + '\n'

# ---------------------------------------------------------------- キャラ図鑑 (character_profiles.json)
# research/character_research.json (神攻略wiki の調査) から、アプリの「キャラ図鑑」に出す分だけ

research = ce.apply_owner_notes(json.load(open(os.path.join(RESEARCH, 'character_research.json'), encoding='utf-8')))


def research_keys(ids):
    return list(dict.fromkeys(effects[str(i)]['key'] for i in ids if str(i) in effects and is_relic(i)
                              and effects[str(i)]['key'] not in UNRELEASED_KEYS))


profiles = {'format': 1, 'about': 'キャラ図鑑のデータ。出典は神攻略wiki。tools/build_suggest/build_data.py で生成（手で編集しない）',
            'researched': research['researched'], 'pages': research['pages'], 'characters': {}}
for ch, c in research['characters'].items():
    if ch not in characters:
        errors.append(f'character_research: unknown character {ch}')
    profiles['characters'][ch] = {
        'page': c['page'], 'stats': c['stats'], 'figures': c['figures'], 'traits': c['traits'],
        'demerits': [{**{k: x[k] for k in ('name', 'source', 'verdict', 'accept_posts', 'avoid_posts', 'decision', 'tier', 'why')},
                      'keys': research_keys(x['ids'])} for x in c['demerits']],
        'important': [{**{k: x[k] for k in ('name', 'level', 'source', 'why')}, 'keys': research_keys(x['ids'])} for x in c['important']],
        'useless': [{**{k: x[k] for k in ('name', 'source', 'why')}, 'keys': research_keys(x['ids'])} for x in c['useless']],
        'contested': c['contested'],
        'changes': [{'date': v['date'], 'version': v['version'], 'kind': x['kind'], 'text': x['text']}
                    for v in research['versions'] for x in v['changes'] if x['target'] == ch],
    }
profiles_text = json.dumps(profiles, ensure_ascii=False, indent=1) + '\n'
for name in UNRELEASED_KEYS:
    if f'"{NAME_BY_KEY[name]}"' in profiles_text:
        errors.append(f'character_profiles: unreleased effect {NAME_BY_KEY[name]}')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)

if '--check' in sys.argv:
    stale = [p for p, t in ((OUT_PATH, text), (PROFILES_PATH, profiles_text))
             if not os.path.exists(p) or open(p, encoding='utf-8').read() != t]
    for p in stale:
        print(f'{p} is out of date: run python tools/build_suggest/build_data.py', file=sys.stderr)
    if stale:
        sys.exit(1)
    print(f'{OUT_PATH} and {PROFILES_PATH} are up to date')
    sys.exit(0)
with open(OUT_PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
with open(PROFILES_PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(profiles_text)
axes = {}
for t in types:
    axes[t['axis']] = axes.get(t['axis'], 0) + 1
print(f'wrote {OUT_PATH}: {len(types)} types {axes}, {len(weapons)} weapon types, '
      f'{len(builds)} builds, {len(staples)} characters with staples, {len(text.encode("utf-8")) // 1024} KB')
