#!/usr/bin/env python3
"""
ビルド提案（試験的）のデータ resources/build_suggest.json を作る

  python tools/build_suggest/build_data.py           # 作成
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
                'ボウガン', 'バリスタ', '杖', '聖印', '小盾', '中盾', '大盾', '松明']
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

# ---------------------------------------------------------------- generic effects for the 火力 ↔ 生存 slider

GENERIC = {
    'offense': keys_of(ns['PHYS'] + ns['UNIV'], '汎用の火力'),
    'survival': keys_of(ns['VIG'] + ns['CUTP'] + ns['CUTA'] + ns['POISE'] + ns['REGAIN'], '汎用の生存'),
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
            'must': entry_keys(b.get('must', []), where), 'rec': entry_keys(b.get('rec', []), where),
            'opt': entry_keys(b.get('opt', []), where), 'avoid': entry_keys(b.get('avoid', []), where),
            'sources': src_urls(b.get('src', [])),
        })

staples = {}
for label, v in cg.STAPLES.items():
    ch = char_id(label)
    where = f'{ch} の定番'
    staples[ch] = {'rec': entry_keys(v.get('rec', []), where), 'opt': entry_keys(v.get('opt', []), where),
                   'avoid': entry_keys(v.get('avoid', []), where)}

# 深層デメリットのうち、神攻略wiki の考察で「避ける」とされるもの（全体で除外: 任意）
demerits = {'avoid': entry_keys(cg.AVOID_COMMON, '避けたい深層デメリット')}

if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)

data = {
    'format': FORMAT,
    'about': 'ビルド提案（試験的）の変換ルール。出典は神攻略wiki。tools/build_suggest/build_data.py で生成（手で編集しない）',
    'types': types,
    'combos': COMBOS,
    'weapons': weapons,
    'generic': GENERIC,
    'builds': builds,
    'staples': staples,
    'demerits': demerits,
}
text = json.dumps(data, ensure_ascii=False, indent=1) + '\n'
if '--check' in sys.argv:
    with open(OUT_PATH, encoding='utf-8') as f:
        if f.read() != text:
            print(f'{OUT_PATH} is out of date: run python tools/build_suggest/build_data.py', file=sys.stderr)
            sys.exit(1)
    print(f'{OUT_PATH} is up to date')
    sys.exit(0)
with open(OUT_PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)
axes = {}
for t in types:
    axes[t['axis']] = axes.get(t['axis'], 0) + 1
print(f'wrote {OUT_PATH}: {len(types)} types {axes}, {len(weapons)} weapon types, '
      f'{len(builds)} builds, {len(staples)} characters with staples, {len(text.encode("utf-8")) // 1024} KB')
