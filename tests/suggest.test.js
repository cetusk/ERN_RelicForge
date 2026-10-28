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
