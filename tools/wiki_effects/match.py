"""effects_data の効果と Wiki の行の照合、および重ね掛け・要約・全文の更新案の作成"""

import collections
import difflib
import re
import unicodedata

import rules

VALUE = r'[約+\-]?\d+(?:\.\d+)?\s*(?:%|％|倍|%分|分|回復)?'


def norm(s):
    s = unicodedata.normalize('NFKC', s).replace('～', '~').replace('〜', '~')
    return re.sub(r'\s+', '', s)


def _expand(wiki_name):
    """'X+1~3' / 'X +0~2' -> concrete names; '○○' rows -> regex patterns."""
    n = norm(wiki_name)
    m = re.match(r'^(.*?)\+(\d)~(\d)$', n)
    if m:
        base, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        return [base if i == 0 else f'{base}+{i}' for i in range(a, b + 1)], []
    if '○○' in n:
        variants = {n} | {n.replace(a, b) for a, b in rules.PLACEHOLDER_VARIANTS}
        return [], [re.compile('^' + re.escape(v).replace('○○', '(.+?)') + '$') for v in variants]
    return [n], []


def _level_range(wiki_name):
    m = re.match(r'^(.*?)\+(\d)~(\d)$', norm(wiki_name))
    return (int(m.group(2)), int(m.group(3))) if m else None


def _data_level(name):
    m = re.match(r'^.*\+(\d)$', norm(name))
    return int(m.group(1)) if m else 0


def _clean_lines(text):
    return [c for c in (rules.clean_note_line(l.strip()) for l in text.split('\n')) if c]


def _strip_char(name):
    m = re.match(r'^【(.+?)】(.*)$', name)
    return (m.group(1), m.group(2)) if m else (None, name)


class Matcher:
    def __init__(self, wiki_rows):
        self.rows = wiki_rows
        self.exact = collections.defaultdict(list)
        self.patterns = []
        for i, r in enumerate(wiki_rows):
            names, pats = _expand(r['name'])
            for n in names:
                self.exact[n].append(i)
            self.patterns += [(p, i) for p in pats]
        self.normal_by_name = {norm(r['name']): r for r in wiki_rows if not r['deep']}

    def match(self, name_ja):
        """Return (candidate row indexes, how)."""
        n = norm(name_ja)
        if self.exact.get(n):
            return self.exact[n], 'exact'
        n2 = norm(rules.NAME_ALIASES.get(name_ja, name_ja))
        for a, b in rules.NAME_REWRITES:
            n2 = n2.replace(norm(a), norm(b))
        if n2 != n and self.exact.get(n2):
            return self.exact[n2], 'alias'
        cand = [i for p, i in self.patterns if p.match(n)]
        if cand:
            return cand, 'pattern'
        for rx, _, _ in rules.SECTION_RULES:
            if re.match(rx, n):
                return [], 'section-rule'
        return [], 'none'

    def suggest(self, name_ja, deep):
        """Closest wiki row (for review only; never applied automatically)."""
        ch, body = _strip_char(norm(name_ja))
        best = (0.0, None)
        for r in self.rows:
            rch, _ = _strip_char(norm(r['name']))
            if rch != ch:
                continue
            for cand in _expand(r['name'])[0] or [norm(r['name'])]:
                sc = difflib.SequenceMatcher(None, body, _strip_char(cand)[1]).ratio() + (0.02 if r['deep'] == deep else 0)
                if sc > best[0]:
                    best = (sc, r['name'])
        return best[1] if best[0] >= 0.6 else ''


def _level_value(wiki_name, data_name, lines):
    """Per-level value from "+4%/+5%/+6%" or "...（5%/7.5%/10%）ほど軽減する" on a "+a~b" row."""
    lr = _level_range(wiki_name)
    if not (lr and lines):
        return ''
    n_lv = lr[1] - lr[0] + 1
    lv = _data_level(data_name) - lr[0]
    first = lines[0]
    m = re.search(r'[（(]([^）)]*/[^）)]*)[）)]', first)
    parts = [x.strip() for x in (m.group(1) if m else first).split('/') if x.strip()]
    prefix = ''
    if len(parts) == n_lv and not m:   # "回復量は最大HPの2.5%/3.3%" -> prefix + value
        pm = re.match(rf'^(.*?)({VALUE})$', parts[0])
        if pm and pm.group(1) and not re.search(r'\d', pm.group(1)):
            prefix = re.sub(r'^(回復量は|効果量は)', '', pm.group(1))
            parts[0] = pm.group(2)
    if not (len(parts) == n_lv and 0 <= lv < n_lv and all(re.fullmatch(VALUE, x) for x in parts)):
        return ''
    if m:
        tail = re.sub(r'^ほど', '', first[m.end():]).replace('する', '').strip()
        return '約' + parts[lv].lstrip('約') + tail
    return prefix + parts[lv]


def _nums(s):
    return re.findall(r'\d+(?:\.\d+)?', unicodedata.normalize('NFKC', s))


def _auto_summary(full):
    if not full:
        return ''
    first = full.split(' / ')[0].strip()
    if first.startswith('Lv.15時'):
        return first
    s = first.split('。')[0].strip()
    if len(s) <= rules.SUMMARY_MAXLEN:
        return s
    quantities = [x for x in re.split(r'[　、，,]', s) if x and re.search(r'\d|倍|%|％', x)]
    if quantities:
        two = '、'.join(quantities[:2])
        return two if len(two) <= rules.SUMMARY_MAXLEN + 4 else quantities[0]
    return s


def _tidy_summary(name, short):
    short = short.replace('　', '、')
    m = re.match(r'^Lv\.15時[、,]\s*(.*)$', short)
    if m:
        short = 'Lv.15時 ' + re.sub(r'\s*[,、]\s*', ', ', m.group(1))
    if re.match(rules.WEAPON_RECOVERY, name):
        short = re.sub(r'^回復量は', '回復量', short)
    return short


def propose(effect_id, entry, matcher):
    """Build the proposal for one effect: stackable / stackNotes (summary) / stackNotesFull."""
    name = entry['name_ja']
    deep = rules.is_deep_id(effect_id)
    cur_stack = entry['stackable']
    cur_short = entry.get('stackNotes', '')
    cur_full = entry.get('stackNotesFull', '')
    cand, how = matcher.match(name)
    flags, wiki = [], None
    stack, full, level_value = cur_stack, cur_full, ''

    if how == 'section-rule':
        for rx, s, note in rules.SECTION_RULES:
            if re.match(rx, norm(name)):
                stack, full = s, note
    elif cand:
        pref = [c for c in cand if matcher.rows[c]['deep'] == deep] or cand
        wiki = matcher.rows[pref[0]]
        sym = wiki['stack']
        lines = _clean_lines(wiki['notes'])
        # Deep table "既存効果" -> use the normal table's remarks for the same effect
        if lines and lines[0].startswith('既存効果'):
            base = matcher.normal_by_name.get(norm(wiki['name']))
            rest = lines[1:] if lines[0] == '既存効果' else [lines[0].replace('既存効果', '').strip()] + lines[1:]
            lines = (_clean_lines(base['notes']) if base else []) + [l for l in rest if l]
            if base and sym in ('', '－'):
                sym = base['stack']
        level_value = _level_value(wiki['name'], name, lines)
        full = ' / '.join(lines)
        if re.match(rules.APPEND_LEFTMOST_NOTE, norm(name)):
            full = ' / '.join(x for x in (full, rules.LEFTMOST_NOTE) if x)
        if sym == '◯':
            stack = True
        elif sym.startswith('✕'):
            stack = False
        elif sym == '※':
            stack = False if re.search(rules.SAME_KEY_NOT_STACKING, wiki['notes']) else 'conditional'
            flags.append('※条件付き')
        elif sym == '－':
            flags.append('Wiki未検証(重複)')
            full = ' / '.join([rules.UNVERIFIED_NOTE] + ([full] if full else []))
        else:
            flags.append(f'記号不明:{sym}')
    else:
        flags.append('Wikiに無し')
    if how == 'alias':
        flags.append('名称差(対応表)')

    # Summary (stackNotes)
    if how == 'none':
        short, src = cur_short, 'unchanged'
    else:
        kept = cur_short.replace(rules.UNVERIFIED_SUFFIX, '')
        if level_value:
            short, src = level_value, 'level'
        elif kept and full and _nums(kept) and all(n in _nums(full) for n in _nums(kept)) \
                and len(kept) <= rules.SUMMARY_MAXLEN + 4:
            short, src = kept, 'keep'          # existing summary still consistent with the wiki
        else:
            short, src = _auto_summary(full), 'auto'
        for rx, val in rules.SUMMARY_RULES:
            if re.match(rx, name):
                short, src = val, 'rule'
        if name in rules.SUMMARY_OVERRIDES:
            short, src = rules.SUMMARY_OVERRIDES[name], 'manual'
        short = _tidy_summary(name, short)
        if 'Wiki未検証(重複)' in flags:
            short = short + rules.UNVERIFIED_SUFFIX if short else '重複は未検証'

    return {
        'id': effect_id, 'key': entry['key'], 'name_ja': name, 'deep_id': deep, 'how': how,
        'cur_stack': cur_stack, 'cur_notes': cur_short, 'cur_full': cur_full,
        'prop_stack': stack, 'prop_short': short, 'prop_notes': full, 'short_src': src,
        'flags': flags,
        'w_section': (('深層:' if wiki['deep'] else '通常:') + wiki['section']) if wiki else '',
        'w_name': wiki['name'] if wiki else '', 'w_stack': wiki['stack'] if wiki else '',
        'suggestion': matcher.suggest(name, deep) if how == 'none' else '',
    }


def apply_proposal(entry, p):
    """Write a proposal into an effects_data entry (keeps key order; stackNotesFull after stackNotes)."""
    if p['how'] == 'none':
        return False
    before = dict(entry)
    entry['stackable'] = p['prop_stack']
    entry['stackNotes'] = p['prop_short']
    items = [(k, v) for k, v in entry.items() if k != 'stackNotesFull']
    entry.clear()
    for k, v in items:
        entry[k] = v
        if k == 'stackNotes' and p['prop_notes']:
            entry['stackNotesFull'] = p['prop_notes']
    return entry != before
