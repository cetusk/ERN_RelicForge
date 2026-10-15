'use strict';
// web/ と gui/renderer/ で共通のファイルが一致していることのテスト
// (片方だけ修正して反映し忘れるのを防ぐ)
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { ROOT_DIR } = require('./helpers');

const SHARED_FILES = ['relic-parser.js', 'relic-optimizer.js', 'relic-share.js', 'lib/crypto-js.min.js', 'lib/icons.js'];

for (const f of SHARED_FILES) {
  test(`web/${f} and gui/renderer/${f} are identical`, () => {
    const web = fs.readFileSync(path.join(ROOT_DIR, 'web', f), 'utf8');
    const gui = fs.readFileSync(path.join(ROOT_DIR, 'gui', 'renderer', f), 'utf8');
    assert.ok(web === gui, `web/${f} differs from gui/renderer/${f} — copy the change to both`);
  });
}
