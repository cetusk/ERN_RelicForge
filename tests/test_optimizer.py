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

from generate import normalize_optimizer_output, run_python_optimizer, scenario_pool_path  # noqa: E402


def load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name), 'r', encoding='utf-8') as f:
        return json.load(f)


class TestOptimizerScenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.scenarios = load_fixture('optimizer_scenarios.json')
        cls.expected = load_fixture('optimizer_expected.json')

    def test_scenarios_match_expected(self):
        for sc in self.scenarios:
            with self.subTest(scenario=sc['name']):
                actual = normalize_optimizer_output(run_python_optimizer(scenario_pool_path(sc), sc))
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

    def test_required_met_preferred_over_tied_scores(self):
        # Combos missing a required effect tie on score; all top results must still meet them
        results = self.expected['wylder_normal_stackable_required_tie']['results']
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r['requiredMet'] for r in results))

    def test_forced_exclusion_is_penalized(self):
        sc = next(s for s in self.scenarios if s['name'] == 'revenant_combined_forced_exclusion')
        excluded = {e['key'] for e in sc['effects'] if e.get('exclude')}
        best = self.expected[sc['name']]['best']
        self.assertTrue(best['requiredMet'])
        self.assertTrue(set(best['excludedPresent']) & excluded)

    def test_wasted_duplicate_earns_no_concentration_bonus(self):
        # A non-stackable effect on two relics works once; the extra copy must not earn the
        # concentration bonus (it made A+B+D beat A+C+D before, see generate_nonstack_dup_pool)
        results = self.expected['wylder_normal_nonstack_duplicate']['results']
        ids = [sorted(r['id'] - 0xC0820001 for r in res['relics']) for res in results]
        self.assertEqual(ids[0], [0, 2, 3])          # A + C + D
        self.assertEqual(results[0]['score'], 161)
        self.assertEqual(ids[1], [0, 1, 3])          # A + B + D: B's X is a wasted copy
        self.assertEqual(results[1]['score'], 156)


    def test_leftmost_only_effects_follow_the_slot_order(self):
        # A skill change works only from the leftmost relic (see generate_leftmost_pool)
        results = self.expected['wylder_normal_leftmost_skill']['results']
        name = 'ABDCE'
        order = lambda res: ''.join(name[r['id'] - 0xC0830001] for r in res['relics'])
        urn = [r for r in results if r['vessel'] == 'urn']
        sealed = [r for r in results if r['vessel'] == 'sealedUrn']
        # Urn (Red, Red, Blue): A is placed left of B, B's and C's skill changes do not work
        self.assertEqual((order(urn[0]), urn[0]['score'], urn[0]['requiredMet']), ('ABC', 135, True))
        self.assertEqual([[e.get('inactive', False) for e in r['effects']] for r in urn[0]['relics']],
                         [[False, False], [True, False], [True, False]])
        # Sealed Urn (Blue, Red, Red): the blue relic is leftmost, so C's skill change overrides A's
        self.assertEqual((order(sealed[0]), sealed[0]['score'], sealed[0]['requiredMet']), ('EAB', 126, True))
        for r in sealed:
            if 'C' in order(r) and 'A' in order(r):
                self.assertFalse(r['requiredMet'])
                self.assertTrue(r['relics'][1]['effects'][0]['inactive'])


class TestLeftmostSharedGroup(unittest.TestCase):
    """復讐者は戦技の変更と祈祷の変更が同時に効かない（最も左のものだけ）。ほかのキャラは別々に効く"""

    def test_revenant_skill_and_incantation_changes_share_the_leftmost_rule(self):
        from relic_optimizer import RelicOptimizer, load_leftmost_data, load_stacking_data
        path = os.path.join(os.path.dirname(TESTS_DIR), 'resources', 'effects_data.json')
        with open(path, encoding='utf-8') as f:
            effects = json.load(f)['effects']
        pick = lambda group: next(e for i, e in sorted(effects.items())
                                  if e.get('leftmost') == group and not e.get('unreleased') and not e.get('deepOnly'))
        skill, spell = pick('skill'), pick('spell')
        plain = next(e for i, e in sorted(effects.items()) if int(i) >= 7000000 and not e.get('leftmost')
                     and not e.get('unreleased') and not e.get('deepOnly') and '【' not in e['name_ja'])
        relic = lambda rid, color, eff: {
            'id': rid, 'itemKey': 'r', 'itemColor': color, 'itemType': 'Relic',
            'effects': [[{'key': eff['key'], 'name_ja': eff['name_ja'], 'name_en': eff['name_en']}]]}
        relics = [relic(1, 'Red', skill), relic(2, 'Red', spell), relic(3, 'Blue', plain)]
        specs = [{'key': e['key'], 'priority': 'preferred'} for e in (skill, spell, plain)]
        for character, score in (('追跡者', 30), ('復讐者', 20)):
            opt = RelicOptimizer(relics, specs, None, load_stacking_data(path), load_leftmost_data(path))
            best = opt.optimize_combined(['Red', 'Red', 'Blue'], [], deep_types=[], character=character, top_n=1)[0]
            self.assertEqual(best['score'], score, character)
            self.assertEqual(len(best['inactive']), 0 if character == '追跡者' else 1, character)
        # one optimizer for both characters: the second run must not reuse the first one's phase combos
        opt = RelicOptimizer(relics, specs, None, load_stacking_data(path), load_leftmost_data(path))
        scores = [opt.optimize_combined(['Red', 'Red', 'Blue'], [], deep_types=[], character=c, top_n=1)[0]['score']
                  for c in ('追跡者', '復讐者')]
        self.assertEqual(scores, [30, 20])


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
