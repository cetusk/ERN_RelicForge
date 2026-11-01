'use strict';
// ビルド提案（試験的）: 変換ルールのデータ (resources/build_suggest.json) と relic-suggest.js のテスト
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('vm');
const { APP_DIRS, loadResource, runScripts } = require('./helpers');

const data = loadResource('build_suggest.json');
const effectsData = loadResource('effects_data.json');
const vessels = loadResource('vessels_data.json');

function suggestContext(dir) {
  return runScripts({}, dir, ['relic-suggest.js']);
}

// Plain JSON out of the vm realm (deepStrictEqual compares prototypes)
function suggest(ctx, input) {
  ctx.__args = [data, input, vm.runInContext('suggestEffectInfo', ctx)(effectsData)];
  return JSON.parse(JSON.stringify(vm.runInContext('suggestConditions(...__args)', ctx)));
}

test('build_suggest.json: every effect exists on relics and none is unreleased', () => {
  const byKey = {};
  for (const [id, e] of Object.entries(effectsData.effects)) {
    const n = Number(id);
    if (n < 200000 || (n >= 6000000 && n < 7400000)) (byKey[e.key] = byKey[e.key] || []).push(e);
  }
  const check = (keys, where) => {
    for (const k of keys) {
      assert.ok(byKey[k], `${where}: unknown effect ${k}`);
      assert.ok(!byKey[k].every((e) => e.unreleased), `${where}: unreleased effect ${k}`);
    }
  };
  for (const t of data.types) for (const tier of ['core', 'good', 'opt', 'avoid']) check(t[tier], `型 ${t.id}`);
  for (const b of data.builds) for (const tier of ['must', 'rec', 'opt', 'avoid']) check(b[tier], `ビルド ${b.id}`);
  for (const [c, s] of Object.entries(data.staples)) for (const tier of ['rec', 'opt', 'avoid']) check(s[tier], `${c} の定番`);
  for (const w of data.weapons) check([...w.attack, ...w.three, ...w.find], `武器種 ${w.id}`);
  check([...data.generic.offense, ...data.generic.survival], 'つまみ');
  for (const b of data.builds) assert.ok(vessels.characters[b.character], `ビルド ${b.id}: unknown character`);
  assert.deepEqual(Object.keys(data.favoredWeapons).sort(), Object.keys(vessels.characters).sort(), 'favoured weapons for every character');
  for (const ws of Object.values(data.favoredWeapons)) for (const w of ws) assert.ok(data.weapons.some((x) => x.id === w), w);
  for (const p of Object.values(data.modePreference)) check([...p.first, ...p.second], 'モード');
  for (const [c, r] of Object.entries(data.characters)) {
    assert.ok(vessels.characters[c], c);
    check([...r.avoid, ...r.useless].map((x) => x.key), `${c} の評価`);
    for (const x of r.avoid) assert.ok(['preferred', 'nice_to_have'].includes(x.priority) && x.why, `${c} ${x.key}`);
  }
  assert.ok(data.types.every((t) => ['style', 'magic', 'status', 'role'].includes(t.axis)));
});

for (const dir of APP_DIRS) {
  test(`${dir}: types, weapons and the slider map to the agreed priorities`, () => {
    const ctx = suggestContext(dir);
    const r = suggest(ctx, { character: '追跡者', mode: 'combined', types: ['バッタ'], weapons: ['大剣'], focus: -2 });
    const pr = Object.fromEntries(r.effects.map((e) => [e.key, e]));
    const batta = data.types.find((t) => t.id === 'バッタ');
    for (const k of batta.core) assert.equal(pr[k].priority, 'preferred', k);
    assert.equal(pr.improvedGreatswordAttackPower.priority, 'preferred');                         // 大剣の攻撃力上昇
    assert.equal(pr.improvedAttackPowerWith3PlusGreatswordsEquipped.priority, 'nice_to_have');    // 3つ以上装備
    for (const k of data.generic.offense) assert.equal(pr[k].exclude, false, k);                  // 火力側に最大
    assert.ok(!r.effects.some((e) => data.generic.survival.includes(e.key) && !batta.core.includes(e.key)
      && !batta.good.includes(e.key) && !batta.opt.includes(e.key) && !data.staples['追跡者'].rec.includes(e.key)
      && !data.staples['追跡者'].opt.includes(e.key)), 'focus -2 adds no generic survival effects');
    assert.ok(r.notOnRelics.some((n) => n.name === '攻撃連続時、カット率上昇'));                // 付帯効果は注記のみ
    // rank order: required < preferred < nice_to_have < excluded
    const levels = r.effects.map((e) => (e.exclude ? 3 : ['required', 'preferred', 'nice_to_have'].indexOf(e.priority)));
    assert.deepEqual(levels, [...levels].sort((a, b) => a - b));
  });

  test(`${dir}: weapon-type effects of a type are used only for the picked weapon types`, () => {
    const ctx = suggestContext(dir);
    const weaponOf = new Map();
    for (const w of data.weapons) for (const k of [...w.attack, ...w.three, ...w.find]) weaponOf.set(k, w.id);
    const none = suggest(ctx, { character: '追跡者', mode: 'combined', types: ['バッタ', '大型武器・タメ'], weapons: [], focus: 0 });
    assert.deepEqual(none.effects.filter((e) => weaponOf.has(e.key)).map((e) => e.key), []);
    const great = suggest(ctx, { character: '追跡者', mode: 'combined', types: ['バッタ', '大型武器・タメ'], weapons: ['大剣'], focus: 0 });
    const used = new Set(great.effects.filter((e) => weaponOf.has(e.key)).map((e) => weaponOf.get(e.key)));
    assert.deepEqual([...used], ['大剣']);
  });

  test(`${dir}: 「見つけやすくなる」 is preferred only for a type the character does not find often, and only one`, () => {
    const ctx = suggestContext(dir);
    const find = (w) => data.weapons.find((x) => x.id === w).find[0];
    const pr = (input) => Object.fromEntries(suggest(ctx, input).effects.map((e) => [e.key, e.priority]));
    const base = { character: '追跡者', mode: 'combined', types: [], focus: 0 };
    assert.equal(pr({ ...base, weapons: ['大剣'] })[find('大剣')], undefined, 'favoured type: no effect');
    assert.equal(pr({ ...base, weapons: ['刀'] })[find('刀')], 'preferred');
    const two = pr({ ...base, weapons: ['大剣', '鎌', '刀'] });
    assert.equal(two[find('鎌')], 'preferred', 'the first picked other type');
    assert.equal(two[find('刀')], 'nice_to_have', 'only one works');
    // 無頼漢 finds three types more often; narrowing them down to one is still useful
    assert.equal(pr({ ...base, character: '無頼漢', weapons: ['大斧'] })[find('大斧')], 'nice_to_have');
    const r = suggest(ctx, { ...base, weapons: ['大剣', '鎌', '刀'] });
    assert.deepEqual(r.notes.filter((n) => n.kind.startsWith('find')).map((n) => n.kind), ['findFavored', 'findReplaces', 'findOnlyOne']);
  });

  test(`${dir}: 封牢 and 夜の侵入者 are ranked by mode (通常のみ = 通常モード, 通常+深層 = 深き夜)`, () => {
    const ctx = suggestContext(dir);
    const evergaol = 'attackPowerPermanentlyIncreasedForEachEvergaolPrisonerDefeated';
    const invader = 'attackPowerUpAfterDefeatingANightInvader';
    for (const [mode, first, second] of [['normal', evergaol, invader], ['combined', invader, evergaol]]) {
      for (const focus of [-2, 0, 2]) {
        const effects = suggest(ctx, { character: '追跡者', mode, types: ['バッタ'], weapons: [], focus }).effects;
        const at = (k) => effects.findIndex((e) => e.key === k);
        assert.ok(at(first) >= 0 && at(first) < at(second), `${mode} ${focus}: ${first} first`);
        assert.equal(effects[at(first)].priority, 'preferred', `${mode} ${focus}`);   // 定番 rec
        assert.equal(effects[at(second)].priority, 'nice_to_have', `${mode} ${focus}`);
      }
    }
  });

  test(`${dir}: per-character evaluations: avoided demerits (body text weighs more) and effects that do not work`, () => {
    const ctx = suggestContext(dir);
    const dodge = 'moreDamageTakenAfterEvasion';   // 回避直後、カット率低下
    assert.ok(data.characters['守護者'].avoid.some((x) => x.key === dodge && x.priority === 'preferred'), 'fixture: 守護者 body text');
    const guardian = suggest(ctx, { character: '守護者', mode: 'combined', types: ['タンク'], weapons: [], focus: 0 });
    const e = guardian.effects.find((x) => x.key === dodge);
    assert.ok(e && e.exclude && e.priority === 'preferred', '守護者 avoids it, with the body-text weight');
    assert.ok(e.reasons.some((r) => r.startsWith('守護者: ')));
    const wylder = suggest(ctx, { character: '追跡者', mode: 'combined', types: ['タンク'], weapons: [], focus: 0 });
    const charReason = (r, c) => r.effects.some((x) => x.key === dodge && x.reasons.some((why) => why.startsWith(`${c}: `)));
    assert.ok(!charReason(wylder, '追跡者') && !charReason(wylder, '守護者'), 'not for a character without the evaluation');
    const normal = suggest(ctx, { character: '守護者', mode: 'normal', types: ['タンク'], weapons: [], focus: 0 });
    assert.ok(!charReason(normal, '守護者'), 'deep demerits only in deep mode');
    // a comment-only evaluation adds the weaker exclusion
    const rc = data.characters['無頼漢'].avoid.find((x) => x.tier === 'comment');
    const raider = suggest(ctx, { character: '無頼漢', mode: 'combined', types: ['タンク'], weapons: [], focus: 0 });
    assert.equal(raider.effects.find((x) => x.key === rc.key).priority, 'nice_to_have');
    // 隠者: skill changes for the starting armament do not work on a staff
    const skillKeys = new Set(data.characters['隠者'].useless.map((x) => x.key));
    const recluse = suggest(ctx, { character: '隠者', mode: 'combined', types: data.types.map((t) => t.id), weapons: [], focus: 0 });
    assert.deepEqual(recluse.effects.filter((x) => skillKeys.has(x.key)).map((x) => x.key), []);
    const other = suggest(ctx, { character: '追跡者', mode: 'combined', types: ['戦技'], weapons: [], focus: 0 });
    assert.ok(other.effects.some((x) => skillKeys.has(x.key)), 'other characters still use them');
  });

  test(`${dir}: a known build makes its defining effects required; staples stay preferred`, () => {
    const ctx = suggestContext(dir);
    const build = data.builds.find((b) => b.character === 'レディ' && b.must.length);
    const r = suggest(ctx, { character: 'レディ', mode: 'combined', buildId: build.id, types: [], weapons: [], focus: 0 });
    const pr = Object.fromEntries(r.effects.map((e) => [e.key, e]));
    for (const k of build.must) assert.equal(pr[k].priority, 'required', k);
    for (const k of data.staples['レディ'].rec) {
      if (!build.must.includes(k)) assert.equal(pr[k].priority, 'preferred', k);
    }
  });

  test(`${dir}: conflicts keep the wanted effect and are reported; unreleased and deep-only rules hold`, () => {
    const ctx = suggestContext(dir);
    const r = suggest(ctx, { character: '執行者', mode: 'combined', types: ['毒', '瓦礫'], weapons: [], focus: 0 });
    const c = r.conflicts.find((x) => x.key === 'poisonBuildupWhenBelowMaxHP');
    assert.ok(c, 'HP最大未満時、毒が蓄積: 瓦礫 wants it, 毒 avoids it');
    assert.ok(c.wantedBy.includes('瓦礫') && c.avoidedBy.includes('毒'));
    assert.equal(r.effects.find((e) => e.key === 'poisonBuildupWhenBelowMaxHP').exclude, false);

    const info = vm.runInContext('suggestEffectInfo', ctx)(effectsData);
    const all = suggest(ctx, { character: '隠者', mode: 'combined', types: data.types.map((t) => t.id), weapons: data.weapons.map((w) => w.id), focus: 0 });
    assert.ok(all.effects.every((e) => !info[e.key].unreleased), 'no unreleased effect');
    const normal = suggest(ctx, { character: '隠者', mode: 'normal', types: data.types.map((t) => t.id), weapons: [], focus: 0 });
    assert.ok(normal.effects.every((e) => !info[e.key].deepOnly), 'normal-only mode drops deep-only effects');
    assert.deepEqual(suggest(ctx, { character: '隠者', types: ['存在しない型'] }).unknown, ['存在しない型']);
    const other = all.effects.filter((e) => info[e.key].character && info[e.key].character !== '隠者');
    assert.deepEqual(other.map((e) => e.key), [], 'no effects for other characters');
    assert.ok(all.effects.some((e) => info[e.key].character === '隠者'), 'own character effects are kept');
  });
}
