/**
 * キャラ図鑑 — one character's numbers, traits, how the build suggestion treats them, the build templates and
 * the research behind it (神攻略wiki). Pure rendering: returns HTML; app.js wires the tab and the clicks.
 *
 * Data: resources/character_profiles.json (stats, traits, demerit evaluations, version changes) and
 * resources/build_suggest.json (staples, builds, per-character rules, favoured weapon types).
 * The content is Japanese (taken from the Japanese wiki); headings follow the display language.
 */

const GUIDE_TEXT = {
  ja: {
    stats: '基本データ', traits: '特性', suggest: 'ビルド提案での扱い', builds: 'ビルドのテンプレート', general: '汎用', targeted: '特定の相手向け',
    demerits: 'デメリットの評価（調査の一覧）', important: '必須・重要な効果（参考）', useless: '意味がない・合わない効果（参考）',
    contested: '意見が割れている点', changes: '性能変更の履歴', favored: '出やすい武器種', staples: '定番の効果',
    avoid: '深き夜で避けるデメリット', unused: '提案に使わない効果', none: 'なし', page: '神攻略wiki のページ',
    updated: '最終更新', aim: '狙い', mode: 'モード', target: '相手', vessel: '献器', source: '出典', suggestThis: 'このビルドで提案',
    must: '必須', rec: '推奨', opt: '任意', avoidTier: '避けたい', body: '本文', comment: 'コメント（一致）',
    effect: '効果', from: '出典', verdict: '評価', posts: '投稿（許容／避ける）', decision: '判定', why: '理由',
    figLegend: '「n位/10」は全 10 キャラでの順位。棒にマウスを乗せると全キャラの値が出ます。', favoredWeapon: '得意武器',
    figRanks: '能力値の補正ランク', figLv15: 'Lv15 の HP・FP・スタミナ', figDodge: '回避の無敵時間（60fps）', figPoise: '強靭度',
    figCut: 'カット率（相対値）', figCutNote: '各属性で最も被ダメージが大きいキャラを 0% とした値', figResist: '状態異常耐性（Lv15、発症までの被弾回数）',
    poise: { high: '高い', low: '低い' }, poiseNote: '高いのは守護者・無頼漢。キャラごとの数値は Wiki にない', rankOf: (n, total) => `${n}位/${total}`, single: '単発', most: '最多', least: '最少',
    showDetail: '詳細を見る', hideDetail: '閉じる', openAll: 'すべて開く', closeAll: 'すべて閉じる', expand: '開く',
    buildsLead: '神攻略wiki のキャラページとビルド投稿から集めた組み合わせの例です。行を押すと効果が開きます。',
    traitGroups: { stats: '能力値', defense: '守り（回避・強靭度・カット率・耐性）', kit: 'スキル・アーツ・アビリティ', play: '立ち回り・役割' },
    foot: (d) => `出典は神攻略wiki のみ（${d} 調査）。評価の使い方: 本文を主に使い、コメント欄は同じ評価の投稿が 3 件以上かつ反対の 2 倍以上のときだけ使う。関係する性能変更より前の投稿は数えない。`,
    count: (n) => `${n} 件`,
  },
  en: {
    stats: 'Numbers', traits: 'Traits', suggest: 'In Build Suggestion', builds: 'Build templates', general: 'General', targeted: 'For a specific boss',
    demerits: 'Demerit evaluations (research)', important: 'Important effects (reference)', useless: 'Effects that do not suit (reference)',
    contested: 'Split opinions', changes: 'Balance changes', favored: 'Weapon types found more often', staples: 'Staple effects',
    avoid: 'Demerits avoided in Deep of Night', unused: 'Effects not used', none: 'None', page: 'Wiki page',
    updated: 'updated', aim: 'Aim', mode: 'Mode', target: 'Target', vessel: 'Vessel', source: 'Source', suggestThis: 'Suggest with this build',
    must: 'Required', rec: 'Preferred', opt: 'Nice to have', avoidTier: 'Avoid', body: 'wiki text', comment: 'comments (agreed)',
    effect: 'Effect', from: 'From', verdict: 'Rating', posts: 'Posts (accept / avoid)', decision: 'Result', why: 'Why',
    figLegend: '"#n/10" is the rank among all 10 characters. Hover a bar for every character.', favoredWeapon: 'Favoured weapon',
    figRanks: 'Stat scaling ranks', figLv15: 'HP / FP / Stamina at Lv15', figDodge: 'Dodge invincibility (60 fps)', figPoise: 'Poise',
    figCut: 'Damage negation (relative)', figCutNote: '0% = the character that takes the most damage of that type', figResist: 'Status resistance (Lv15, hits until it triggers)',
    poise: { high: 'High', low: 'Low' }, poiseNote: 'High for Guardian and Raider; the wiki has no numbers per character', rankOf: (n, total) => `#${n}/${total}`, single: 'Single', most: 'most', least: 'least',
    showDetail: 'Details', hideDetail: 'Close', openAll: 'Open all', closeAll: 'Close all', expand: 'Open',
    buildsLead: 'Example sets from the wiki character pages and build posts. Click a row to see its effects.',
    traitGroups: { stats: 'Stats', defense: 'Defense (dodge, poise, negation, resistance)', kit: 'Skill, Art & Ability', play: 'Playstyle & role' },
    foot: (d) => `From the Japanese Kamikouryaku wiki only (researched ${d}); the content is in Japanese.`,
    count: (n) => `${n}`,
  },
};
const GUIDE_VERDICT = { accept: '許容', avoid: '避けたい', mixed: '割れる', depends: '条件次第', must: '必須', strong: '重要', nice: 'あると良い' };
const GUIDE_DECISION = { accept: '許容', avoid: '避けたい', mixed: '割れる（変えない）' };
const GUIDE_KIND = { buff: '上方', nerf: '下方', fix: '不具合修正', change: '変更', add: '追加' };

function guideEsc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// A wiki URL's page name (e.g. 「ビルド投稿/拳追跡者」) as the link text
function guideWikiTitle(url) {
  try {
    return decodeURIComponent(String(url).split('?')[1] || url);
  } catch (e) {
    return url;
  }
}

function guideChevron() {
  return typeof iconSvg === 'function' ? iconSvg('chevron-right', 14) : '▸';
}

// Trait headings vary per character; sort them into four groups by their wording
function guideTraitGroup(what) {
  const w = String(what || '');
  if (/スキル|アーツ|アビリティ|トランス|探究|共感術|携行知識|苔薬|強化版/.test(w)) return 'kit';
  if (/立ち回り|役割|救助|火力|ファーム|方針|ルーン|初期装備|出撃時の武器|得意武器|混成魔法|攻め|神秘と状態異常|使い方|生存力の位置づけ/.test(w)) return 'play';
  if (/耐性|回避|強靭|カット|耐久|盾|その場回避|斬り下がり|自衛/.test(w)) return 'defense';
  return 'stats';
}

const GUIDE_RANKS = ['D', 'C', 'B', 'A', 'S'];

// 基本データ as charts: rank bars, value bars with the rank among all characters, pips. The favoured weapon stays text
function guideFigures(ch, profiles, T) {
  const chars = Object.keys(profiles.characters);
  const fig = (c) => profiles.characters[c].figures || {};
  const mine = fig(ch);
  if (!mine.lv15) return '';
  const fmt = (v, unit) => `${Number.isInteger(v) ? v : v.toFixed(1)}${unit || ''}`;
  // value: this character's; values: [{c, v}] for every character; scale: the bar's full length
  const bar = (label, value, values, unit, scale) => {
    const max = scale || Math.max(...values.map((x) => x.v));
    const rank = 1 + values.filter((x) => x.v > value).length;
    const tip = values.slice().sort((a, b) => b.v - a.v).map((x) => `${x.c} ${fmt(x.v, unit)}`).join('\n');
    return `<div class="gf-row" title="${guideEsc(tip)}"><span class="gf-label">${guideEsc(label)}</span>
      <span class="gf-track" role="img" aria-label="${guideEsc(`${label} ${fmt(value, unit)}`)}"><span class="gf-fill" style="width:${(100 * value / max).toFixed(2)}%"></span></span>
      <span class="gf-value">${guideEsc(fmt(value, unit))}<small>${guideEsc(T.rankOf(rank, values.length))}</small></span></div>`;
  };
  const all = (get) => chars.map((c) => ({ c, v: get(fig(c)) })).filter((x) => typeof x.v === 'number');

  const ranks = Object.entries(mine.ranks).map(([k, r]) => {
    const n = GUIDE_RANKS.indexOf(r) + 1;
    return `<div class="gf-row"><span class="gf-label">${guideEsc(k)}</span>
      <span class="gf-steps" role="img" aria-label="${guideEsc(`${k} ${r}`)}">${GUIDE_RANKS.map((x, i) => `<span class="gf-step${i < n ? ' on' : ''}"></span>`).join('')}</span>
      <span class="gf-value gf-letter">${guideEsc(r)}</span></div>`;
  }).join('');
  const lv15 = ['HP', 'FP', 'スタミナ'].map((k) => bar(k, mine.lv15[k], all((f) => f.lv15 && f.lv15[k]))).join('');
  const dodgeAll = all((f) => f.dodge && f.dodge.invuln);
  const dodgeMax = Math.max(...chars.flatMap((c) => [fig(c).dodge.invuln, ...fig(c).dodge.extra.map((x) => x.invuln)]));
  const dodge = bar(mine.dodge.extra.some((x) => x.label === '連続') ? T.single : mine.dodge.kind, mine.dodge.invuln, dodgeAll, 'F', dodgeMax) +
    mine.dodge.extra.map((x) => bar(x.label, x.invuln, [...dodgeAll.filter((y) => y.c !== ch), { c: ch, v: x.invuln }], 'F', dodgeMax)).join('');
  const poise = `<span class="gf-pill gf-${mine.poise}">${guideEsc(T.poise[mine.poise])}</span>`;
  const cutMax = Math.max(...chars.flatMap((c) => Object.values(fig(c).cut || {})));
  const cut = Object.entries(mine.cut).map(([k, v]) => bar(k, v, all((f) => f.cut && f.cut[k]), '%', cutMax)).join('');
  const pipMax = Math.max(...chars.flatMap((c) => Object.values(fig(c).resist || {})));
  const resist = Object.entries(mine.resist).map(([k, v]) => {
    const others = all((f) => f.resist && f.resist[k]).map((x) => x.v);
    const tip = all((f) => f.resist && f.resist[k]).map((x) => `${x.c} ${x.v}`).join('\n');
    const note = v === Math.max(...others) && v > Math.min(...others) ? T.most : v === Math.min(...others) && v < Math.max(...others) ? T.least : '';
    return `<div class="gf-row" title="${guideEsc(tip)}"><span class="gf-label">${guideEsc(k)}</span>
      <span class="gf-pips" role="img" aria-label="${guideEsc(`${k} ${v}`)}">${Array.from({ length: pipMax }, (_, i) => `<span class="gf-pip${i < v ? ' on' : ''}"></span>`).join('')}</span>
      <span class="gf-value">${v}${note ? `<small>${note}</small>` : ''}</span></div>`;
  }).join('');
  const block = (title, body, note) => `<div class="gf-block"><h4>${title}</h4>${note ? `<p class="guide-muted">${note}</p>` : ''}${body}</div>`;
  const weapon = profiles.characters[ch].stats['得意武器'];
  return `<section class="guide-card"><h3>${T.stats}</h3>
    ${weapon ? `<dl class="guide-stats"><dt>${T.favoredWeapon}</dt><dd>${guideEsc(weapon)}</dd></dl>` : ''}
    <p class="guide-muted gf-legend">${T.figLegend}</p><div class="gf-grid">
    ${block(T.figRanks, ranks)}${block(T.figLv15, lv15)}${block(T.figDodge, dodge)}${block(T.figPoise, poise, T.poiseNote)}${block(T.figCut, cut, T.figCutNote)}${block(T.figResist, resist)}
  </div></section>`;
}

function guideLink(url, text) {
  return url ? `<a href="${guideEsc(url)}" target="_blank" rel="noopener noreferrer">${guideEsc(text)}</a>` : guideEsc(text);
}

/**
 * @param {object} o  { character, profiles, suggest, effectName(key) -> name, ja }
 * @returns {string} HTML of the character selector and the selected character's page
 */
function renderCharacterGuide(o) {
  const T = o.ja ? GUIDE_TEXT.ja : GUIDE_TEXT.en;
  const chars = Object.keys(o.profiles.characters);
  const ch = chars.includes(o.character) ? o.character : chars[0];
  const p = o.profiles.characters[ch];
  const sg = o.suggest || {};
  const name = (k) => o.effectName(k);
  const effList = (keys, cls) => (keys && keys.length
    ? `<span class="guide-effs">${keys.map((k) => `<span class="guide-eff ${cls}">${guideEsc(name(k))}</span>`).join('')}</span>`
    : `<span class="guide-muted">${T.none}</span>`);
  const card = (title, body, open = true) => (open
    ? `<section class="guide-card"><h3>${title}</h3>${body}</section>`
    : `<details class="guide-card guide-fold"><summary><span class="guide-chevron">${guideChevron()}</span><h3>${title}</h3>
        <span class="guide-hint"><span class="guide-hint-closed">${T.expand}</span><span class="guide-hint-open">${T.hideDetail}</span></span></summary>${body}</details>`);

  const selector = `<div class="guide-chars" role="group">${chars.map((c) => `<button type="button" class="suggest-chip guide-char" data-character="${guideEsc(c)}" aria-pressed="${c === ch}">${guideEsc(o.charName ? o.charName(c) : c)}</button>`).join('')}</div>`;

  const head = `<div class="guide-head"><h2>${guideEsc(o.charName ? o.charName(ch) : ch)}</h2>
    <span class="guide-muted">${guideLink(p.page.url, T.page)}${p.page.last_updated ? `（${T.updated} ${guideEsc(p.page.last_updated)}）` : ''}</span></div>`;

  // charts when the numbers are there; otherwise the text list
  const stats = guideFigures(ch, o.profiles, T) ||
    card(T.stats, `<dl class="guide-stats">${Object.entries(p.stats).map(([k, v]) => `<dt>${guideEsc(k)}</dt><dd>${guideEsc(v)}</dd>`).join('')}</dl>`);
  const groups = { stats: [], defense: [], kit: [], play: [] };
  for (const t of p.traits) groups[guideTraitGroup(t.what)].push(t);
  const traits = card(T.traits, `<div class="guide-traits">${Object.entries(groups).filter(([, items]) => items.length).map(([g, items]) => `
    <div class="guide-trait-group guide-trait-${g}"><h4>${guideEsc(T.traitGroups[g])}</h4>
      ${items.map((t) => `<div class="guide-trait"><div class="guide-trait-name">${guideEsc(t.what)}</div><div class="guide-trait-value">${guideEsc(t.value)}</div></div>`).join('')}
    </div>`).join('')}</div>`);

  // How the build suggestion treats this character
  const st = (sg.staples || {})[ch] || { rec: [], opt: [], avoid: [] };
  const rules = (sg.characters || {})[ch] || { avoid: [], useless: [] };
  const favored = (sg.favoredWeapons || {})[ch] || [];
  const avoidRows = rules.avoid.length ? `<ul class="guide-list">${rules.avoid.map((x) => `<li><span class="guide-eff guide-x">${guideEsc(name(x.key))}</span> ${guideEsc(x.why)} <span class="guide-tag">${x.tier === 'body' ? T.body : T.comment}</span></li>`).join('')}</ul>` : `<span class="guide-muted">${T.none}</span>`;
  const unusedByWhy = new Map();
  for (const x of rules.useless) {
    if (!unusedByWhy.has(x.why)) unusedByWhy.set(x.why, []);
    unusedByWhy.get(x.why).push(x.key);
  }
  const unused = unusedByWhy.size ? `<ul class="guide-list">${[...unusedByWhy].map(([why, keys]) => `<li>${effList(keys, 'guide-x')} ${guideEsc(why)}</li>`).join('')}</ul>` : `<span class="guide-muted">${T.none}</span>`;
  const suggest = card(T.suggest, `<dl class="guide-rules">
    <dt>${T.favored}</dt><dd>${favored.length ? guideEsc(favored.join('・')) : `<span class="guide-muted">${T.none}</span>`}</dd>
    <dt>${T.staples}</dt><dd><div class="guide-tier"><span class="guide-tier-label">${T.rec}</span>${effList(st.rec, 'guide-rec')}</div>
      <div class="guide-tier"><span class="guide-tier-label">${T.opt}</span>${effList(st.opt, 'guide-opt')}</div>
      ${st.avoid.length ? `<div class="guide-tier"><span class="guide-tier-label">${T.avoidTier}</span>${effList(st.avoid, 'guide-x')}</div>` : ''}</dd>
    <dt>${T.avoid}</dt><dd>${avoidRows}</dd>
    <dt>${T.unused}</dt><dd>${unused}</dd></dl>`);

  // Build templates
  const builds = (sg.builds || []).filter((b) => b.character === ch);
  const buildHtml = (b) => `<details class="guide-build"><summary>
      <span class="guide-chevron">${guideChevron()}</span>
      <span class="guide-build-title"><span class="guide-build-name">${guideEsc(b.name)}</span>
        <span class="guide-muted">${guideEsc([b.aim, b.mode, b.target].filter(Boolean).join(' ／ '))}</span></span>
      <span class="guide-hint"><span class="guide-hint-closed">${T.showDetail}</span><span class="guide-hint-open">${T.hideDetail}</span></span></summary>
    <div class="guide-build-body">
      ${[['must', T.must, 'guide-must'], ['rec', T.rec, 'guide-rec'], ['opt', T.opt, 'guide-opt'], ['avoid', T.avoidTier, 'guide-x']]
        .filter(([k]) => b[k].length).map(([k, label, cls]) => `<div class="guide-tier"><span class="guide-tier-label">${label}</span>${effList(b[k], cls)}</div>`).join('')}
      ${b.vessel ? `<p class="guide-muted">${T.vessel}: ${guideEsc(b.vessel)}</p>` : ''}
      ${b.sources.length ? `<p class="guide-muted">${T.source}: ${b.sources.map((u) => guideLink(u, guideWikiTitle(u))).join('、')}</p>` : ''}
      <button type="button" class="btn-secondary guide-suggest" data-build="${guideEsc(b.id)}">${T.suggestThis}</button>
    </div></details>`;
  const general = builds.filter((b) => !b.target);
  const targeted = builds.filter((b) => b.target);
  const buildsCard = card(`${T.builds}（${T.count(builds.length)}）`,
    `<div class="guide-builds-head"><p class="guide-muted">${T.buildsLead}</p>
      <span class="guide-builds-actions"><button type="button" class="btn-secondary guide-toggle-builds" data-open="1">${T.openAll}</button>
      <button type="button" class="btn-secondary guide-toggle-builds" data-open="0">${T.closeAll}</button></span></div>` +
    (general.length ? `<h4>${T.general}</h4>${general.map(buildHtml).join('')}` : '') +
    (targeted.length ? `<h4>${T.targeted}</h4>${targeted.map(buildHtml).join('')}` : ''));

  // Research (collapsed)
  const demRows = p.demerits.map((x) => `<tr><td>${guideEsc(x.name)}</td><td>${guideEsc(x.source)}</td><td>${guideEsc(GUIDE_VERDICT[x.verdict] || x.verdict || '—')}</td>
    <td class="guide-num">${x.accept_posts}／${x.avoid_posts}</td><td>${guideEsc(GUIDE_DECISION[x.decision] || '—')}</td><td>${guideEsc(x.why)}</td></tr>`).join('');
  const demerits = card(T.demerits, `<div class="guide-scroll"><table class="guide-table"><thead><tr><th>${T.effect}</th><th>${T.from}</th><th>${T.verdict}</th><th>${T.posts}</th><th>${T.decision}</th><th>${T.why}</th></tr></thead><tbody>${demRows}</tbody></table></div>`, false);
  const refList = (items) => `<ul class="guide-list">${items.map((x) => `<li>${x.level ? `<span class="guide-tag">${guideEsc(GUIDE_VERDICT[x.level] || x.level)}</span> ` : ''}<b>${guideEsc(x.name)}</b>（${guideEsc(x.source)}）: ${guideEsc(x.why)}</li>`).join('')}</ul>`;
  const important = p.important.length ? card(T.important, refList(p.important), false) : '';
  const useless = p.useless.length ? card(T.useless, refList(p.useless), false) : '';
  const contested = p.contested.length ? card(T.contested, `<ul class="guide-list">${p.contested.map((x) => `<li><b>${guideEsc(x.topic)}</b><ul>${x.views.map((v) => `<li>${guideEsc(v)}</li>`).join('')}</ul></li>`).join('')}</ul>`, false) : '';
  const changes = p.changes.length ? card(T.changes, `<ul class="guide-list">${p.changes.map((x) => `<li><span class="guide-num">${guideEsc(x.date)}</span> <span class="guide-tag">${guideEsc(GUIDE_KIND[x.kind] || x.kind)}</span> ${guideEsc(x.text)}</li>`).join('')}</ul>`, false) : '';

  return `${selector}<div class="guide">${head}${stats}${traits}${suggest}${buildsCard}${demerits}${important}${useless}${contested}${changes}
    <p class="guide-foot">${guideEsc(T.foot(o.profiles.researched))}</p></div>`;
}
