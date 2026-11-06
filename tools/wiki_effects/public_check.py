#!/usr/bin/env python3
"""
公開ページ（web/guide.html）の効果カタログに出す効果・出さない効果を、根拠つきで確認するページを作る

  python tools/wiki_effects/sync.py              # 先に照合（debugs/effects_review/proposal.json ができる）
  python tools/wiki_effects/public_check.py      # → debugs/effects_review/public_check.html（Git 管理外）

公開ページの効果カタログは、遺物効果（固有遺物 ID < 200000、通常・深層 6000000〜7399999）のうち、
effects_data.json で "unreleased" の印が付いていない ID を 1 つでも持つ効果（key）を表示する（web/relic-effects.js の
releasedRelicEffects と同じ規則）。このページはその一覧と、出さない（未公開の）効果を並べ、それぞれの根拠
（Wiki の行に対応したか、手元のセーブに出てきたか）を示す。Wiki のまとめ行だけに当てはまり、セーブにも
出てこない効果は「要確認」として先頭に出す（実在しないのにまとめ行に当てはまってしまう効果の見落とし防止）。
"""

import argparse
import html
import json
import os
import sys

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TOOL_DIR, '..', '..'))
sys.path.insert(0, TOOL_DIR)
import rules  # noqa: E402

HOW = {'exact': 'Wiki に同じ名前の行', 'alias': 'Wiki の別名の行（rules.NAME_ALIASES）', 'pattern': 'Wiki のまとめ行（「○○」など）に当てはまる',
       'section-rule': 'Wiki の節の説明（rules.SECTION_RULES）', 'none': 'Wiki に対応する行なし'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', default=os.path.join(ROOT_DIR, 'debugs', 'effects_review'),
                    help='sync.py の出力先（proposal.json がある場所。ページもここに書く）')
    args = ap.parse_args()
    proposal_path = os.path.join(args.dir, 'proposal.json')
    if not os.path.exists(proposal_path):
        sys.exit(f'{proposal_path} がありません。先に python tools/wiki_effects/sync.py を実行してください')
    proposal = json.load(open(proposal_path, encoding='utf-8'))
    match = {x['id']: x for x in proposal['items']}
    effects = json.load(open(os.path.join(ROOT_DIR, 'resources', 'effects_data.json'), encoding='utf-8'))['effects']

    relic = {int(i): e for i, e in effects.items() if rules.in_scope(int(i))}
    by_key = {}
    for i in sorted(relic):
        by_key.setdefault(relic[i]['key'], []).append(i)
    shown_keys = {k for k, ids in by_key.items() if any(not relic[i].get('unreleased') for i in ids)}

    def evidence(i):
        m = match.get(i, {})
        return m.get('how', 'none'), bool(m.get('seen')), m.get('w_name') or ''

    hidden, shown = [], []
    for i, e in sorted(relic.items()):
        how, seen, w_name = evidence(i)
        row = {'id': i, 'name': e['name_ja'], 'key': e['key'], 'how': how, 'seen': seen, 'w_name': w_name,
               'deep': bool(e.get('deepOnly')), 'override': i in rules.UNRELEASED_OVERRIDES}
        if e.get('unreleased'):
            row['same_name_shown'] = e['key'] in shown_keys
            hidden.append(row)
        else:
            # needs a look: matched only through a generic wiki row and never seen in the saves
            row['check'] = how == 'pattern' and not seen
            shown.append(row)
    shown.sort(key=lambda r: (not r['check'], r['name']))
    # mismatch the owner must see: an effect marked unreleased that the saves contain, or shown without any evidence
    problems = [r for r in hidden if r['seen']] + [r for r in shown if r['how'] == 'none' and not r['seen']]

    esc = lambda s: html.escape(str(s), quote=True)  # noqa: E731

    def hidden_rows():
        out = []
        for r in hidden:
            why = '手動で未公開に指定（rules.UNRELEASED_OVERRIDES）' if r['override'] else 'Wiki に対応する行がなく、セーブにも出てこない'
            if r['how'] == 'pattern':
                why += f'（まとめ行「{esc(r["w_name"])}」には当てはまる）'
            out.append(f'<tr><td class="num">{r["id"]}</td><td>{esc(r["name"])}</td><td>{esc(HOW.get(r["how"], r["how"]))}</td>'
                       f'<td>{"○" if r["seen"] else "—"}</td><td>{why}</td></tr>')
        return ''.join(out)

    def shown_rows():
        out = []
        for r in shown:
            tag = '<span class="tag">要確認</span> ' if r['check'] else ''
            out.append(f'<tr class="{"check" if r["check"] else ""}"><td class="num">{r["id"]}</td><td>{tag}{esc(r["name"])}'
                       f'{" <small>深層</small>" if r["deep"] else ""}</td><td>{esc(HOW.get(r["how"], r["how"]))}'
                       f'{f"<br><small>{esc(r["w_name"])}</small>" if r["how"] in ("pattern", "alias") and r["w_name"] else ""}</td>'
                       f'<td>{"○" if r["seen"] else "—"}</td></tr>')
        return ''.join(out)

    n_check = sum(r['check'] for r in shown)
    page = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>公開ページの効果の確認</title>
<style>
body {{ margin: 0; padding: 20px max(16px, env(safe-area-inset-left)); background: #1a1a1a; color: #e0e0e0;
  font: 14px/1.6 system-ui, "Hiragino Sans", "Yu Gothic", sans-serif; }}
h1 {{ font-size: 20px; color: #4cc9b0; }} h2 {{ font-size: 16px; margin-top: 28px; border-bottom: 1px solid #3a3a3a; }}
p, li {{ color: #c8c8c8; }} small {{ color: #909090; }}
table {{ border-collapse: collapse; font-size: 13px; }} th, td {{ border: 1px solid #3a3a3a; padding: 4px 8px; text-align: left; vertical-align: top; }}
th {{ background: #242424; position: sticky; top: 0; }} .num {{ font-variant-numeric: tabular-nums; }}
.wrap {{ overflow-x: auto; }} tr.check td {{ background: #3a3020; }} .tag {{ color: #1a1a1a; background: #f0a830; border-radius: 3px; padding: 0 5px; font-size: 11px; }}
.bad {{ color: #ff8a7a; font-weight: 600; }} label {{ display: inline-flex; gap: 6px; align-items: center; margin: 8px 0; }}
</style></head><body>
<h1>公開ページの効果カタログ: 出す効果・出さない効果</h1>
<p>照合: 神攻略wiki「遺物効果」ページ（最終更新 {esc(proposal.get('wiki_updated') or '—')}）と手元のセーブ（debugs/*.sl2）。
このページは確認用で、Git 管理外（debugs/）。</p>
<ul>
<li>公開ページに出す効果: <b>{len(shown_keys)}</b> 種類（ID {len(shown)} 件）。うち<span class="tag">要確認</span> {n_check} 件
（Wiki のまとめ行だけに当てはまり、セーブにも出てこない。実在するか確認してください）</li>
<li>出さない効果（未公開の印あり）: <b>{len(hidden)}</b> 件</li>
<li class="{'bad' if problems else ''}">食い違い: {len(problems)} 件
（未公開の印があるのにセーブに出てきた効果、または根拠のないまま出している効果）</li>
</ul>
<p>判定: Wiki のどの行にも対応せず、かつセーブに一度も出てこない効果を未公開とする（tools/wiki_effects/README.md）。
公開ページは未公開の印がある ID を表示しない（web/relic-effects.js の releasedRelicEffects）。</p>

<h2>出さない効果（未公開） {len(hidden)} 件</h2>
<div class="wrap"><table><thead><tr><th>ID</th><th>効果名</th><th>Wiki</th><th>セーブ</th><th>未公開とした理由</th></tr></thead>
<tbody>{hidden_rows()}</tbody></table></div>

<h2>出す効果 ID {len(shown)} 件（要確認を先頭に）</h2>
<label><input type="checkbox" id="only-check"> 要確認だけ表示</label>
<div class="wrap"><table id="shown"><thead><tr><th>ID</th><th>効果名</th><th>Wiki の根拠</th><th>セーブ</th></tr></thead>
<tbody>{shown_rows()}</tbody></table></div>
<script>
document.getElementById('only-check').addEventListener('change', (e) => {{
  document.querySelectorAll('#shown tbody tr').forEach((tr) => {{ tr.hidden = e.target.checked && !tr.classList.contains('check'); }});
}});
</script>
</body></html>
"""
    out = os.path.join(args.dir, 'public_check.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'shown {len(shown_keys)} kinds ({len(shown)} ids, {n_check} to check), hidden {len(hidden)}, problems {len(problems)}')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
