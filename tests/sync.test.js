'use strict';
// web/ と gui/renderer/ で共通のファイルが一致していることのテスト
// (片方だけ修正して反映し忘れるのを防ぐ)
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { ROOT_DIR } = require('./helpers');

const SHARED_FILES = ['relic-parser.js', 'relic-optimizer.js', 'relic-share.js', 'lib/crypto-js.min.js', 'lib/icons.js',
  'lib/qrcode.js', 'lib/qrcode.LICENSE.txt', 'relic-suggest.js'];

for (const f of SHARED_FILES) {
  test(`web/${f} and gui/renderer/${f} are identical`, () => {
    const web = fs.readFileSync(path.join(ROOT_DIR, 'web', f), 'utf8');
    const gui = fs.readFileSync(path.join(ROOT_DIR, 'gui', 'renderer', f), 'utf8');
    assert.ok(web === gui, `web/${f} differs from gui/renderer/${f} — copy the change to both`);
  });
}

test('app version / game version / last updated are the same in web, gui and gui/package.json', () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(ROOT_DIR, 'gui', 'package.json'), 'utf8'));
  const constant = (dir, name) => {
    const src = fs.readFileSync(path.join(ROOT_DIR, dir, 'app.js'), 'utf8');
    const m = src.match(new RegExp(`const ${name} = '([^']*)'`));
    assert.ok(m, `${dir}/app.js has no ${name}`);
    return m[1];
  };
  for (const dir of ['web', 'gui/renderer']) {
    assert.equal(constant(dir, 'APP_VERSION'), pkg.version, `${dir}/app.js APP_VERSION`);
    for (const name of ['APP_NIGHTREIGN_VERSION', 'APP_LAST_UPDATED']) {
      assert.equal(constant(dir, name), constant('web', name), `${dir}/app.js ${name}`);
    }
    // the header text before app.js runs
    const html = fs.readFileSync(path.join(ROOT_DIR, dir, 'index.html'), 'utf8');
    assert.ok(html.includes(`>${constant(dir, 'APP_NIGHTREIGN_VERSION')} 対応<`), `${dir}/index.html version label`);
    assert.ok(html.includes(`>最終更新: ${constant(dir, 'APP_LAST_UPDATED')}<`), `${dir}/index.html last updated`);
  }
});
