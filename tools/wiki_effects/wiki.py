"""攻略 Wiki「遺物効果」ページの取得と、効果テーブルの解析"""

import re
import urllib.request
from html.parser import HTMLParser

WIKI_URL = 'https://kamikouryaku.net/nightreign_eldenring/?%E9%81%BA%E7%89%A9%E5%8A%B9%E6%9E%9C'
TOP_SECTIONS = ('遺物に付与される効果', '深層の遺物に付与される効果')


def fetch(url=WIKI_URL):
    req = urllib.request.Request(url, headers={'User-Agent': 'ERN_RelicForge effects sync'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode('utf-8', errors='replace')


def last_updated(html):
    m = re.search(r'最終更新:\s*([0-9-]+)', html)
    return m.group(1) if m else ''


class _TableParser(HTMLParser):
    """Collect tables with the heading path (h2/h3/h4) they appear under."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heads = []      # [(level, text)]
        self.tables = []     # [{'rows': [[cell]], 'heads': [...]}]
        self._stack = []
        self._head_tag = None
        self._head_text = ''
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('h2', 'h3', 'h4'):
            self._head_tag, self._head_text = tag, ''
        elif tag == 'table':
            self._stack.append({'rows': [], 'heads': list(self.heads)})
        elif tag == 'tr' and self._stack:
            self._row = []
        elif tag in ('td', 'th') and self._row is not None:
            self._cell = {'text': '', 'rs': int(a.get('rowspan') or 1), 'cs': int(a.get('colspan') or 1)}
        elif tag in ('br', 'hr', 'li', 'p', 'div') and self._cell is not None:
            self._cell['text'] += '\n'   # line breaks / separators inside a cell

    def handle_endtag(self, tag):
        if tag == self._head_tag:
            level = int(tag[1])
            text = re.sub(r'\s+', ' ', self._head_text).replace('†', '').strip()
            self.heads = [h for h in self.heads if h[0] < level] + [(level, text)]
            self._head_tag = None
        elif tag in ('td', 'th') and self._cell is not None and self._row is not None:
            self._row.append(self._cell)
            self._cell = None
        elif tag == 'tr' and self._row is not None and self._stack:
            self._stack[-1]['rows'].append(self._row)
            self._row = None
        elif tag == 'table' and self._stack:
            self.tables.append(self._stack.pop())

    def handle_data(self, data):
        if self._head_tag:
            self._head_text += data
        if self._cell is not None:
            self._cell['text'] += data


def _grid(rows):
    """Expand rowspan/colspan into a rectangular grid of cell texts."""
    out, pending = [], {}   # pending: col -> (remaining rows, cell)
    for cells in rows:
        line, col, ci = [], 0, 0
        while ci < len(cells) or col in pending:
            if col in pending:
                rem, c = pending[col]
                line.append(c)
                if rem > 1:
                    pending[col] = (rem - 1, c)
                else:
                    del pending[col]
                col += 1
                continue
            c = cells[ci]
            ci += 1
            for _ in range(c['cs']):
                line.append(c)
                if c['rs'] > 1:
                    pending[col] = (c['rs'] - 1, c)
                col += 1
        out.append([x['text'].strip() for x in line])
    return out


def parse_effect_rows(html):
    """Return effect rows: {deep, section, name, stack, notes, demerit}.

    - 効果テーブル (効果 / 重ね掛け / [デメリット] / 備考)
    - キャラクター固有テーブル (キャラ|夜渡り / 効果 / 備考) -> 「同じ効果は重ね掛け不可」
    """
    p = _TableParser()
    p.feed(html)
    rows = []
    for t in p.tables:
        heads = [h[1] for h in t['heads']]
        if not heads or heads[0] not in TOP_SECTIONS:
            continue
        g = _grid(t['rows'])
        if not g:
            continue
        deep = heads[0].startswith('深層')
        hdr = g[0]
        for r in g[1:]:
            if r == hdr or len(r) < len(hdr):
                continue
            d = dict(zip(hdr, r))
            if hdr[:1] == ['効果']:
                rows.append({'deep': deep, 'section': heads[-1], 'name': d['効果'],
                             'stack': d.get('重ね掛け', ''), 'notes': d.get('備考', ''),
                             'demerit': d.get('デメリット', '')})
            elif hdr[:3] in (['キャラ', '効果', '備考'], ['夜渡り', '効果', '備考']):
                ch = d[hdr[0]].strip('【】')
                rows.append({'deep': deep, 'section': heads[-1], 'name': f'【{ch}】' + d['効果'],
                             'stack': '✕(固有)', 'notes': d['備考'], 'demerit': ''})
    return rows
