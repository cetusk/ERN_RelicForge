#!/usr/bin/env python3
"""
攻略 Wiki「遺物効果」ページと resources/effects_data.json の重ね掛け・備考を照合する

  python tools/wiki_effects/sync.py              # Wiki を取得して照合し、レビューページを作成
  python tools/wiki_effects/sync.py --offline    # 前回取得した Wiki ページで再照合
  python tools/wiki_effects/sync.py --apply      # 照合結果を effects_data.json に反映

詳細は tools/wiki_effects/README.md を参照。
"""

import argparse
import collections
import glob
import json
import os
import sys

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TOOL_DIR, '..', '..'))
sys.path.insert(0, TOOL_DIR)

import match   # noqa: E402
import report  # noqa: E402
import rules   # noqa: E402
import wiki    # noqa: E402

EFFECTS_PATH = os.path.join(ROOT_DIR, 'resources', 'effects_data.json')
DEFAULT_OUT = os.path.join(ROOT_DIR, 'debugs', 'effects_review')


def effects_in_saves(save_paths, effects):
    """Effect IDs that actually appear on relics in the given save files (via src/relic_parser.py)."""
    if not save_paths:
        return set()
    sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))
    from relic_parser import RelicParser, SaveFileDecryptor
    with open(os.path.join(ROOT_DIR, 'resources', 'items_data.json'), encoding='utf-8') as f:
        valid_items = {int(k) for k in json.load(f)['items']}
    valid_effects = {int(k) for k in effects}
    seen = set()
    for path in save_paths:
        entries = SaveFileDecryptor.decrypt_save_file(path)
        for relic in RelicParser.parse_relics_from_entry(entries[0].clean_data, valid_items, valid_effects):
            for group in relic['effects']:
                seen.update(group)
    return seen


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out-dir', default=DEFAULT_OUT, help='レビューページ等の出力先 (default: debugs/effects_review)')
    ap.add_argument('--offline', action='store_true', help='Wiki を取得せず、出力先に保存済みの wiki.html を使う')
    ap.add_argument('--saves', nargs='*', default=None,
                    help='出現判定に使うセーブファイル (default: debugs/*.sl2)')
    ap.add_argument('--apply', action='store_true', help='照合結果を resources/effects_data.json に反映する')
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    html_path = os.path.join(args.out_dir, 'wiki.html')
    if args.offline:
        with open(html_path, encoding='utf-8') as f:
            html = f.read()
    else:
        print(f'Fetching {wiki.WIKI_URL}', file=sys.stderr)
        html = wiki.fetch()
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
    updated = wiki.last_updated(html)
    rows = wiki.parse_effect_rows(html)
    print(f'Wiki: {len(rows)} effect rows (last updated {updated or "?"})', file=sys.stderr)

    with open(EFFECTS_PATH, encoding='utf-8') as f:
        data = json.load(f)
    effects = data['effects']
    saves = args.saves if args.saves is not None else sorted(glob.glob(os.path.join(ROOT_DIR, 'debugs', '*.sl2')))
    seen = effects_in_saves(saves, effects)
    print(f'Saves: {len(saves)} file(s), {len(seen)} distinct effects on relics', file=sys.stderr)

    if not saves:
        print('WARNING: no save files; the released/unreleased flags are left as they are', file=sys.stderr)

    matcher = match.Matcher(rows)
    items = []
    for k, entry in sorted(effects.items(), key=lambda x: int(x[0])):
        eid = int(k)
        if not rules.in_scope(eid):
            continue
        p = match.propose(eid, entry, matcher)
        p['seen'] = eid in seen
        p['cur_unreleased'] = bool(entry.get('unreleased'))
        if saves:
            p['unreleased'] = (p['how'] == 'none' and not p['seen']) or eid in rules.UNRELEASED_OVERRIDES
        else:
            p['unreleased'] = p['cur_unreleased']
        status = []
        if p['prop_stack'] != p['cur_stack']:
            status.append('重複変更')
        if p['prop_short'] != p['cur_notes']:
            status.append('要約変更')
        if p['prop_notes'] != p['cur_full']:
            status.append('全文変更')
        if p['unreleased'] != p['cur_unreleased']:
            status.append('公開状況変更')
        p['status'] = status or ['変更なし']
        items.append(p)

    used = {p['w_name'] for p in items if p['w_name']}
    wiki_only = [r for r in rows if r['name'] not in used]
    report.write(os.path.join(args.out_dir, 'index.html'), items, wiki_only, updated)
    with open(os.path.join(args.out_dir, 'proposal.json'), 'w', encoding='utf-8') as f:
        json.dump({'wiki_updated': updated, 'items': items, 'wiki_only': wiki_only}, f, ensure_ascii=False, indent=1)

    how = collections.Counter(p['how'] + ('/seen' if p['seen'] else '') for p in items)
    st = collections.Counter('+'.join(p['status']) for p in items)
    print(f'Effects in scope: {len(items)}  match: {dict(sorted(how.items()))}', file=sys.stderr)
    print(f'Changes: {dict(st)}', file=sys.stderr)
    print(f'Unreleased (not on the wiki, never seen in saves): {sum(p["unreleased"] for p in items)}',
          file=sys.stderr)
    unmatched_seen = [p for p in items if p['seen'] and p['how'] == 'none']
    if unmatched_seen:
        print(f'WARNING: {len(unmatched_seen)} effects seen in saves have no wiki row '
              f'(add to rules.NAME_ALIASES if renamed):', file=sys.stderr)
        for p in unmatched_seen:
            print(f'  {p["id"]} {p["name_ja"]}  suggestion: {p["suggestion"]}', file=sys.stderr)
    print(f'Review page: {os.path.join(args.out_dir, "index.html")}', file=sys.stderr)

    if args.apply:
        changed = 0
        for p in items:
            entry = effects[str(p['id'])]
            updated = match.apply_proposal(entry, p)
            if p['unreleased'] != bool(entry.get('unreleased')):
                if p['unreleased']:
                    entry['unreleased'] = True
                else:
                    entry.pop('unreleased', None)
                updated = True
            changed += updated
        with open(EFFECTS_PATH, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f'Applied: {changed} effects updated in {EFFECTS_PATH}', file=sys.stderr)


if __name__ == '__main__':
    main()
