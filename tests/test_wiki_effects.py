"""tools/wiki_effects（Wiki 照合ツール）のテスト

小さな Wiki 風 HTML で、表の解析（結合セル）と照合・更新案のルールを確認する。
"""

import os
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, 'tools', 'wiki_effects'))

import match  # noqa: E402
import wiki   # noqa: E402

HTML = '''
<h2>遺物に付与される効果</h2>
<h3>攻撃力</h3>
<table>
<tr><th>効果</th><th>重ね掛け</th><th>備考</th></tr>
<tr><td>物理攻撃力上昇+0~2</td><td rowspan="2">◯</td><td>+4%/+5%/+6%/<br>魔術にも効果あり(下記参照)</td></tr>
<tr><td>魔力攻撃力上昇+0~2</td><td>+4%/+5%/+6%/</td></tr>
<tr><td>物理カット率上昇</td><td>－</td><td>約8%カット</td></tr>
<tr><td>ガード成功時、HPを回復</td><td>✕</td><td>固定+15<br>下部を参照</td></tr>
</table>
<h3>スキル／アーツ</h3>
<table>
<tr><th>効果</th><th>重ね掛け</th><th>備考</th></tr>
<tr><td>スキルクールタイム軽減+1~3</td><td>◯</td><td>スキルクールタイムを（5%/7.5%/10%）ほど軽減する</td></tr>
</table>
<h3>キャラクター固有</h3>
<table>
<tr><th>キャラ</th><th>効果</th><th>備考</th></tr>
<tr><td>追跡者</td><td>スキルの使用回数+1</td><td>リチャージは一回分ずつ</td></tr>
</table>
<h2>深層の遺物に付与される効果</h2>
<h3>攻撃力</h3>
<table>
<tr><th>効果</th><th>重ね掛け</th><th>デメリット</th><th>備考</th></tr>
<tr><td>毒状態の敵に対する攻撃を強化 +0~2</td><td>※</td><td>+1以上</td><td>+10%/+16%/+20%<hr>※+値が違えば重ね掛け可</td></tr>
<tr><td>物理カット率上昇</td><td>◯</td><td>無し</td><td>既存効果</td></tr>
</table>
'''


def entry(name, stackable='conditional', notes=''):
    return {'key': 'k', 'name_ja': name, 'name_en': name, 'stackable': stackable, 'stackNotes': notes}


class TestWikiParse(unittest.TestCase):

    def setUp(self):
        self.rows = wiki.parse_effect_rows(HTML)
        self.by = {(r['deep'], r['name']): r for r in self.rows}

    def test_rowspan_is_expanded(self):
        self.assertEqual(self.by[(False, '魔力攻撃力上昇+0~2')]['stack'], '◯')
        self.assertEqual(self.by[(False, '魔力攻撃力上昇+0~2')]['notes'], '+4%/+5%/+6%/')

    def test_sections_and_character_table(self):
        self.assertEqual(self.by[(False, '【追跡者】スキルの使用回数+1')]['stack'], '✕(固有)')
        self.assertTrue(self.by[(True, '毒状態の敵に対する攻撃を強化 +0~2')]['deep'])

    def test_cell_separators_become_lines(self):
        self.assertIn('\n', self.by[(True, '毒状態の敵に対する攻撃を強化 +0~2')]['notes'])


class TestProposal(unittest.TestCase):

    def setUp(self):
        self.m = match.Matcher(wiki.parse_effect_rows(HTML))

    def p(self, eid, name, **kw):
        return match.propose(eid, entry(name, **kw), self.m)

    def test_level_values_and_full_text(self):
        p = self.p(7001401, '物理攻撃力上昇+1')
        self.assertEqual((p['prop_stack'], p['prop_short']), (True, '+5%'))
        self.assertEqual(p['prop_notes'], '+4%/+5%/+6%/ / 魔術にも効果あり')   # "(下記参照)" removed
        self.assertEqual(self.p(7001400, '物理攻撃力上昇')['prop_short'], '+4%')

    def test_parenthesized_level_values(self):
        self.assertEqual(self.p(7000801, 'スキルクールタイム軽減+2')['prop_short'], '約7.5%軽減')

    def test_same_key_not_stacking_when_only_different_values_stack(self):
        p = self.p(6260000, '毒状態の敵に対する攻撃を強化+1')
        self.assertEqual((p['prop_stack'], p['prop_short']), (False, '+16%'))

    def test_unverified_keeps_value_and_notes_it(self):
        p = self.p(7006200, '物理カット率上昇', stackable='conditional', notes='約8%')
        self.assertEqual(p['prop_stack'], 'conditional')
        self.assertEqual(p['prop_short'], '約8%（重複は未検証）')
        self.assertTrue(p['prop_notes'].startswith('重ね掛けの可否は Wiki で未検証'))
        # Re-running on the applied value must not add the note twice
        again = self.p(7006200, '物理カット率上昇', stackable='conditional', notes=p['prop_short'])
        self.assertEqual(again['prop_short'], '約8%（重複は未検証）')

    def test_deep_row_uses_deep_section_and_existing_effect_notes(self):
        p = self.p(6006200, '物理カット率上昇')   # deep ID -> deep row "既存効果" -> normal notes
        self.assertEqual(p['prop_stack'], True)
        self.assertEqual(p['prop_notes'], '約8%カット')

    def test_alias_and_reference_cleanup(self):
        p = self.p(7036100, 'ガード成功時、HP回復')   # data name differs from wiki name
        self.assertEqual(p['how'], 'alias')
        self.assertEqual((p['prop_stack'], p['prop_notes']), (False, '固定+15'))

    def test_section_rule_and_unmatched(self):
        p = self.p(7124300, '出撃時の武器の戦技を「我慢」にする')
        self.assertEqual((p['how'], p['prop_stack'], p['prop_short']),
                         ('section-rule', False, '献器の最も左の遺物の効果のみ発動'))
        none = self.p(7999999, '存在しない効果', notes='そのまま')
        self.assertEqual((none['how'], none['prop_short']), ('none', 'そのまま'))
        e = entry('存在しない効果', notes='そのまま')
        self.assertFalse(match.apply_proposal(e, none))


if __name__ == '__main__':
    unittest.main()
