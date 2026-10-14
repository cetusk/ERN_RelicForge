"""Python 版パーサー (src/relic_parser.py) のテスト

合成セーブファイル (tests/fixtures/synthetic_save.sl2) を CLI で解析し、
期待値 (parser_expected.json) と一致すること、および未知の遺物の扱いを確認する。
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(TESTS_DIR)
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


def run_parser(save_path, items_path, effects_path):
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, 'out.json')
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT_DIR, 'src', 'relic_parser.py'), save_path,
             '-o', out_path, '--items', items_path, '--effects', effects_path],
            capture_output=True, text=True, encoding='utf-8')
        if proc.returncode != 0:
            raise AssertionError(f'relic_parser.py failed:\n{proc.stderr}')
        with open(out_path, 'r', encoding='utf-8') as f:
            return json.load(f), proc.stderr


class TestParserSyntheticSave(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result, cls.stderr = run_parser(
            os.path.join(FIXTURES_DIR, 'synthetic_save.sl2'),
            os.path.join(FIXTURES_DIR, 'items_min.json'),
            os.path.join(FIXTURES_DIR, 'effects_min.json'))
        cls.result.pop('file')
        with open(os.path.join(FIXTURES_DIR, 'parser_expected.json'), 'r', encoding='utf-8') as f:
            cls.expected = json.load(f)
        cls.by_id = {r['id']: r for r in cls.result['relics']}

    def test_matches_expected_output(self):
        self.assertEqual(self.result, self.expected)

    def test_character_name(self):
        self.assertEqual(self.result['characterName'], 'Tester')

    def test_relics_sorted_by_sort_key_desc(self):
        keys = [r['sortKey'] for r in self.result['relics']]
        self.assertEqual(keys, sorted(keys, reverse=True))

    def test_noise_slots_are_ignored(self):
        # 0xC0800201-203: noise / no sort-key record; 0xC0800101 duplicate must not replace the known relic
        ids = set(self.by_id)
        self.assertEqual(ids, {0xC0800000 | n for n in range(0x101, 0x108)})
        self.assertNotIn('unknown', self.by_id[0xC0800101])

    def test_unknown_effect(self):
        relic = self.by_id[0xC0800105]
        self.assertTrue(relic['unknown'])
        eff = relic['effects'][1][0]
        self.assertEqual(eff, {'id': 7999901, 'key': 'unknownEffect_7999901',
                               'name_en': 'Unknown Effect (ID: 7999901)',
                               'name_ja': '未知の効果 (ID: 7999901)', 'unknown': True})

    def test_unknown_item(self):
        relic = self.by_id[0xC0800106]
        self.assertTrue(relic['unknown'])
        self.assertEqual(relic['itemNameJa'], '未知の遺物 (ID: 99001)')
        self.assertIsNone(relic['itemColor'])
        self.assertIsNone(relic['itemType'])
        self.assertIsNone(relic['coordinates'])
        self.assertIsNone(relic['coordinatesByColor'])

    def test_unknown_debuff_only(self):
        relic = self.by_id[0xC0800107]
        self.assertTrue(relic['unknown'])
        self.assertTrue(relic['effects'][0][1]['unknown'])
        self.assertNotIn('unknown', relic['effects'][0][0])

    def test_unknown_count_and_warning(self):
        self.assertEqual(self.result['unknownRelics'], 3)
        self.assertEqual(sum(1 for r in self.result['relics'] if r.get('unknown')), 3)
        self.assertIn('Warning: 3 relics', self.stderr)

    def test_known_relics_have_no_unknown_flags(self):
        for rid in (0xC0800101, 0xC0800102, 0xC0800103, 0xC0800104):
            relic = self.by_id[rid]
            self.assertNotIn('unknown', relic)
            for group in relic['effects']:
                for eff in group:
                    self.assertNotIn('unknown', eff)

    def test_unknown_item_does_not_shift_coordinates(self):
        # Normal relics in sort order: 0x104, 0x101, (0x106 unknown), 0x102, 0x105, 0x107
        coords = [self.by_id[0xC0800000 | n]['coordinates'] for n in (0x104, 0x101, 0x102, 0x105, 0x107)]
        self.assertEqual(coords, [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]])


class TestParserWithFullData(unittest.TestCase):
    """resources/ の実データで解析しても未知扱いにならないこと"""

    def test_no_unknown_with_resources_data(self):
        result, _ = run_parser(
            os.path.join(FIXTURES_DIR, 'synthetic_save.sl2'),
            os.path.join(ROOT_DIR, 'resources', 'items_data.json'),
            os.path.join(ROOT_DIR, 'resources', 'effects_data.json'))
        known = [r for r in result['relics'] if r['id'] in {0xC0800000 | n for n in range(0x101, 0x105)}]
        self.assertEqual(len(known), 4)
        for r in known:
            self.assertNotIn('unknown', r)


if __name__ == '__main__':
    unittest.main()
