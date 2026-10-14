'use strict';
// JS 版パーサー (web / gui) が Python 版と同じ期待値を返すことのテスト
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const { FIXTURES_DIR, APP_DIRS, loadFixture, loadResource, parseSave } = require('./helpers');

const SAVE = path.join(FIXTURES_DIR, 'synthetic_save.sl2');
const KNOWN_IDS = [0x101, 0x102, 0x103, 0x104].map(n => (0xC0800000 | n) >>> 0);

for (const dir of APP_DIRS) {
  test(`${dir}: synthetic save matches expected output`, () => {
    const result = parseSave(dir, SAVE, loadFixture('items_min.json'), loadFixture('effects_min.json'));
    assert.deepStrictEqual(result, loadFixture('parser_expected.json'));
  });

  test(`${dir}: no unknown relics with resources data`, () => {
    const result = parseSave(dir, SAVE, loadResource('items_data.json'), loadResource('effects_data.json'));
    const known = result.relics.filter(r => KNOWN_IDS.includes(r.id));
    assert.equal(known.length, 4);
    for (const r of known) assert.equal(r.unknown, undefined);
  });
}
