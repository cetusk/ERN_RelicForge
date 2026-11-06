'use strict';
// キャラ図鑑 (relic-guide.js): every character renders from the shipped data, with its builds and no unreleased effect
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('vm');
const { APP_DIRS, loadResource, runScripts } = require('./helpers');

const profiles = loadResource('character_profiles.json');
const suggest = loadResource('build_suggest.json');
const effects = loadResource('effects_data.json').effects;
const names = {};
for (const e of Object.values(effects)) if (!(e.key in names)) names[e.key] = e.name_ja;
const unreleasedNames = Object.values(effects).filter((e) => e.unreleased).map((e) => e.name_ja);

for (const dir of APP_DIRS) {
  test(`${dir}: キャラ図鑑 renders every character`, () => {
    const ctx = runScripts({}, dir, ['relic-guide.js']);
    assert.deepEqual(Object.keys(profiles.characters).sort(), Object.keys(suggest.staples).sort());
    for (const ch of Object.keys(profiles.characters)) {
      ctx.__o = { character: ch, profiles, suggest, ja: true, effectName: (k) => names[k] || k };
      const html = vm.runInContext('renderCharacterGuide(__o)', ctx);
      const builds = suggest.builds.filter((b) => b.character === ch);
      assert.equal((html.match(/class="guide-build"/g) || []).length, builds.length, ch);
      assert.ok(html.includes(`aria-pressed="true">${ch}<`), `${ch} is selected`);
      // 基本データ charts: 8 rank bars, 3 Lv15 bars, dodge, 5 negation bars, 7 resistance rows
      assert.ok(html.includes('class="gf-grid"'), `${ch} has the comparison charts`);
      assert.ok((html.match(/class="gf-row"/g) || []).length >= 8 + 3 + 1 + 5 + 7, `${ch} chart rows`);
      assert.ok(!/NaN|undefined|Infinity/.test(html), `${ch}: no broken numbers`);
      // 特性: the same 8 items for every character, one in each of the four groups at least
      assert.deepEqual(profiles.characters[ch].traits.map((t) => t.what.split('：')[0]),
        ['能力値の特徴', '回避', '耐久', 'アビリティ', 'スキル', 'アーツ', '立ち回り', '役割'], ch);
      for (const g of ['stats', 'defense', 'kit', 'play']) assert.ok(html.includes(`guide-trait-${g}`), `${ch}: group ${g}`);
      for (const n of unreleasedNames) assert.ok(!html.includes(`>${n}<`), `${ch}: unreleased effect ${n}`);
    }
  });
}

// 公開ページ (web/guide.html): the effect catalog and the appendix never show an unreleased effect (spoilers)
const fs = require('fs');
const path = require('path');
const { ROOT_DIR } = require('./helpers');

for (const dir of APP_DIRS) {
  test(`${dir}: releasedRelicEffects lists released relic effects only`, () => {
    const ctx = runScripts({}, dir, ['relic-effects.js']);
    ctx.__e = loadResource('effects_data.json');
    const list = JSON.parse(JSON.stringify(vm.runInContext('releasedRelicEffects(__e)', ctx)));
    const relic = (id) => Number(id) < 200000 || (Number(id) >= 6000000 && Number(id) < 7400000);
    const releasedKeys = new Set(Object.entries(effects).filter(([id, e]) => relic(id) && !e.unreleased).map(([, e]) => e.key));
    assert.deepEqual(list.map((e) => e.key).sort(), [...releasedKeys].sort());
    const shown = new Set(list.flatMap((e) => [e.name_ja, e.name_en]));
    for (const [id, e] of Object.entries(effects)) {
      // an unreleased id's name may only appear when another, released relic id has the same name
      if (e.unreleased && relic(id) && shown.has(e.name_ja)) {
        assert.ok(Object.entries(effects).some(([j, x]) => j !== id && relic(j) && !x.unreleased && x.name_ja === e.name_ja), `${id} ${e.name_ja}`);
      }
    }
  });
}

test('appendix HTML (shown on the public page) has no unreleased effect', () => {
  const released = new Set(Object.values(effects).filter((e) => !e.unreleased).map((e) => e.name_ja));
  const hidden = unreleasedNames.filter((n) => !released.has(n));
  for (const f of ['builds.html', 'characters.html']) {
    const html = fs.readFileSync(path.join(ROOT_DIR, 'tools', 'build_suggest', 'catalog', f), 'utf8');
    for (const n of hidden) assert.ok(!html.includes(`「${n}」`) && !html.includes(`>${n}<`) && !html.includes(`| ${n} |`), `${f}: ${n}`);
  }
});
