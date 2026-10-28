"""ビルド提案（試験的）のデータ resources/build_suggest.json が元データから作り直した結果と一致すること

元データ（tools/build_suggest/research/）や effects_data.json を直したら
python tools/build_suggest/build_data.py で作り直す。
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


if __name__ == '__main__':
    unittest.main()
