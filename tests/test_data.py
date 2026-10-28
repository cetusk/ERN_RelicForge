"""resources/ のゲームデータ (items / effects / vessels) の整合性テスト

ゲームアップデートに合わせてデータを更新した際の記入漏れ・型の誤りを検出する。
"""

import json
import os
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(ROOT_DIR, 'resources')

COLORS = {'Red', 'Blue', 'Yellow', 'Green'}
ITEM_TYPES = {'Relic', 'DeepRelic', 'UniqueRelic', 'Misc'}
STACKABLE_VALUES = (True, False, 'conditional')


def load(name):
    with open(os.path.join(RESOURCES_DIR, name), 'r', encoding='utf-8') as f:
        return json.load(f)


class TestItemsData(unittest.TestCase):

    def test_items(self):
        items = load('items_data.json')['items']
        self.assertTrue(items)
        for item_id, item in items.items():
            with self.subTest(item_id=item_id):
                self.assertTrue(item_id.isdigit())
                self.assertLess(int(item_id), 0x01000000)  # 24-bit field in save data
                for field in ('key', 'name_en', 'name_ja'):
                    self.assertIsInstance(item.get(field), str)
                    self.assertTrue(item[field])
                self.assertIn(item.get('type'), ITEM_TYPES)
                if item['type'] == 'Misc':
                    self.assertIsNone(item.get('color'))
                else:
                    self.assertIn(item.get('color'), COLORS)


class TestEffectsData(unittest.TestCase):

    def test_effects(self):
        effects = load('effects_data.json')['effects']
        self.assertTrue(effects)
        for eff_id, eff in effects.items():
            with self.subTest(effect_id=eff_id):
                self.assertTrue(eff_id.isdigit())
                self.assertLess(int(eff_id), 0x01000000)  # 24-bit limit used by the parser
                for field in ('key', 'name_en', 'name_ja'):
                    self.assertIsInstance(eff.get(field), str)
                    self.assertTrue(eff[field])
                self.assertIn(eff.get('stackable'), STACKABLE_VALUES)
                # stackNotes: short summary shown inline; stackNotesFull: full remarks (optional)
                self.assertIsInstance(eff.get('stackNotes'), str)
                if 'stackNotesFull' in eff:
                    self.assertIsInstance(eff['stackNotesFull'], str)
                    self.assertTrue(eff['stackNotesFull'])
                if 'deepOnly' in eff:
                    self.assertIsInstance(eff['deepOnly'], bool)
                # unreleased: in the game data but not in the current game (never offered to users)
                if 'unreleased' in eff:
                    self.assertIs(eff['unreleased'], True)


class TestVesselsData(unittest.TestCase):

    def test_vessels(self):
        data = load('vessels_data.json')
        slot_colors = COLORS | {'Any'}
        type_keys = {vt['key'] for vt in data['vesselTypes']}
        self.assertTrue(data['characters'])
        for char, info in data['characters'].items():
            for vkey, vessel in info['vessels'].items():
                with self.subTest(character=char, vessel=vkey):
                    self.assertIn(vkey, type_keys)
                    for slots in ('normalSlots', 'deepSlots'):
                        self.assertEqual(len(vessel[slots]), 3)
                        for c in vessel[slots]:
                            self.assertIn(c, slot_colors)
        for vessel in data['universalVessels']:
            with self.subTest(universal=vessel['key']):
                for slots in ('normalSlots', 'deepSlots'):
                    self.assertEqual(len(vessel[slots]), 3)
                    for c in vessel[slots]:
                        self.assertIn(c, slot_colors)


if __name__ == '__main__':
    unittest.main()
