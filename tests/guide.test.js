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

for (const dir of APP_DIRS) {
  test(`${dir}: the public page's ビルド一覧 / キャラ別の評価 tabs show only their sections`, () => {
    const ctx = runScripts({}, dir, ['relic-guide.js']);
    const ch = Object.keys(profiles.characters)[0];
    const render = (sections) => {
      ctx.__o = { character: ch, profiles, suggest, ja: true, effectName: (k) => names[k] || k, standalone: true, sections };
      return vm.runInContext('renderCharacterGuide(__o)', ctx);
    };
    const builds = render(['builds']);
    assert.equal((builds.match(/class="guide-build"/g) || []).length, suggest.builds.filter((b) => b.character === ch).length);
    assert.ok(!builds.includes('gf-grid') && !builds.includes('guide-suggest'));
    const evals = render(['stats', 'suggest', 'demerits']);
    assert.ok(evals.includes('gf-grid') && evals.includes('guide-table') && !evals.includes('guide-build"'));
    // a reference page: nothing about the app's build suggestion
    for (const html of [builds, evals, render(undefined)]) assert.ok(!html.includes('提案') && !html.includes('guide-suggest'), 'no 提案');
  });

  test(`${dir}: deep-only kinds and the effect card`, () => {
    const ctx = runScripts({}, dir, ['relic-effects.js', 'relic-guide.js']);
    ctx.__e = loadResource('effects_data.json');
    const list = JSON.parse(JSON.stringify(vm.runInContext('releasedRelicEffects(__e)', ctx)));
    const byKey = Object.fromEntries(list.map((e) => [e.key, e]));
    // deep-only only when every released relic id is: 属性カット率上昇 is also a relic's fixed (normal) effect
    assert.equal(byKey.physicalAttackUpPlus3.deepOnly, true);
    assert.equal(byKey.improvedAffinityDamageNegation.deepOnly, false);
    assert.equal(byKey.increasedMaximumHP.deepOnly, false);
    // a kind with different normal and deep values lists both
    assert.deepEqual(byKey.increasedMaximumHP.variants.map((v) => [v.deep, v.stackNotes]),
      [[false, effects['7000090'].stackNotes], [true, effects['6610400'].stackNotes]]);
    assert.equal(byKey.improvedAffinityDamageNegation.variants, null);
    ctx.__x = byKey.increasedMaximumHP;
    const hp = vm.runInContext('renderEffectCard(__x, { ja: true })', ctx);
    assert.ok(hp.includes('catalog-card-variants') && hp.includes('<dt>通常</dt>') && hp.includes('<dt>深層</dt>'));
    const demerits = list.filter((e) => e.category === 'demerit');
    assert.ok(demerits.length > 0);
    for (const e of demerits) {
      ctx.__x = e;
      const html = vm.runInContext('renderEffectCard(__x, { ja: true })', ctx);
      assert.ok(html.includes('catalog-demerit-badge') && html.includes('深層のみ'), e.name_ja);
    }
  });
}

for (const dir of APP_DIRS) {
  // The app's effect catalog is releasedRelicEffects over this lookup: it must carry the "unreleased" flag
  test(`${dir}/app.js: the effect lookup keeps unreleased (the catalog never shows those effects)`, () => {
    const src = fs.readFileSync(path.join(ROOT_DIR, dir, 'app.js'), 'utf8');
    const fn = src.match(/function buildStackingLookup\(effectsData\) \{[\s\S]*?\n\}/);
    assert.ok(fn, 'buildStackingLookup');
    const ctx = runScripts({}, dir, ['relic-effects.js']);
    vm.runInContext(fn[0], ctx);
    ctx.__e = loadResource('effects_data.json');
    const viaLookup = vm.runInContext('releasedRelicEffects({ effects: buildStackingLookup(__e) })', ctx).map((e) => e.key);
    const direct = vm.runInContext('releasedRelicEffects(__e)', ctx).map((e) => e.key);
    assert.deepEqual([...viaLookup], [...direct]);
  });
}

test('appendix (catalog/*.md, public in the repository) has no unreleased effect', () => {
  const released = new Set(Object.values(effects).filter((e) => !e.unreleased).map((e) => e.name_ja));
  const hidden = unreleasedNames.filter((n) => !released.has(n));
  for (const f of ['builds.md', 'characters.md']) {
    const md = fs.readFileSync(path.join(ROOT_DIR, 'tools', 'build_suggest', 'catalog', f), 'utf8');
    for (const n of hidden) assert.ok(!md.includes(`「${n}」`) && !md.includes(`- ${n} `) && !md.includes(`| ${n} |`), `${f}: ${n}`);
  }
});
