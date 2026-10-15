'use strict';
// 共有リンク (relic-share.js) のテスト: 往復で遺物が一致すること、不正な入力を拒否すること
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { ROOT_DIR, FIXTURES_DIR, APP_DIRS, loadFixture, parserContext } = require('./helpers');

function shareContext(dir) {
  const ctx = parserContext(dir);
  Object.assign(ctx, { TextEncoder, Blob, Response, CompressionStream, DecompressionStream, btoa, atob });
  const filename = path.join(ROOT_DIR, dir, 'relic-share.js');
  vm.runInContext(fs.readFileSync(filename, 'utf8'), ctx, { filename });
  return ctx;
}

for (const dir of APP_DIRS) {
  test(`${dir}: share link round trip keeps relics, effects and order`, async () => {
    const ctx = shareContext(dir);
    const buf = fs.readFileSync(path.join(FIXTURES_DIR, 'synthetic_save.sl2'));
    ctx.__args = [buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.length),
      loadFixture('items_min.json'), loadFixture('effects_min.json')];
    const result = await vm.runInContext(`(async () => {
      const [ab, items, effects] = __args;
      const { characterName, relics } = extractRelics(ab, items, effects);
      const original = buildRelicData(characterName, relics, items, effects);
      const token = await encodeRelicShare({ characterName, relics: compactRelics(relics) });
      const url = relicShareUrl(SHARE_PUBLIC_URL, token);
      const shared = await decodeRelicShare(findRelicShareToken('see ' + url + ' !'));
      const rebuilt = buildRelicData(shared.characterName, expandRelics(shared.relics), items, effects);
      const noName = await decodeRelicShare(await encodeRelicShare(
        { characterName, relics: compactRelics(relics) }, { includeName: false }));
      return { original, rebuilt, url, noName: noName.characterName };
    })()`, ctx);
    const strip = d => JSON.parse(JSON.stringify(d.relics.map(r => {
      const { id, sortKey, ...rest } = r;   // IDs / sort keys are renumbered by design
      return rest;
    })));
    assert.deepStrictEqual(strip(result.rebuilt), strip(result.original));
    assert.equal(result.rebuilt.characterName, 'Tester');
    assert.equal(result.rebuilt.unknownRelics, result.original.unknownRelics);
    assert.ok(result.url.startsWith('https://cetusk.github.io/ERN_RelicForge/web/index.html#r='));
    assert.equal(result.noName, '');
  });

  test(`${dir}: malformed share data is rejected`, async () => {
    const ctx = shareContext(dir);
    for (const bad of ['', 'AAAA', 'not-a-token', 'dVc']) {
      ctx.__bad = bad;
      await assert.rejects(vm.runInContext('decodeRelicShare(__bad)', ctx));
    }
    assert.equal(vm.runInContext("findRelicShareToken('https://example.com/page')", ctx), null);
  });
}
