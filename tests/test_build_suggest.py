"""ビルド提案（試験的）のデータ resources/build_suggest.json が元データから作り直した結果と一致すること

元データ（tools/build_suggest/research/）や effects_data.json を直したら
python tools/build_suggest/build_data.py と python tools/build_suggest/catalog.py で作り直す。
"""

import os
import subprocess
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestBuildSuggestData(unittest.TestCase):

    def test_up_to_date(self):
        result = subprocess.run([sys.executable, os.path.join(ROOT_DIR, 'tools', 'build_suggest', 'build_data.py'), '--check'],
                                capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_catalog_up_to_date(self):
        # 付録のカタログ（tools/build_suggest/catalog/*.md）も作り直し忘れを検出する
        result = subprocess.run([sys.executable, os.path.join(ROOT_DIR, 'tools', 'build_suggest', 'catalog.py'), '--check'],
                                capture_output=True, text=True, cwd=ROOT_DIR)
        self.assertEqual(result.returncode, 0, result.stderr)


class TestOwnerNotes(unittest.TestCase):
    """オーナーが確認した事実（research/character_effects.py の OWNER_NOTES）がキャラ図鑑のデータに反映されていること"""

    def test_owner_notes_override_research(self):
        import json
        sys.path.insert(0, os.path.join(ROOT_DIR, 'tools', 'build_suggest', 'research'))
        import character_effects as ce
        with open(os.path.join(ROOT_DIR, 'resources', 'character_profiles.json'), encoding='utf-8') as f:
            profiles = json.load(f)['characters']
        for ch, notes in ce.OWNER_NOTES.items():
            for k, v in notes.get('stats', {}).items():
                self.assertEqual(profiles[ch]['stats'][k], v)
            traits = {t['what']: t['value'] for t in profiles[ch]['traits']}
            for k, v in notes.get('traits', {}).items():
                self.assertEqual(traits[k], v)


if __name__ == '__main__':
    unittest.main()
