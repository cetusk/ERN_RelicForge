'use strict';
/**
 * Test helpers: load the browser scripts (web/ and gui/renderer/) into a Node vm
 * context, the same way the pages / Web Worker load them.
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT_DIR = path.resolve(__dirname, '..');
const FIXTURES_DIR = path.join(__dirname, 'fixtures');
const APP_DIRS = ['web', 'gui/renderer'];

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function loadFixture(name) {
  return readJson(path.join(FIXTURES_DIR, name));
}

function loadResource(name) {
  return readJson(path.join(ROOT_DIR, 'resources', name));
}

function runScripts(ctx, appDir, files) {
  vm.createContext(ctx);
  for (const f of files) {
    const filename = path.join(ROOT_DIR, appDir, f);
    vm.runInContext(fs.readFileSync(filename, 'utf8'), ctx, { filename });
  }
  return ctx;
}

/** vm context with crypto-js + relic-parser.js from appDir loaded */
function parserContext(appDir) {
  return runScripts({ console, TextDecoder }, appDir, ['lib/crypto-js.min.js', 'relic-parser.js']);
}

/** Parse a save file with relic-parser.js from appDir. Returns output without `file`. */
function parseSave(appDir, savePath, itemsData, effectsData) {
  const ctx = runScripts({ console, TextDecoder }, appDir, ['lib/crypto-js.min.js', 'relic-parser.js']);
  const buf = fs.readFileSync(savePath);
  ctx.__args = [buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.length), itemsData, effectsData];
  const result = vm.runInContext('parseSaveFile(...__args)', ctx);
  delete result.file;
  return JSON.parse(JSON.stringify(result));
}

/**
 * Run relic-optimizer.js from appDir through its Web Worker message handler,
 * with the same inputs the app posts to the worker.
 */
function runOptimizer(appDir, relics, scenario) {
  let result = null;
  let error = null;
  const self = {
    postMessage(msg) {
      if (msg.result) result = msg.result;
      if (msg.error) error = msg.error;
    },
  };
  const ctx = runScripts({ self, console }, appDir, ['relic-optimizer.js']);
  ctx.__effectsData = loadResource('effects_data.json');
  const stackingData = vm.runInContext('loadStackingData(__effectsData)', ctx);
  self.onmessage({
    data: {
      relics,
      effectSpecs: scenario.effects,
      vesselsData: loadResource('vessels_data.json'),
      stackingData,
      params: scenario.params,
    },
  });
  if (error) throw new Error(error);
  return JSON.parse(JSON.stringify(result));
}

/** Same as normalize_optimizer_output() in fixtures/generate.py */
function normalizeOptimizerOutput(output) {
  const norm = (res) => {
    const r = { ...res };
    if (r.vessel) r.vessel = r.vessel.key;
    return r;
  };
  const results = (output.allResults || []).flatMap(g => g.results.map(norm));
  const best = output.bestResult ? norm(output.bestResult.result) : null;
  return { best, results };
}

module.exports = {
  ROOT_DIR, FIXTURES_DIR, APP_DIRS,
  loadFixture, loadResource, runScripts, parseSave, parserContext, runOptimizer, normalizeOptimizerOutput,
};
