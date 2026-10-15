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

  test(`${dir}: QR fountain frames rebuild the link from any frames, despite missed ones`, () => {
    const ctx = shareContext(dir);
    const qrFile = path.join(ROOT_DIR, dir, 'lib', 'qrcode.js');
    vm.runInContext(fs.readFileSync(qrFile, 'utf8'), ctx, { filename: qrFile });
    const result = JSON.parse(vm.runInContext(`JSON.stringify((() => {
      let seed = 12345;
      const random = () => (seed = (Math.imul(seed, 1103515245) + 12345) >>> 0) / 4294967296;
      const bytes = new Uint8Array(9221);   // ~ a 1600-relic link
      for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(random() * 256);
      const token = shareBytesToBase64Url(bytes);
      const sender = createRelicShareQrSender(token);
      const versions = [1, 5, sender.blocks + 3].map(seq => {
        const q = qrcode(0, 'L'); q.addData(sender.frame(seq), 'Byte'); q.make(); return (q.getModuleCount() - 17) / 4;
      });
      // 200 transfers: start anywhere, miss 40% of the frames, see each frame 1-2 times
      const used = [];
      let wrong = 0;
      for (let run = 0; run < 200; run++) {
        const c = new RelicShareQrCollector();
        let seq = 1 + Math.floor(random() * 3 * sender.blocks);
        let scanned = 0;
        for (;;) {
          if (random() < 0.4) { seq++; continue; }
          const r = c.add(sender.frame(seq));
          scanned++;
          if (random() < 0.3) c.add(sender.frame(seq));   // same frame again: no harm
          if (r.state === 'done') { if (r.token !== token) wrong++; break; }
          seq++;
        }
        used.push(scanned);
      }
      used.sort((a, b) => a - b);
      const other = new RelicShareQrCollector();
      const states = [other.add('hello').state, other.add('ERNRF2:zz:5:2:1:AAAA').state, other.add('ERNRF2:zz:10:1:1:AAAA').state];
      const link = new RelicShareQrCollector().add('https://x.example/web/index.html#r=' + token.slice(0, 40));
      return { blocks: sender.blocks, maxVersion: Math.max(...versions), wrong, median: used[100], worst: used[199],
               states, link: [link.state, link.token.length] };
    })())`, ctx));
    assert.equal(result.blocks, 26);
    assert.ok(result.maxVersion <= 15, `QR version ${result.maxVersion}`);
    assert.equal(result.wrong, 0);
    assert.ok(result.median <= result.blocks + 3, `median frames ${result.median}`);
    assert.ok(result.worst <= result.blocks + 12, `worst frames ${result.worst}`);
    assert.deepEqual(result.states, ['ignored', 'progress', 'ignored']);   // last: size does not match the block
    assert.deepEqual(result.link, ['done', 40]);
  });
}
