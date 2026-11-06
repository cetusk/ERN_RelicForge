/**
 * Public guide page (web/guide.html): キャラ図鑑, 効果カタログ, ビルド一覧 and キャラ別の評価と数値, without a save file.
 *
 * Every tab uses the app's rendering (relic-guide.js): ビルド一覧 and キャラ別の評価と数値 are parts of the
 * キャラ図鑑 page. The effect catalog lists released relic effects only (releasedRelicEffects in relic-effects.js
 * drops every id marked "unreleased").
 */

const GP = {
  lang: 'ja',
  tab: 'characters',
  character: '',
  data: null,          // { effects, profiles, suggest, released }
};
// Data files are fetched with revalidation (same as the app), so an update shows without a hard reload
const GP_FETCH = { cache: 'no-cache' };
const GP_TABS = ['characters', 'effects', 'builds', 'evaluations'];
// The parts of the キャラ図鑑 page each character tab shows (GUIDE_SECTIONS in relic-guide.js)
const GP_SECTIONS = {
  characters: GUIDE_SECTIONS,
  builds: ['builds'],
  evaluations: ['stats', 'suggest', 'demerits', 'important', 'useless', 'contested', 'changes'],
};

const gpEsc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const gpText = (ja, en) => (GP.lang === 'ja' ? ja : en);

function gpStorage(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch (e) { /* storage may be blocked; the page works without it */ }
  return null;
}

async function gpLoad() {
  const get = async (f) => {
    const r = await fetch(`../resources/${f}`, GP_FETCH);
    if (!r.ok) throw new Error(`${f}: ${r.status}`);
    return r.json();
  };
  const [effects, profiles, suggest] = await Promise.all([get('effects_data.json'), get('character_profiles.json'), get('build_suggest.json')]);
  GP.data = { effects, profiles, suggest, released: releasedRelicEffects(effects) };
  GP.names = {};
  for (const e of GP.data.released) GP.names[e.key] = e;
}

// ---------------------------------------------------------------- キャラ図鑑, ビルド一覧, キャラ別の評価と数値

function gpRenderCharacters(tab) {
  const el = document.getElementById(`gp-${tab}`);
  const ja = GP.lang === 'ja';
  const chars = Object.keys(GP.data.profiles.characters);
  if (!chars.includes(GP.character)) GP.character = chars[0];
  // only released effects have a name here; the guide data never refers to unreleased ones (checked by tests)
  const effectName = (key) => (GP.names[key] ? (ja ? GP.names[key].name_ja : GP.names[key].name_en) : key);
  el.innerHTML = `<div class="guide-scroll-area">${renderCharacterGuide({
    character: GP.character, profiles: GP.data.profiles, suggest: GP.data.suggest, ja, effectName, standalone: true,
    sections: GP_SECTIONS[tab],
  })}</div>`;
}

Object.keys(GP_SECTIONS).forEach((tab) => {
  const el = document.getElementById(`gp-${tab}`);
  el.addEventListener('click', (e) => {
    const chip = e.target.closest('.guide-char');
    if (chip) {
      GP.character = chip.dataset.character;   // the same character stays selected across the tabs
      gpStorage('gp-character', GP.character);
      gpRenderCharacters(tab);
      return;
    }
    const toggle = e.target.closest('.guide-toggle-builds');
    if (toggle) el.querySelectorAll('.guide-build').forEach((d) => { d.open = toggle.dataset.open === '1'; });
  });
});

// ---------------------------------------------------------------- 効果カタログ

const gpCollapsed = new Set();

function gpRenderEffectFilters() {
  const sel = document.getElementById('gp-effects-category');
  const cur = sel.value;
  sel.innerHTML = `<option value="">${gpText('すべて', 'All')}</option>` +
    EFFECT_CATEGORIES.map((c) => `<option value="${c.id}">${gpEsc(GP.lang === 'ja' ? c.ja : c.en)}</option>`).join('');
  sel.value = cur;
}

function gpRenderEffects() {
  const ja = GP.lang === 'ja';
  const q = document.getElementById('gp-effects-search').value.trim().toLowerCase();
  const cat = document.getElementById('gp-effects-category').value;
  const deep = document.getElementById('gp-effects-deep').value;
  const stack = document.getElementById('gp-effects-stack').value;
  const all = GP.data.released;
  const list = all.filter((e) => {
    if (q && !e.name_ja.toLowerCase().includes(q) && !e.name_en.toLowerCase().includes(q)) return false;
    if (cat && e.category !== cat) return false;
    if (deep === 'yes' && !e.deepOnly) return false;
    if (deep === 'no' && e.deepOnly) return false;
    if (stack === 'yes' && e.stackable !== true) return false;
    if (stack === 'no' && e.stackable !== false) return false;
    if (stack === 'conditional' && e.stackable !== 'conditional') return false;
    return true;
  });
  document.getElementById('gp-effects-count').textContent = ja ? `${list.length} / ${all.length} 件` : `${list.length} / ${all.length}`;
  const groups = new Map(EFFECT_CATEGORIES.map((c) => [c.id, []]));
  for (const e of list) (groups.get(e.category) || groups.get('other')).push(e);
  document.getElementById('gp-effects-list').innerHTML = EFFECT_CATEGORIES.map((c) => {
    const items = groups.get(c.id);
    if (!items.length) return '';
    const closed = gpCollapsed.has(c.id);
    return `<div class="catalog-group-header${closed ? ' collapsed' : ''}" data-cat="${c.id}"><span class="catalog-group-arrow">&#9660;</span>
        <span>${gpEsc(ja ? c.ja : c.en)}</span><span class="catalog-group-count">(${items.length})</span></div>
      <div class="catalog-group-tiles gp-tiles${closed ? ' collapsed' : ''}" data-cat="${c.id}">${items.map((e) => renderEffectCard(e, { ja })).join('')}</div>`;
  }).join('');
}

['gp-effects-search', 'gp-effects-category', 'gp-effects-deep', 'gp-effects-stack'].forEach((id) => {
  document.getElementById(id).addEventListener('input', gpRenderEffects);
});
document.getElementById('gp-effects-list').addEventListener('click', (e) => {
  const head = e.target.closest('.catalog-group-header');
  if (head) {
    const id = head.dataset.cat;
    if (gpCollapsed.has(id)) gpCollapsed.delete(id);
    else gpCollapsed.add(id);
    gpRenderEffects();
    return;
  }
  const card = e.target.closest('.catalog-card.has-full');
  if (card) {
    const full = card.querySelector('.catalog-card-notes-full');
    full.hidden = !full.hidden;
    card.classList.toggle('expanded', !full.hidden);
  }
});

// ---------------------------------------------------------------- tabs, language

function gpShow(tab) {
  GP.tab = GP_TABS.includes(tab) ? tab : 'characters';
  document.querySelectorAll('.gp-tabs .tab').forEach((t) => t.classList.toggle('active', t.dataset.tab === GP.tab));
  GP_TABS.forEach((t) => { document.getElementById(`gp-${t}`).hidden = t !== GP.tab; });
  if (!GP.data) return;
  if (GP.tab === 'effects') gpRenderEffects();
  else gpRenderCharacters(GP.tab);
}

function gpApplyLang() {
  document.documentElement.lang = GP.lang;
  const t = (id, text) => { document.getElementById(id).textContent = text; };
  t('gp-subtitle', gpText('キャラ図鑑・カタログ', 'Characters & catalogs'));
  t('gp-source-label', gpText('参照', 'Source'));
  t('gp-tab-characters', gpText('キャラ図鑑', 'Characters'));
  t('gp-tab-effects', gpText('効果カタログ', 'Effect Catalog'));
  t('gp-tab-builds', gpText('ビルド一覧', 'Build Templates'));
  t('gp-tab-evaluations', gpText('キャラ別の評価と数値', 'Character Evaluations'));
  t('gp-effects-category-label', gpText('カテゴリ:', 'Category:'));
  t('gp-effects-deep-label', gpText('通常/深層:', 'Normal/Deep:'));
  t('gp-effects-stack-label', gpText('重複:', 'Stacking:'));
  document.getElementById('gp-effects-search').placeholder = gpText('効果名で検索 (日本語 / English)...', 'Search effects (Japanese / English)...');
  const deep = document.getElementById('gp-effects-deep').options;
  deep[0].textContent = gpText('すべて', 'All'); deep[1].textContent = gpText('通常の遺物にも付く', 'Also on normal relics'); deep[2].textContent = gpText('深層のみ', 'Deep only');
  const stack = document.getElementById('gp-effects-stack').options;
  stack[0].textContent = gpText('すべて', 'All'); stack[1].textContent = gpText('○ 重複可', '○ Stackable');
  stack[2].textContent = gpText('× 重複不可', '× No Stack'); stack[3].textContent = gpText('△ 条件付き', '△ Conditional');
  gpRenderEffectFilters();
}

document.getElementById('gp-lang').addEventListener('change', (e) => {
  GP.lang = e.target.value === 'en' ? 'en' : 'ja';
  gpStorage('gp-lang', GP.lang);
  gpApplyLang();
  gpShow(GP.tab);
});
window.addEventListener('hashchange', () => gpShow(location.hash.slice(1)));

(async () => {
  GP.lang = gpStorage('gp-lang') === 'en' ? 'en' : 'ja';
  GP.character = gpStorage('gp-character') || '';
  document.getElementById('gp-lang').value = GP.lang;
  gpApplyLang();
  gpShow(location.hash.slice(1));
  try {
    await gpLoad();
  } catch (err) {
    document.querySelector('.gp-main').insertAdjacentHTML('afterbegin',
      `<p class="gp-loading">${gpText('データの読み込みに失敗しました', 'Could not load the data')}: ${gpEsc(err.message || err)}</p>`);
    return;
  }
  gpShow(GP.tab);
})();
