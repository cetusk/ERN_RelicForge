#!/usr/bin/env python3
"""
実際のセーブファイルでの確認スクリプト (ローカル専用・CI では実行しない)

各セーブファイルを Python 版・JS 版 (web / gui) パーサーで解析し、
結果が一致すること、未知の遺物 (データ未収録の ID) が無いことを確認する。
ゲームアップデート後に resources/ のデータが追いついているかの確認にも使う。

  python tests/check_real_saves.py                 # debugs/*.sl2 を確認
  python tests/check_real_saves.py path/to/NR0000.sl2 ...

終了コード: 0 = すべて一致かつ未知 0 件 / 1 = 不一致または未知あり
"""

import glob
import json
import os
import subprocess
import sys
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(TESTS_DIR)

JS_PARSE = """
const { parseSave, loadResource } = require(process.argv[1]);
const [dir, save, out] = process.argv.slice(2);
const r = parseSave(dir, save, loadResource('items_data.json'), loadResource('effects_data.json'));
require('fs').writeFileSync(out, JSON.stringify(r));
"""


def parse_python(save, tmp):
    out = os.path.join(tmp, 'py.json')
    subprocess.run([sys.executable, os.path.join(ROOT_DIR, 'src', 'relic_parser.py'), save, '-o', out],
                   check=True, capture_output=True, cwd=ROOT_DIR)
    with open(out, 'r', encoding='utf-8') as f:
        result = json.load(f)
    result.pop('file')
    return result


def parse_js(app_dir, save, tmp):
    out = os.path.join(tmp, 'js.json')
    subprocess.run(['node', '-e', JS_PARSE, os.path.join(TESTS_DIR, 'helpers.js'), app_dir, save, out],
                   check=True, capture_output=True)
    with open(out, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    saves = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT_DIR, 'debugs', '*.sl2')))
    if not saves:
        print('No save files found (put .sl2 files in debugs/ or pass paths)')
        return 1
    ok = True
    for save in saves:
        with tempfile.TemporaryDirectory() as tmp:
            py = parse_python(os.path.abspath(save), tmp)
            mismatched = [d for d in ('web', 'gui/renderer')
                          if parse_js(d, os.path.abspath(save), tmp) != py]
        unknown = py.get('unknownRelics', 0)
        status = 'OK' if not mismatched and unknown == 0 else 'NG'
        ok = ok and status == 'OK'
        print(f"[{status}] {os.path.basename(save)}: {py['totalRelics']} relics, "
              f"unknown {unknown}, Python/JS {'mismatch: ' + ', '.join(mismatched) if mismatched else 'match'}")
        if unknown:
            ids = sorted({e['id'] for r in py['relics'] for g in r['effects'] for e in g if e.get('unknown')})
            items = sorted({r['itemId'] for r in py['relics'] if r['itemKey'].startswith('unknownItem_')})
            print(f'       unknown effect IDs: {ids}')
            print(f'       unknown item IDs:   {items}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
