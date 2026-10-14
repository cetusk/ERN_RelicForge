"""Python 版オプティマイザ (src/relic_optimizer.py) のテスト

tests/fixtures/relic_pool.json に対して各シナリオを CLI で実行し、
期待値 (optimizer_expected.json) と一致することを確認する。
"""

import json
import os
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')
sys.path.insert(0, FIXTURES_DIR)
sys.path.insert(0, os.path.join(os.path.dirname(TESTS_DIR), 'src'))

from generate import normalize_optimizer_output, run_python_optimizer  # noqa: E402


def load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name), 'r', encoding='utf-8') as f:
        return json.load(f)


class TestOptimizerScenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.scenarios = load_fixture('optimizer_scenarios.json')
        cls.expected = load_fixture('optimizer_expected.json')
        cls.pool_path = os.path.join(FIXTURES_DIR, 'relic_pool.json')

    def test_scenarios_match_expected(self):
        for sc in self.scenarios:
            with self.subTest(scenario=sc['name']):
                actual = normalize_optimizer_output(
                    run_python_optimizer(self.pool_path, sc), sc.get('unorderedRelics', False))
                self.assertEqual(actual, self.expected[sc['name']])

    def test_results_are_ranked(self):
        for name, exp in self.expected.items():
            with self.subTest(scenario=name):
                # allResults is grouped by vessel, so order by rank first
                results = sorted(exp['results'], key=lambda r: r['rank'])
                self.assertTrue(results, 'scenario should produce results')
                self.assertEqual([r['rank'] for r in results], list(range(1, len(results) + 1)))
                keys = [(not r['requiredMet'], -r['score']) for r in results]
                self.assertEqual(keys, sorted(keys))
                self.assertEqual(exp['best'], results[0])

    def test_exclude_required_never_in_required_met_results(self):
        sc = next(s for s in self.scenarios if s['name'] == 'executor_combined_with_exclusions')
        excl_required = {e['key'] for e in sc['effects'] if e.get('exclude') and e['priority'] == 'required'}
        self.assertTrue(excl_required)
        for r in self.expected[sc['name']]['results']:
            if r['requiredMet']:
                self.assertFalse(excl_required & set(r['excludedPresent']))

    def test_forced_exclusion_is_penalized(self):
        sc = next(s for s in self.scenarios if s['name'] == 'revenant_combined_forced_exclusion')
        excluded = {e['key'] for e in sc['effects'] if e.get('exclude')}
        best = self.expected[sc['name']]['best']
        self.assertTrue(best['requiredMet'])
        self.assertTrue(set(best['excludedPresent']) & excluded)


class TestEffectsConfigLoader(unittest.TestCase):
    """README 形式の除外指定 (exclude_required 等) を GUI と同じ形式に変換すること"""

    def test_exclude_priorities_are_converted(self):
        from relic_optimizer import load_effects_config
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'specs.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'effects': [
                    {'key': 'a', 'priority': 'required'},
                    {'key': 'b', 'priority': 'exclude_required'},
                    {'key': 'c', 'priority': 'exclude_preferred'},
                    {'key': 'd', 'priority': 'exclude_nice_to_have'},
                ]}, f)
            specs = load_effects_config(path)
        self.assertEqual(specs, [
            {'key': 'a', 'priority': 'required'},
            {'key': 'b', 'priority': 'required', 'exclude': True},
            {'key': 'c', 'priority': 'preferred', 'exclude': True},
            {'key': 'd', 'priority': 'nice_to_have', 'exclude': True},
        ])

if __name__ == '__main__':
    unittest.main()
