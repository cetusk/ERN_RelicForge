/**
 * キャラ図鑑 — one character's numbers, traits, how the build suggestion treats them, the known builds and
 * the research behind it (神攻略wiki). Pure rendering: returns HTML; app.js wires the tab and the clicks.
 *
 * Data: resources/character_profiles.json (stats, traits, demerit evaluations, version changes) and
 * resources/build_suggest.json (staples, builds, per-character rules, favoured weapon types).
 * The content is Japanese (taken from the Japanese wiki); headings follow the display language.
 */

const GUIDE_TEXT = {
  ja: {
    stats: '基本データ', traits: '特性', suggest: 'ビルド提案での扱い', builds: '定番のビルド', general: '汎用', targeted: '特定の相手向け',
    demerits: 'デメリットの評価（調査の一覧）', important: '必須・重要な効果（参考）', useless: '意味がない・合わない効果（参考）',
    contested: '意見が割れている点', changes: '性能変更の履歴', favored: '出やすい武器種', staples: '定番の効果',
    avoid: '深き夜で避けるデメリット', unused: '提案に使わない効果', none: 'なし', page: '神攻略wiki のページ',
    updated: '最終更新', aim: '狙い', mode: 'モード', target: '相手', vessel: '献器', source: '出典', suggestThis: 'このビルドで提案',
    must: '必須', rec: '推奨', opt: '任意', avoidTier: '避けたい', body: '本文', comment: 'コメント（一致）',
    effect: '効果', from: '出典', verdict: '評価', posts: '投稿（許容／避ける）', decision: '判定', why: '理由',
    foot: (d) => `出典は神攻略wiki のみ（${d} 調査）。評価の使い方: 本文を主に使い、コメント欄は同じ評価の投稿が 3 件以上かつ反対の 2 倍以上のときだけ使う。関係する性能変更より前の投稿は数えない。`,
    count: (n) => `${n} 件`,
  },
  en: {
    stats: 'Numbers', traits: 'Traits', suggest: 'In Build Suggestion', builds: 'Known builds', general: 'General', targeted: 'For a specific boss',
    demerits: 'Demerit evaluations (research)', important: 'Important effects (reference)', useless: 'Effects that do not suit (reference)',
    contested: 'Split opinions', changes: 'Balance changes', favored: 'Weapon types found more often', staples: 'Staple effects',
    avoid: 'Demerits avoided in Deep of Night', unused: 'Effects not used', none: 'None', page: 'Wiki page',
    updated: 'updated', aim: 'Aim', mode: 'Mode', target: 'Target', vessel: 'Vessel', source: 'Source', suggestThis: 'Suggest with this build',
    must: 'Required', rec: 'Preferred', opt: 'Nice to have', avoidTier: 'Avoid', body: 'wiki text', comment: 'comments (agreed)',
    effect: 'Effect', from: 'From', verdict: 'Rating', posts: 'Posts (accept / avoid)', decision: 'Result', why: 'Why',
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
    : `<details class="guide-card"><summary><h3>${title}</h3></summary>${body}</details>`);

  const selector = `<div class="guide-chars" role="group">${chars.map((c) => `<button type="button" class="suggest-chip guide-char" data-character="${guideEsc(c)}" aria-pressed="${c === ch}">${guideEsc(o.charName ? o.charName(c) : c)}</button>`).join('')}</div>`;

  const head = `<div class="guide-head"><h2>${guideEsc(o.charName ? o.charName(ch) : ch)}</h2>
    <span class="guide-muted">${guideLink(p.page.url, T.page)}${p.page.last_updated ? `（${T.updated} ${guideEsc(p.page.last_updated)}）` : ''}</span></div>`;

  const stats = card(T.stats, `<dl class="guide-stats">${Object.entries(p.stats).map(([k, v]) => `<dt>${guideEsc(k)}</dt><dd>${guideEsc(v)}</dd>`).join('')}</dl>`);
  const traits = card(T.traits, `<ul class="guide-list">${p.traits.map((t) => `<li><b>${guideEsc(t.what)}</b>: ${guideEsc(t.value)}</li>`).join('')}</ul>`);

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

  // Known builds
  const builds = (sg.builds || []).filter((b) => b.character === ch);
  const buildHtml = (b) => `<details class="guide-build"><summary><span class="guide-build-name">${guideEsc(b.name)}</span>
      <span class="guide-muted">${guideEsc([b.aim, b.mode, b.target].filter(Boolean).join(' ／ '))}</span></summary>
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
