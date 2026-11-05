#!/usr/bin/env python3
"""
ビルド提案（試験的）の付録カタログを作る（resources/build_suggest.json から。手で編集しない）

  python tools/build_suggest/catalog.py           # catalog/*.md を作る
  python tools/build_suggest/catalog.py --check   # 作り直した結果が今のファイルと同じか確認（テスト用）

  catalog/builds.md      キャラ別のビルド一覧（定番の効果と、神攻略wiki のビルド 174 件）
  catalog/characters.md  キャラ別の評価と数値（デメリットの評価・キャラの数値・版ごとの性能変更）
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT_DIR = os.path.join(HERE, 'catalog')
sys.path.insert(0, os.path.join(HERE, 'research'))
import characters_gen as cg  # noqa: E402

data = json.load(open(os.path.join(ROOT, 'resources', 'build_suggest.json'), encoding='utf-8'))
effects = json.load(open(os.path.join(ROOT, 'resources', 'effects_data.json'), encoding='utf-8'))['effects']
CHARACTERS = list(json.load(open(os.path.join(ROOT, 'resources', 'vessels_data.json'), encoding='utf-8'))['characters'])

NAME = {}
for i in sorted(effects, key=int):
    n = int(i)
    if n < 200000 or 6000000 <= n < 7400000:
        NAME.setdefault(effects[i]['key'], effects[i]['name_ja'])
SOURCE_TITLE = {url: title for title, url, _ in cg.SRC.values()}

HEADER = """<!-- tools/build_suggest/catalog.py で生成（手で編集しない） -->
"""


def names(keys):
    return ''.join(f'「{NAME.get(k, k)}」' for k in keys) or '—'


def anchor(text):
    return text.replace(' ', '-')


def builds_md():
    lines = [HEADER, '# キャラ別のビルド一覧（付録）', '',
             'ビルド提案（試験的）が使う「キャラの定番の効果」と「ビルドのテンプレート」の一覧。出典は神攻略wiki のみ'
             '（キャラページとビルド投稿）。効果の優先度は、ビルド提案での使われ方',
             '（必須 = そのビルドを決める効果、推奨、任意、避けたい）。未公開の効果は含まない。', '',
             f'ビルド {len(data["builds"])} 件（うち特定の相手向け {sum(1 for b in data["builds"] if b["target"])} 件）。', '']
    lines += ['| キャラ | 汎用 | 特定の相手向け |', '|---|---:|---:|']
    for ch in CHARACTERS:
        bs = [b for b in data['builds'] if b['character'] == ch]
        lines.append(f'| [{ch}](#{anchor(ch)}) | {sum(1 for b in bs if not b["target"])} | {sum(1 for b in bs if b["target"])} |')
    for ch in CHARACTERS:
        lines += ['', f'## {ch}', '']
        st = data['staples'].get(ch)
        if st:
            lines += ['### キャラの定番の効果', '',
                      f'- 推奨: {names(st["rec"])}', f'- 任意: {names(st["opt"])}', f'- 避けたい: {names(st["avoid"])}', '']
        bs = [b for b in data['builds'] if b['character'] == ch]
        for title, group in (('汎用のビルド', [b for b in bs if not b['target']]),
                             ('特定の相手向けのビルド', [b for b in bs if b['target']])):
            if not group:
                continue
            lines += [f'### {title}（{len(group)} 件）', '']
            for b in group:
                head = f'#### {b["id"]} {b["name"]}'
                lines += [head, '']
                meta = [f'狙い: {b["aim"]}' if b['aim'] else '', f'相手: {b["target"]}' if b['target'] else '',
                        f'モード: {b["mode"]}' if b['mode'] else '']
                lines.append('- ' + ' ／ '.join(m for m in meta if m))
                for label, key in (('必須', 'must'), ('推奨', 'rec'), ('任意', 'opt'), ('避けたい', 'avoid')):
                    if b[key]:
                        lines.append(f'- {label}: {names(b[key])}')
                if b['vessel']:
                    lines.append(f'- 献器: {b["vessel"]}')
                if b['sources']:
                    lines.append('- 出典: ' + '、'.join(f'[{SOURCE_TITLE.get(u, u)}]({u})' for u in b['sources']))
                lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


import character_effects as ce  # noqa: E402

RESEARCH = ce.apply_owner_notes(json.load(open(os.path.join(HERE, 'research', 'character_research.json'), encoding='utf-8')))
VERDICT = {'accept': '許容', 'avoid': '避けたい', 'mixed': '割れる', 'depends': '条件次第', 'must': '必須', 'strong': '重要', 'nice': 'あると良い'}
TIER = {'body': '本文', 'comment': 'コメントの多数意見', 'body-contested': '本文（最近のコメントが反対）',
        'comment-over-body-mixed': 'コメントの多数意見（本文は割れる）'}
KIND = {'buff': '上方', 'nerf': '下方', 'fix': '不具合修正', 'change': '変更', 'add': '追加'}


def cell(text):
    return str(text or '').replace('|', '／').replace('\n', ' ')


def characters_md():
    used = data.get('characters', {})
    lines = [HEADER, '# キャラ別の評価と数値（付録）', '',
             f'キャラの特性（能力値・HP・回避・強靭度・カット率・状態異常耐性・スキルとアーツ・立ち回り）によって変わる遺物効果の評価。'
             f'神攻略wiki のキャラページ（本文とコメント欄）と、キャラクター・ステータス・強靭度・基本アクション・遺物効果・'
             f'アップデート情報のページから集めた（{RESEARCH["researched"]} 調査）。未公開の効果は含まない。', '',
             '## 評価の使い方（オーナーの方針）', '',
             '- 本文の評価を主に使う。ビルド提案では除外の重みを「推奨」にする',
             '- コメント欄の評価は、同じ評価の投稿が 3 件以上かつ反対の 2 倍以上あるときだけ使う（同じ人の連投は 1 件）。除外の重みは「任意」',
             '- 本文の評価でも、最近のコメントがはっきり反対していれば（3 件以上かつ 2 倍以上）「割れる」として扱いを変えない',
             '- 関係する性能変更より前の投稿は数えない（下の「版ごとの性能変更」。各表の「集計開始」がその日付）',
             '- 条件付きの評価（「瓦礫ビルドなら」「重ね付けしなければ」など）と、本文どうしが食い違うものは使わない',
             '- 全キャラ共通の評価（遺物効果ページの考察）と同じになるものは、共通の評価のまま', '',
             '## ビルド提案で使っている評価', '',
             '深き夜（通常+深層）のときだけ使う。理由はビルド提案の画面にもそのまま表示する。', '',
             '| キャラ | 効果 | 扱い | 根拠 | 理由 |', '|---|---|---|---|---|']
    for ch in CHARACTERS:
        r = used.get(ch)
        if not r:
            continue
        for x in r['avoid']:
            lines.append(f'| {ch} | {NAME.get(x["key"], x["key"])} | 除外（{"推奨" if x["priority"] == "preferred" else "任意"}） | '
                         f'{"本文" if x["tier"] == "body" else "コメントの多数意見"} | {cell(x["why"])} |')
        by_why = {}
        for x in r['useless']:
            by_why.setdefault(x['why'], []).append(NAME.get(x['key'], x['key']))
        for why, ns in by_why.items():
            lines.append(f'| {ch} | {"".join(f"「{n}」" for n in ns)} | 使わない | 本文 | {cell(why)} |')
    lines += ['', '## キャラの数値の比較', '',
              '| キャラ | Lv15 の HP / FP / スタミナ | 回避 | 強靭度 | 得意武器 |', '|---|---|---|---|---|']
    for ch in CHARACTERS:
        st = RESEARCH['characters'][ch]['stats']
        lines.append(f'| [{ch}](#{anchor(ch)}) | {st.get("Lv15 の HP / FP / スタミナ", "—")} | {cell(st.get("回避", "—"))} | '
                     f'{cell(st.get("強靭度", "—"))} | {cell(st.get("得意武器", "—"))} |')
    lines += ['', '出典: ' + '、'.join(f'[{p["name"]}]({p["url"]})（{p.get("last_updated") or "—"}）' for p in RESEARCH['pages']), '']
    for ch in CHARACTERS:
        c = RESEARCH['characters'][ch]
        lines += ['', f'## {ch}', '', f'[キャラページ]({c["page"]["url"]})（最終更新 {c["page"]["last_updated"] or "—"}）', '',
                  '### 数値', '']
        lines += [f'- {k}: {v}' for k, v in c['stats'].items()]
        lines += ['', '### 特性', '']
        lines += [f'- {t["what"]}: {t["value"]}' for t in c['traits']]
        lines += ['', '### デメリットの評価', '',
                  '| 効果 | 出典 | 評価 | 投稿（許容／避けたい） | 集計開始 | 判定 | 理由 |', '|---|---|---|---|---|---|---|']
        for x in c['demerits']:
            decision = {'accept': '許容', 'avoid': '避けたい', 'mixed': '割れる（変えない）'}.get(x['decision'], '使わない（一致なし）')
            tier = f'（{TIER.get(x["tier"], x["tier"])}）' if x['tier'] else ''
            lines.append(f'| {cell(x["name"])} | {x["source"]} | {VERDICT.get(x["verdict"], x["verdict"] or "—")} | '
                         f'{x["accept_posts"]}／{x["avoid_posts"]} | {x["counted_since"]} | {decision}{tier} | {cell(x["why"])} |')
        for title, key in (('必須・重要な効果（参考）', 'important'), ('意味がない・合わない効果（参考）', 'useless')):
            if c[key]:
                lines += ['', f'### {title}', '']
                lines += [f'- {VERDICT.get(x["level"], "") + "：" if x["level"] else ""}{x["name"]}（{x["source"]}）: {x["why"]}' for x in c[key]]
        if c['contested']:
            lines += ['', '### 意見が割れている点', '']
            for x in c['contested']:
                lines.append(f'- {x["topic"]}')
                lines += [f'  - {v}' for v in x['views']]
    lines += ['', '## 版ごとの性能変更', '',
              'アップデート情報のページから、キャラの性能と遺物効果（とくに深層のデメリット）に関わるもの。'
              '評価の集計では、関係する変更より前の投稿を数えていない。', '']
    for v in RESEARCH['versions']:
        if not v['changes']:
            continue
        lines += [f'### {v["date"]} {v["version"]}', '']
        lines += [f'- {c["target"]}（{KIND.get(c["kind"], c["kind"])}）: {c["text"]}' for c in v['changes']]
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


FILES = {'builds.md': builds_md, 'characters.md': characters_md}

if __name__ == '__main__':
    stale = []
    for name, make in FILES.items():
        path = os.path.join(OUT_DIR, name)
        text = make()
        if '--check' in sys.argv:
            if not os.path.exists(path) or open(path, encoding='utf-8').read() != text:
                stale.append(path)
            continue
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print(f'wrote {path} ({len(text.encode("utf-8")) // 1024} KB)')
    if stale:
        print('out of date (run python tools/build_suggest/catalog.py): ' + ', '.join(stale), file=sys.stderr)
        sys.exit(1)
