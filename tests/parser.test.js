'use strict';
// JS 版パーサー (web / gui) が Python 版と同じ期待値を返すことのテスト
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const fs = require('fs');
const vm = require('vm');
const { FIXTURES_DIR, APP_DIRS, loadFixture, loadResource, parseSave, parserContext } = require('./helpers');

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

for (const dir of APP_DIRS) {
  test(`${dir}: rebuilding from compact (stored / shared) relics gives the same output`, () => {
    const ctx = parserContext(dir);
    const buf = fs.readFileSync(SAVE);
    ctx.__args = [buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.length),
      loadFixture('items_min.json'), loadFixture('effects_min.json')];
    const rebuilt = vm.runInContext(`(() => {
      const [ab, items, effects] = __args;
      const { characterName, relics } = extractRelics(ab, items, effects);
      const compact = JSON.parse(JSON.stringify(compactRelics(relics)));   // as stored
      return buildRelicData(characterName, expandRelics(compact), items, effects);
    })()`, ctx);
    delete rebuilt.file;
    assert.deepStrictEqual(JSON.parse(JSON.stringify(rebuilt)), loadFixture('parser_expected.json'));
  });
}
