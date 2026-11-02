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
      for (const n of unreleasedNames) assert.ok(!html.includes(`>${n}<`), `${ch}: unreleased effect ${n}`);
    }
  });
}
