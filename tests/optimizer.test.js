'use strict';
// JS 版オプティマイザ (web / gui) が Python 版と同じ期待値を返すことのテスト
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('vm');
const { APP_DIRS, loadFixture, loadResource, runOptimizer, runScripts, normalizeOptimizerOutput } = require('./helpers');

const scenarios = loadFixture('optimizer_scenarios.json');
const expected = loadFixture('optimizer_expected.json');

for (const dir of APP_DIRS) {
  for (const sc of scenarios) {
    test(`${dir}: ${sc.name}`, () => {
      const pool = loadFixture(sc.pool || 'relic_pool.json');
      const output = runOptimizer(dir, pool.relics, sc);
      assert.deepStrictEqual(normalizeOptimizerOutput(output), expected[sc.name]);
    });
  }
}

// 復讐者 cannot change the skill and the incantation at the same time (only the leftmost works);
// for other characters they are separate (same check as test_optimizer.py)
for (const dir of APP_DIRS) {
  test(`${dir}: 復讐者 skill and incantation changes share the leftmost rule`, () => {
    const effects = Object.entries(loadResource('effects_data.json').effects).sort(([a], [b]) => (a < b ? -1 : 1));
    const pick = (group) => effects.find(([, e]) => e.leftmost === group && !e.unreleased && !e.deepOnly)[1];
    const skill = pick('skill'), spell = pick('spell');
    const plain = effects.find(([i, e]) => Number(i) >= 7000000 && !e.leftmost && !e.unreleased && !e.deepOnly
      && !e.name_ja.includes('【'))[1];
    const relic = (id, color, e) => ({ id, itemKey: 'r', itemColor: color, itemType: 'Relic',
      effects: [[{ key: e.key, name_ja: e.name_ja, name_en: e.name_en }]] });
    const specs = [skill, spell, plain].map(e => ({ key: e.key, priority: 'preferred' }));
    // urn normal slots: 追跡者 Red, Red, Blue / 復讐者 Blue, Blue, Yellow
    for (const [character, two, one, score, inactive] of [['追跡者', 'Red', 'Blue', 30, 0], ['復讐者', 'Blue', 'Yellow', 20, 1]]) {
      const relics = [relic(1, two, skill), relic(2, two, spell), relic(3, one, plain)];
      const out = runOptimizer(dir, relics, { effects: specs, params: { character, vessel: 'urn', combined: false, candidates: 30, top: 1 } });
      const best = out.bestResult.result;
      assert.equal(best.score, score, character);
      assert.equal(best.relics.flatMap(r => r.effects).filter(e => e.inactive).length, inactive, character);
    }
  });
}

// The same optimizer run for another character must not reuse the first character's phase combos
// (the leftmost groups differ: 復讐者 shares skill and incantation changes)
for (const dir of APP_DIRS) {
  test(`${dir}: one optimizer, two characters: 復讐者 after 追跡者 keeps the 復讐者 rule`, () => {
    const effectsData = loadResource('effects_data.json');
    const effects = Object.entries(effectsData.effects).sort(([a], [b]) => (a < b ? -1 : 1));
    const pick = (group) => effects.find(([, e]) => e.leftmost === group && !e.unreleased && !e.deepOnly)[1];
    const relic = (id, color, e) => ({ id, itemKey: 'r', itemColor: color, itemType: 'Relic',
      effects: [[{ key: e.key, name_ja: e.name_ja, name_en: e.name_en }]] });
    const skill = pick('skill'), spell = pick('spell');
    const plain = effects.find(([i, e]) => Number(i) >= 7000000 && !e.leftmost && !e.unreleased && !e.deepOnly
      && !e.name_ja.includes('【'))[1];
    const relics = [relic(1, 'Blue', skill), relic(2, 'Blue', spell), relic(3, 'Yellow', plain)];
    const ctx = runScripts({ self: {}, console }, dir, ['relic-optimizer.js']);
    ctx.__a = [relics, [skill, spell, plain].map(e => ({ key: e.key, priority: 'preferred' })), loadResource('vessels_data.json'),
      vm.runInContext('loadStackingData', ctx)(effectsData), vm.runInContext('loadLeftmostData', ctx)(effectsData)];
    const opt = vm.runInContext('new RelicOptimizer(...__a)', ctx);
    const best = (character) => opt.optimizeCombined(['Blue', 'Blue', 'Yellow'], [], { deepTypes: [], character, topN: 1 })[0].score;
    const wylder = best('追跡者');
    const revenant = best('復讐者');
    assert.deepEqual([wylder, revenant], [30, 20], '追跡者 counts both changes, 復讐者 only the leftmost');
  });
}
