#!/usr/bin/env python3
"""
実際のセーブファイルでの確認スクリプト (ローカル専用・CI では実行しない)

各セーブファイルを Python 版・JS 版 (web / gui) パーサーで解析し、
結果が一致すること、未知の遺物 (データ未収録の ID) が無いこと、
深層専用 (deepOnly) の印が付いた効果が通常の遺物に付いていないことを確認する。
ゲームアップデート後に resources/ のデータが追いついているかの確認にも使う。

  python tests/check_real_saves.py                 # debugs/*.sl2 を確認
  python tests/check_real_saves.py path/to/NR0000.sl2 ...

終了コード: 0 = すべて問題なし / 1 = 不一致・未知・deepOnly の矛盾のいずれかあり
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


def deep_only_on_normal(py):
    """deepOnly kinds (any id of the key marked) found on normal relics.

    The ID range does not tell whether an effect is deep-only (6xxxxxx effects also appear
    on normal relics), so the flag is checked against what real saves contain.
    """
    with open(os.path.join(ROOT_DIR, 'resources', 'effects_data.json'), encoding='utf-8') as f:
        effects = json.load(f)['effects']
    deep_keys = {v['key'] for v in effects.values() if v.get('deepOnly')}
    return sorted({e['name_ja'] for r in py['relics'] if r['itemType'] == 'Relic'
                   for g in r['effects'] for e in g if e.get('key') in deep_keys})


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
        wrong_deep = deep_only_on_normal(py)
        status = 'OK' if not mismatched and unknown == 0 and not wrong_deep else 'NG'
        ok = ok and status == 'OK'
        print(f"[{status}] {os.path.basename(save)}: {py['totalRelics']} relics, "
              f"unknown {unknown}, Python/JS {'mismatch: ' + ', '.join(mismatched) if mismatched else 'match'}")
        if unknown:
            ids = sorted({e['id'] for r in py['relics'] for g in r['effects'] for e in g if e.get('unknown')})
            items = sorted({r['itemId'] for r in py['relics'] if r['itemKey'].startswith('unknownItem_')})
            print(f'       unknown effect IDs: {ids}')
            print(f'       unknown item IDs:   {items}')
        if wrong_deep:
            print(f'       deepOnly effects on normal relics: {wrong_deep}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
