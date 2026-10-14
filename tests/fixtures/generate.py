#!/usr/bin/env python3
"""
テスト用フィクスチャの生成スクリプト

実際のセーブファイルは個人情報 (Steam ID 等) を含むためリポジトリに含めない。
代わりに、遺物スロットの構造を再現した合成セーブファイルと、ゲームデータから
決定的に生成した遺物プールを使ってテストする。

生成物 (tests/fixtures/):
  synthetic_save.sl2       合成セーブファイル (AES-CBC 暗号化済み BND4)
  items_min.json           パーサーテスト用の最小アイテムデータ
  effects_min.json         パーサーテスト用の最小効果データ
  parser_expected.json     合成セーブの期待される解析結果
  relic_pool.json          オプティマイザテスト用の遺物プール (パーサー出力形式)
  optimizer_scenarios.json オプティマイザのテストシナリオ
  optimizer_expected.json  各シナリオの期待される結果

期待値は Python 版で生成し、テストでは Python 版・JS 版 (web / gui) の両方が
これと一致することを確認する。意図した挙動変更の後は、このスクリプトを再実行して
差分を確認したうえでコミットすること:

  python tests/fixtures/generate.py
"""

import json
import os
import random
import struct
import subprocess
import sys
import tempfile

from Crypto.Cipher import AES

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(FIXTURES_DIR, '..', '..'))
RESOURCES_DIR = os.path.join(ROOT_DIR, 'resources')

DS2_KEY = bytes.fromhex('18f6326605bd178a5524523ac0a0c609')
EMPTY = 0xFFFFFFFF


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(name, data):
    with open(os.path.join(FIXTURES_DIR, name), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')


# ============================================================
# Synthetic save file (parser tests)
# ============================================================

# Item IDs (from resources/items_data.json)
ITEM_NORMAL_RED = 100        # Relic / Red
ITEM_NORMAL_BLUE = 109       # Relic / Blue
ITEM_DEEP = 2000000          # DeepRelic
ITEM_UNIQUE = 12002          # UniqueRelic (2nd item field differs: 12003)
# IDs deliberately absent from items_min.json / effects_min.json
ITEM_UNKNOWN = 99001
EFFECT_UNKNOWN = 7999901


def pick_effects(effects, lo, hi, n):
    """Pick the first n effect IDs in [lo, hi) (deterministic)."""
    ids = sorted(int(k) for k in effects if lo <= int(k) < hi)
    return ids[:n]


def relic_slot(relic_id, item_id, effect_ids, debuff_ids=(), item_id2=None):
    """80-byte relic slot with the layout found in real save files."""
    effs = list(effect_ids) + [EMPTY] * (4 - len(effect_ids))
    debs = list(debuff_ids) + [EMPTY] * (4 - len(debuff_ids))
    item2 = item_id if item_id2 is None else item_id2
    slot = struct.pack('<IIII', relic_id, item_id | 0x80000000, item2 | 0x80000000, EMPTY)  # +0
    slot += struct.pack('<IIII', *effs)                                                  # +16
    slot += struct.pack('<I', EMPTY) + bytes([0, 0, 0, 0xFF]) + bytes(8)                 # +32
    slot += struct.pack('<II', EMPTY, EMPTY)                                             # +48
    slot += struct.pack('<IIII', *debs)                                                  # +56
    slot += bytes(8)                                                                     # +72
    assert len(slot) == 80
    return slot


def build_save_entry(effects_all):
    """Build decrypted entry 0 content and return (clean_data, effect IDs for effects_min.json)."""
    normal = pick_effects(effects_all, 7000000, 7100000, 6)
    deep = pick_effects(effects_all, 6000000, 6100000, 3)
    debuffs = pick_effects(effects_all, 6800000, 6900000, 2)

    rid = lambda n: 0xC0800000 | n  # b3=0x80, b4=0xC0
    relics = [
        # (relic_id, item_id, effects, debuffs, item_id2, sort_key)
        (rid(0x101), ITEM_NORMAL_RED, normal[0:3], [], None, 500),
        (rid(0x102), ITEM_NORMAL_BLUE, normal[3:4], [debuffs[0]], None, 400),
        (rid(0x103), ITEM_DEEP, deep[0:2], [debuffs[0], debuffs[1]], None, 300),
        (rid(0x104), ITEM_UNIQUE, normal[4:6], [], ITEM_UNIQUE + 1, 600),
        # unknown effect (known item)
        (rid(0x105), ITEM_NORMAL_RED, [normal[0], EFFECT_UNKNOWN], [], None, 200),
        # unknown item (known effects) -> coordinates null
        (rid(0x106), ITEM_UNKNOWN, normal[1:3], [], None, 450),
        # unknown debuff only
        (rid(0x107), ITEM_NORMAL_BLUE, normal[2:3], [EFFECT_UNKNOWN], None, 100),
    ]
    noise = [
        # unknown item, item field without 0x80 flag -> not a relic slot
        (struct.pack('<IIII', rid(0x201), ITEM_UNKNOWN, ITEM_UNKNOWN, EMPTY)
         + struct.pack('<IIII', normal[0], EMPTY, EMPTY, EMPTY) + bytes(48), 50),
        # unknown effect ID above 24 bits -> not a relic slot
        (relic_slot(rid(0x202), ITEM_UNKNOWN, [0x6F006D00]), 60),
        # same relic ID as a known relic (later in data) -> skipped
        (relic_slot(rid(0x101), ITEM_UNKNOWN, [EFFECT_UNKNOWN]), None),
        # valid relic slot without a sort-key record -> skipped
        (relic_slot(rid(0x203), ITEM_NORMAL_RED, normal[0:1]), None),
    ]

    data = bytearray(0x2000)
    # Character name: UTF-16LE name, terminator, NAME_PATTERN 51 bytes after name start
    name = 'Tester'.encode('utf-16-le') + b'\x00\x00'
    data[0x100:0x100 + len(name)] = name
    data[0x100 + 51:0x100 + 51 + 7] = bytes.fromhex('27000046414345')

    pos = 0x400
    sort_records = []
    for relic_id, item_id, effs, debs, item2, sort_key in relics:
        data[pos:pos + 80] = relic_slot(relic_id, item_id, effs, debs, item2)
        sort_records.append((relic_id, sort_key))
        pos += 96
    for blob, sort_key in noise:
        data[pos:pos + len(blob)] = blob
        if sort_key is not None:
            sort_records.append((struct.unpack_from('<I', blob, 0)[0], sort_key))
        pos += 96

    # Sort-key records: [id][01 00 00 00][sortKey u16][pad]
    pos = 0x1400
    for relic_id, sort_key in sort_records:
        data[pos:pos + 12] = struct.pack('<IIHH', relic_id, 1, sort_key, 0)
        pos += 16

    min_effect_ids = sorted(set(normal + deep + debuffs))
    return bytes(data), min_effect_ids


def build_sl2(clean_data):
    """Wrap entry data in a BND4 container encrypted like a real .sl2 file."""
    plain = bytes(4) + clean_data
    plain += bytes(-len(plain) % 16)
    iv = bytes(range(16))
    payload = iv + AES.new(DS2_KEY, AES.MODE_CBC, iv).encrypt(plain)

    header = bytearray(64)
    header[0:4] = b'BND4'
    struct.pack_into('<I', header, 12, 1)  # entry count
    entry_header = bytearray(32)
    entry_header[0:8] = b'\x40\x00\x00\x00\xff\xff\xff\xff'
    data_offset = 64 + 32
    struct.pack_into('<I', entry_header, 8, len(payload))
    struct.pack_into('<I', entry_header, 16, data_offset)
    return bytes(header) + bytes(entry_header) + payload


def generate_parser_fixtures(items_all, effects_all):
    clean, min_effect_ids = build_save_entry(effects_all)
    with open(os.path.join(FIXTURES_DIR, 'synthetic_save.sl2'), 'wb') as f:
        f.write(build_sl2(clean))

    item_ids = [ITEM_NORMAL_RED, ITEM_NORMAL_BLUE, ITEM_DEEP, ITEM_UNIQUE]
    write_json('items_min.json', {'items': {str(i): items_all[str(i)] for i in item_ids}})
    write_json('effects_min.json', {'effects': {str(i): effects_all[str(i)] for i in min_effect_ids}})

    out_path = os.path.join(tempfile.mkdtemp(), 'out.json')
    subprocess.run(
        [sys.executable, os.path.join(ROOT_DIR, 'src', 'relic_parser.py'),
         os.path.join(FIXTURES_DIR, 'synthetic_save.sl2'), '-o', out_path,
         '--items', os.path.join(FIXTURES_DIR, 'items_min.json'),
         '--effects', os.path.join(FIXTURES_DIR, 'effects_min.json')],
        check=True, capture_output=True)
    result = load_json(out_path)
    result.pop('file')
    write_json('parser_expected.json', result)
    print(f"parser: {result['totalRelics']} relics ({result['unknownRelics']} unknown)")


# ============================================================
# Relic pool + scenarios (optimizer tests)
# ============================================================

POOL_SEED = 20261014
SCENARIO_KEYS_PER_CHAR = 6


def effect_entry(effects_all, eid):
    e = effects_all[str(eid)]
    return {'id': eid, 'key': e['key'], 'name_en': e['name_en'], 'name_ja': e['name_ja']}


def generate_relic_pool(items_all, effects_all):
    """Deterministic pool resembling real inventories (effect ID ranges per relic type)."""
    rng = random.Random(POOL_SEED)
    by_type = {}
    for k, v in items_all.items():
        by_type.setdefault(v['type'], []).append(int(k))
    for v in by_type.values():
        v.sort()

    eff_ids = sorted(int(k) for k in effects_all)
    normal_effects = [i for i in eff_ids if 7000000 <= i < 7400000 and not effects_all[str(i)].get('deepOnly')]
    deep_effects = [i for i in eff_ids if (6000000 <= i < 6700000 or 7000000 <= i < 7400000)]
    debuff_effects = [i for i in eff_ids if 6800000 <= i < 6900000]

    plan = [('Relic', 260, normal_effects, 0.0), ('DeepRelic', 160, deep_effects, 0.4),
            ('UniqueRelic', 20, normal_effects, 0.0)]
    relics = []
    next_id = 0xC0800001
    for item_type, count, pool, debuff_rate in plan:
        for _ in range(count):
            item_id = rng.choice(by_type[item_type])
            item = items_all[str(item_id)]
            n_eff = rng.choice([2, 3, 3])
            effects = []
            for eid in rng.sample(pool, n_eff):
                group = [effect_entry(effects_all, eid)]
                if rng.random() < debuff_rate:
                    group.append(effect_entry(effects_all, rng.choice(debuff_effects)))
                effects.append(group)
            relics.append({
                'id': next_id, 'itemId': item_id, 'itemKey': item['key'],
                'itemNameEn': item['name_en'], 'itemNameJa': item['name_ja'],
                'itemColor': item['color'], 'itemType': item_type,
                'effects': effects, 'sortKey': 0,
            })
            next_id += 1
    for i, r in enumerate(relics):
        r['sortKey'] = len(relics) - i
    return {'characterName': 'Synthetic', 'totalRelics': len(relics), 'relics': relics}


def common_keys(pool, item_types, n, skip=0):
    """Most frequent main-effect keys among the given relic types (deterministic)."""
    counts = {}
    for r in pool['relics']:
        if r['itemType'] in item_types:
            for g in r['effects']:
                counts[g[0]['key']] = counts.get(g[0]['key'], 0) + 1
    ranked = sorted(counts, key=lambda k: (-counts[k], k))
    return ranked[skip:skip + n]


def gui_effect_specs(selected):
    """Effect specs as the GUI posts them to the worker (collectOptimizerParams in app.js):
    rank = order within each priority, exclude_* -> {priority, exclude: True}."""
    specs, rank_counters = [], {}
    for key, priority in selected:
        rank = rank_counters.get(priority, 0)
        rank_counters[priority] = rank + 1
        if priority.startswith('exclude_'):
            specs.append({'key': key, 'priority': priority[len('exclude_'):], 'exclude': True, 'rank': rank})
        else:
            specs.append({'key': key, 'priority': priority, 'rank': rank})
    return specs


def generate_scenarios(pool):
    normal_keys = common_keys(pool, ('Relic',), 8)
    deep_keys = common_keys(pool, ('DeepRelic',), 6, skip=2)
    debuff_keys = sorted({g[1]['key'] for r in pool['relics'] for g in r['effects'] if len(g) > 1})
    pri = ['required', 'required', 'preferred', 'preferred', 'nice_to_have', 'nice_to_have']
    # Deep effect whose every occurrence carries a debuff (fewest occurrences first)
    debuffs_by_key = {}
    for r in pool['relics']:
        for g in r['effects']:
            debuffs_by_key.setdefault(g[0]['key'], []).append(g[1]['key'] if len(g) > 1 else None)
    forced_key = min((k for k, ds in debuffs_by_key.items() if all(ds)),
                     key=lambda k: (len(debuffs_by_key[k]), k))
    forced_debuffs = sorted(set(debuffs_by_key[forced_key]))
    return [
        {'name': 'wylder_combined_all_vessels',
         'params': {'character': '追跡者', 'combined': True, 'candidates': 30, 'top': 10},
         'effects': gui_effect_specs(zip(normal_keys[:3] + deep_keys[:3], pri))},
        {'name': 'executor_combined_with_exclusions',
         'params': {'character': '執行者', 'combined': True, 'candidates': 30, 'top': 10},
         'effects': gui_effect_specs(list(zip(normal_keys[2:5] + deep_keys[1:3], pri))
                                     + [(debuff_keys[0], 'exclude_required'),
                                        (debuff_keys[1], 'exclude_preferred'),
                                        (debuff_keys[2], 'exclude_preferred'),
                                        (normal_keys[7], 'exclude_nice_to_have')])},
        {'name': 'guardian_normal_only',
         'params': {'character': '守護者', 'combined': False, 'candidates': 30, 'top': 10},
         'effects': gui_effect_specs(zip(normal_keys[1:7], pri))},
        # Required effect only available on relics carrying excluded debuffs -> penalty applied
        {'name': 'revenant_combined_forced_exclusion',
         'params': {'character': '復讐者', 'combined': True, 'candidates': 30, 'top': 10},
         'effects': gui_effect_specs([(forced_key, 'required'), (normal_keys[0], 'preferred')]
                                     + [(d, 'exclude_preferred') for d in forced_debuffs])},
        {'name': 'scholar_combined_single_vessel_small',
         'params': {'character': '学者', 'vessel': 'urn', 'combined': True, 'candidates': 15, 'top': 5},
         'effects': gui_effect_specs((k, 'preferred') for k in normal_keys[:2] + deep_keys[:2])},
    ]


def run_python_optimizer(pool_path, scenario):
    tmp = tempfile.mkdtemp()
    spec_path = os.path.join(tmp, 'specs.json')
    out_path = os.path.join(tmp, 'out.json')
    with open(spec_path, 'w', encoding='utf-8') as f:
        json.dump({'effects': scenario['effects']}, f, ensure_ascii=False)
    p = scenario['params']
    args = [sys.executable, os.path.join(ROOT_DIR, 'src', 'relic_optimizer.py'),
            '--input', pool_path, '--effects', spec_path, '-o', out_path,
            '--character', p['character'], '--top', str(p['top']), '--candidates', str(p['candidates'])]
    if p.get('vessel'):
        args += ['--vessel', p['vessel']]
    if p['combined']:
        args.append('--combined')
    subprocess.run(args, check=True, capture_output=True)
    return load_json(out_path)


def normalize_optimizer_output(output):
    """Results only, comparable across Python/JS (vessel metadata reduced to its key)."""
    def norm(res):
        r = dict(res)
        if r.get('vessel'):
            r['vessel'] = r['vessel'].get('key')
        return r
    results = [norm(r) for g in output.get('allResults', []) for r in g['results']]
    best = output.get('bestResult')
    return {'best': norm(best['result']) if best else None, 'results': results}


def generate_optimizer_fixtures(items_all, effects_all):
    pool = generate_relic_pool(items_all, effects_all)
    write_json('relic_pool.json', pool)
    scenarios = generate_scenarios(pool)
    write_json('optimizer_scenarios.json', scenarios)

    pool_path = os.path.join(FIXTURES_DIR, 'relic_pool.json')
    expected = {}
    for sc in scenarios:
        expected[sc['name']] = normalize_optimizer_output(run_python_optimizer(pool_path, sc))
        res = expected[sc['name']]['results']
        print(f"optimizer {sc['name']}: {len(res)} results, best score "
              f"{res[0]['score'] if res else '-'} (requiredMet {res[0]['requiredMet'] if res else '-'})")
    write_json('optimizer_expected.json', expected)


def main():
    items_all = load_json(os.path.join(RESOURCES_DIR, 'items_data.json'))['items']
    effects_all = load_json(os.path.join(RESOURCES_DIR, 'effects_data.json'))['effects']
    assert str(ITEM_UNKNOWN) not in items_all and str(EFFECT_UNKNOWN) not in effects_all
    generate_parser_fixtures(items_all, effects_all)
    generate_optimizer_fixtures(items_all, effects_all)


if __name__ == '__main__':
    main()
