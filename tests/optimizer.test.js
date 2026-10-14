'use strict';
// JS 版オプティマイザ (web / gui) が Python 版と同じ期待値を返すことのテスト
const test = require('node:test');
const assert = require('node:assert/strict');
const { APP_DIRS, loadFixture, runOptimizer, normalizeOptimizerOutput } = require('./helpers');

const pool = loadFixture('relic_pool.json');
const scenarios = loadFixture('optimizer_scenarios.json');
const expected = loadFixture('optimizer_expected.json');

for (const dir of APP_DIRS) {
  for (const sc of scenarios) {
    test(`${dir}: ${sc.name}`, () => {
      const output = runOptimizer(dir, pool.relics, sc);
      assert.deepStrictEqual(normalizeOptimizerOutput(output, !!sc.unorderedRelics), expected[sc.name]);
    });
  }
}
