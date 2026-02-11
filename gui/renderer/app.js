// === State ===
let relicData = null;       // Full parsed data
let filteredRelics = [];    // After filter/search
let sortColumn = 'sortKey';
let sortDirection = 'desc';
let selectedRelicId = null;
let displayLang = 'ja';    // 'ja' or 'en'
let loadedFileName = '';   // currently loaded filename
let andGroups = [new Set(), new Set(), new Set()]; // AND groups (OR within, AND between)
let activeAndGroup = 0;             // active AND group index
let allUniqueEffects = [];          // unique effects with counts
let collapsedCategories = new Set(); // collapsed category IDs in inspector
let stackingLookup = {};           // effectId -> { stackable, stackNotes }
const AND_GROUP_COLORS = ['#e74c3c', '#3498db', '#2ecc71']; // group indicator colors

// === Tab State ===
let activeTab = 'main';
let optimizerTabs = new Map(); // tabId -> { label, data, params }
let nextTabId = 1;
let vesselsData = null;  // cached vessels_data.json
let optSelectedEffects = new Map(); // effectKey -> priority
let optVesselCollapsed = true;  // vessel list collapsed state
let effectSelectCollapsed = new Set(); // collapsed categories in effect selector

// Priority display labels
const PRIORITY_LABELS = {
  required:             { ja: '必須', en: 'Required' },
  preferred:            { ja: '推奨', en: 'Preferred' },
  nice_to_have:         { ja: '任意', en: 'Nice to have' },
  exclude_required:     { ja: '除外:必須', en: 'Exclude:Required' },
  exclude_preferred:    { ja: '除外:推奨', en: 'Exclude:Preferred' },
  exclude_nice_to_have: { ja: '除外:任意', en: 'Exclude:Nice to have' },
};
const PRIORITY_WEIGHTS = { required: 100, preferred: 10, nice_to_have: 1 };
const CONCENTRATION_BONUS = 5;

// App metadata
const APP_NIGHTREIGN_VERSION = 'v1.03.4';
const APP_LAST_UPDATED = '2026-02-11';

// === Type Display Names ===
const TYPE_LABELS = {
  Relic:       { ja: '通常', en: 'Relic' },
  DeepRelic:   { ja: '深層', en: 'Deep' },
  UniqueRelic: { ja: '固有', en: 'Unique' },
};

// === DOM Elements ===
const btnOpen = document.getElementById('btn-open');
const btnOpenWelcome = document.getElementById('btn-open-welcome');
const btnAutoLoad = document.getElementById('btn-auto-load');
const autoLoadNote = document.getElementById('auto-load-note');
const autoLoadStatus = document.getElementById('auto-load-status');
const headerInfo = document.getElementById('header-info');
const toolbar = document.getElementById('toolbar');
const welcome = document.getElementById('welcome');
const loading = document.getElementById('loading');
const contentArea = document.getElementById('content-area');
const searchInput = document.getElementById('search-input');
const filterType = document.getElementById('filter-type');
// Custom color select
const colorSelectBtn = document.getElementById('color-select-btn');
const colorSelectLabel = document.getElementById('color-select-label');
const colorSelectDropdown = document.getElementById('color-select-dropdown');
let colorFilterValue = '';
const resultCount = document.getElementById('result-count');
const relicTbody = document.getElementById('relic-tbody');
const detailPanel = document.getElementById('detail-panel');
const detailTitle = document.getElementById('detail-title');
const detailBody = document.getElementById('detail-body');
const detailClose = document.getElementById('detail-close');
const filterLang = document.getElementById('filter-lang');

const searchSuggestions = document.getElementById('search-suggestions');
const searchClear = document.getElementById('search-clear');

// Inspector elements
const btnInspector = document.getElementById('btn-inspector');
const btnInspectorLabel = document.getElementById('btn-inspector-label');
const inspectorBackdrop = document.getElementById('inspector-backdrop');
const inspector = document.getElementById('inspector');
const inspectorClose = document.getElementById('inspector-close');
const inspectorSearch = document.getElementById('inspector-search');
const inspectorSearchClear = document.getElementById('inspector-search-clear');
const inspectorEffectList = document.getElementById('inspector-effect-list');
const inspectorSelectedCount = document.getElementById('inspector-selected-count');
const inspectorClear = document.getElementById('inspector-clear');
const inspectorApply = document.getElementById('inspector-apply');

// Tab bar
const tabBar = document.getElementById('tab-bar');

// Export button
const btnExportTable = document.getElementById('btn-export-table');
const btnExportTableLabel = document.getElementById('btn-export-table-label');

// Optimizer inspector elements
const btnOptimizer = document.getElementById('btn-optimizer');
const btnOptimizerLabel = document.getElementById('btn-optimizer-label');
const optimizerBackdrop = document.getElementById('optimizer-backdrop');
const optimizerInspector = document.getElementById('optimizer-inspector');
const optimizerClose = document.getElementById('optimizer-close');
const optCharacter = document.getElementById('opt-character');
const optVesselList = document.getElementById('opt-vessel-list');
const optMode = document.getElementById('opt-mode');
const optEffectsList = document.getElementById('opt-effects-list');
const optAddEffect = document.getElementById('opt-add-effect');
const optCandidates = document.getElementById('opt-candidates');
const optTop = document.getElementById('opt-top');
const optimizerClearBtn = document.getElementById('optimizer-clear');
const optimizerRunBtn = document.getElementById('optimizer-run');
const optVesselHeader = document.getElementById('opt-vessel-header');

// Effect selection inspector elements
const effectSelectBackdrop = document.getElementById('effect-select-backdrop');
const effectSelectInspector = document.getElementById('effect-select-inspector');
const effectSelectClose = document.getElementById('effect-select-close');
const effectSelectSearch = document.getElementById('effect-select-search');
const effectSelectSearchClear = document.getElementById('effect-select-search-clear');
const effectSelectList = document.getElementById('effect-select-list');
const effectSelectClearBtn = document.getElementById('effect-select-clear');
const effectSelectApplyBtn = document.getElementById('effect-select-apply');

// Minimap elements
const minimap = document.getElementById('minimap');
const minimapCanvas = document.getElementById('minimap-canvas');
const minimapSlider = document.getElementById('minimap-slider');
const tableContainer = document.getElementById('table-container');
let suggestionIndex = -1;   // keyboard navigation index
let searchTerms = [];       // cached suggestion candidates

// === Init ===
btnOpen.addEventListener('click', openFile);
btnOpenWelcome.addEventListener('click', openFile);
btnAutoLoad.addEventListener('click', autoLoad);
searchInput.addEventListener('input', () => {
  searchClear.classList.toggle('hidden', !searchInput.value);
  applyFilters();
  updateSuggestions();
});
searchClear.addEventListener('click', () => {
  searchInput.value = '';
  searchClear.classList.add('hidden');
  searchSuggestions.classList.add('hidden');
  applyFilters();
  searchInput.focus();
});
// Color custom select
colorSelectBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  colorSelectDropdown.classList.toggle('hidden');
});
colorSelectDropdown.addEventListener('mousedown', (e) => {
  const opt = e.target.closest('.custom-select-option');
  if (!opt) return;
  colorFilterValue = opt.dataset.value;
  // Update button label with badge
  if (colorFilterValue) {
    colorSelectLabel.innerHTML =
      `<span class="color-badge ${colorFilterValue}"></span>${colorFilterValue}`;
  } else {
    colorSelectLabel.textContent = displayLang === 'ja' ? 'すべて' : 'All';
  }
  // Highlight selected
  colorSelectDropdown.querySelectorAll('.custom-select-option').forEach(o =>
    o.classList.toggle('selected', o.dataset.value === colorFilterValue));
  colorSelectDropdown.classList.add('hidden');
  applyFilters();
});
document.addEventListener('click', () => colorSelectDropdown.classList.add('hidden'));
filterType.addEventListener('change', applyFilters);
detailClose.addEventListener('click', closeDetail);
filterLang.addEventListener('change', () => {
  displayLang = filterLang.value;
  updateLangUI();
  renderTable();
  updateHeaderInfo();
  updateResultCount();
  // Re-render detail if open
  if (selectedRelicId) {
    const relic = filteredRelics.find(r => r.id === selectedRelicId);
    if (relic) showDetail(relic);
  }
});

document.querySelectorAll('th.sortable').forEach(th => {
  th.addEventListener('click', () => {
    const col = th.dataset.sort;
    if (sortColumn === col) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = col;
      sortDirection = col === 'sortKey' ? 'desc' : 'asc';
    }
    updateSortIndicators();
    applyFilters();
  });
});

// === File Open ===
async function openFile() {
  const filePath = await window.api.openFileDialog();
  if (!filePath) return;
  await loadAndDisplay(filePath);
}

async function loadAndDisplay(filePath) {
  showView('loading');
  try {
    relicData = await window.api.parseSaveFile(filePath);
    stackingLookup = await window.api.loadStackingData();
    loadedFileName = filePath.split(/[/\\]/).pop();
    buildSearchTerms();
    buildUniqueEffects();
    andGroups.forEach(g => g.clear());
    updateHeaderInfo();
    toolbar.classList.remove('hidden');
    btnInspector.classList.remove('hidden');
    btnOptimizer.classList.remove('hidden');
    btnExportTable.classList.remove('hidden');
    tabBar.classList.remove('hidden');
    updateInspectorButton();
    updateOptimizerButton();
    sortColumn = 'sortKey';
    sortDirection = 'desc';
    updateSortIndicators();
    applyFilters();
    showView('content');
  } catch (err) {
    alert(`解析エラー:\n${err}`);
    showView('welcome');
    resetAutoLoadUI();
  }
}

// === Auto Load ===
function resetAutoLoadUI() {
  autoLoadStatus.classList.add('hidden');
  autoLoadStatus.innerHTML = '';
  btnAutoLoad.disabled = false;
  btnOpenWelcome.disabled = false;
}

function setAutoLoadStatus(html) {
  autoLoadStatus.innerHTML = html;
  autoLoadStatus.classList.remove('hidden');
}

async function autoLoad() {
  btnAutoLoad.disabled = true;
  btnOpenWelcome.disabled = true;
  setAutoLoadStatus('<div class="status-msg">セーブデータを検索中...</div>');

  try {
    const saveFiles = await window.api.findSaveFiles();

    if (saveFiles.length === 0) {
      setAutoLoadStatus(
        '<div class="status-error">セーブデータが見つかりませんでした</div>' +
        '<div class="status-hint">AppData\\Roaming\\Nightreign\\ 内に NR0000.sl2.bak が見つかりません</div>');
      btnAutoLoad.disabled = false;
      btnOpenWelcome.disabled = false;
      return;
    }

    if (saveFiles.length === 1) {
      await autoLoadFile(saveFiles[0]);
      return;
    }

    // Multiple save files: show selection
    let listHtml = '<div class="status-msg">複数のセーブデータが見つかりました。選択してください:</div>';
    listHtml += '<div class="save-file-list">';
    for (let i = 0; i < saveFiles.length; i++) {
      const sf = saveFiles[i];
      const dt = new Date(sf.mtime);
      const dateStr = dt.toLocaleString('ja-JP');
      listHtml += `<div class="save-file-item" data-idx="${i}">` +
        `<span class="save-id">${sf.id}</span>` +
        `<span class="save-mtime">${dateStr}</span>` +
        '</div>';
    }
    listHtml += '</div>';
    setAutoLoadStatus(listHtml);
    btnOpenWelcome.disabled = false;

    // Attach click handlers to items
    const items = autoLoadStatus.querySelectorAll('.save-file-item');
    items.forEach(item => {
      item.addEventListener('click', async () => {
        const idx = parseInt(item.dataset.idx);
        await autoLoadFile(saveFiles[idx]);
      });
    });
  } catch (err) {
    setAutoLoadStatus(
      `<div class="status-error">エラー: ${err}</div>`);
    btnAutoLoad.disabled = false;
    btnOpenWelcome.disabled = false;
  }
}

async function autoLoadFile(saveFile) {
  btnAutoLoad.disabled = true;
  btnOpenWelcome.disabled = true;
  setAutoLoadStatus(
    '<div class="status-msg">セーブデータを一時フォルダにコピーしています...</div>');

  try {
    const copiedPath = await window.api.autoLoadSave(saveFile.path);
    setAutoLoadStatus(
      '<div class="status-msg">解析中...</div>');
    await loadAndDisplay(copiedPath);
  } catch (err) {
    setAutoLoadStatus(
      `<div class="status-error">コピーまたは解析に失敗しました</div>` +
      `<div class="status-hint">${err}</div>`);
    btnAutoLoad.disabled = false;
    btnOpenWelcome.disabled = false;
  }
}

// === View Management ===
function showView(name) {
  welcome.classList.toggle('hidden', name !== 'welcome');
  loading.classList.toggle('hidden', name !== 'loading');
  contentArea.classList.toggle('hidden', name !== 'content');
  if (name === 'welcome') resetAutoLoadUI();
}

// === Language UI ===
function updateLangUI() {
  const ja = displayLang === 'ja';
  // Welcome screen
  document.getElementById('welcome-msg').textContent = ja
    ? 'セーブファイル (.sl2) を開いて遺物を確認'
    : 'Open a save file (.sl2) to view relics';
  btnAutoLoad.textContent = ja ? '自動で読み込む' : 'Auto Load';
  btnOpenWelcome.textContent = ja ? 'ファイルを選択して開く' : 'Select File';
  autoLoadNote.textContent = ja
    ? '\u203b セーブデータ (.bak) を一時フォルダにコピーしてから読み込みます'
    : '* The save data (.bak) will be copied to a temp folder before loading';
  // Header meta
  document.getElementById('header-meta-version').textContent = ja
    ? `Nightreign ${APP_NIGHTREIGN_VERSION} 対応`
    : `Nightreign ${APP_NIGHTREIGN_VERSION}`;
  document.getElementById('header-meta-updated').textContent = ja
    ? `最終更新: ${APP_LAST_UPDATED}`
    : `Updated: ${APP_LAST_UPDATED}`;
  // Toolbar labels
  document.getElementById('label-color').textContent = ja ? '色:' : 'Color:';
  document.getElementById('label-type').textContent = ja ? 'タイプ:' : 'Type:';
  document.getElementById('label-lang').textContent = ja ? '言語:' : 'Lang:';
  // Search placeholder
  searchInput.placeholder = ja
    ? '効果名で検索 (日本語 / English)...'
    : 'Search effects (Japanese / English)...';
  // Table headers
  document.getElementById('th-color').childNodes[0].textContent = ja ? '色' : 'Color';
  document.getElementById('th-type').childNodes[0].textContent = ja ? 'タイプ' : 'Type';
  document.getElementById('th-item').childNodes[0].textContent = ja ? 'アイテム' : 'Item';
  document.getElementById('th-effects').textContent = ja ? '効果' : 'Effects';
  // Type filter options
  const typeOpts = filterType.options;
  typeOpts[0].textContent = ja ? 'すべて' : 'All';
  typeOpts[1].textContent = ja ? '通常' : 'Relic';
  typeOpts[2].textContent = ja ? '深層' : 'Deep';
  typeOpts[3].textContent = ja ? '固有' : 'Unique';
  // Color filter: update "All" option text and current label if "All" is selected
  const allOpt = colorSelectDropdown.querySelector('[data-value=""]');
  if (allOpt) allOpt.textContent = ja ? 'すべて' : 'All';
  if (!colorFilterValue) {
    colorSelectLabel.textContent = ja ? 'すべて' : 'All';
  }
  // Inspector
  document.getElementById('inspector-title').textContent = ja ? '高度な検索' : 'Advanced Search';
  document.getElementById('inspector-effect-label').textContent = ja ? '効果フィルター' : 'Effect Filter';
  inspectorSearch.placeholder = ja ? '効果名で絞り込み...' : 'Filter effects...';
  inspectorClear.textContent = ja ? 'クリア' : 'Clear';
  inspectorApply.textContent = ja ? '適用' : 'Apply';
  updateInspectorButton();
  updateInspectorCount();
  if (inspector.classList.contains('open')) renderInspectorEffects();
}

function updateHeaderInfo() {
  if (!relicData) return;
  const relics = relicData.relics;
  const normal = relics.filter(r => r.itemType === 'Relic').length;
  const deep = relics.filter(r => r.itemType === 'DeepRelic').length;
  const unique = relics.filter(r => r.itemType === 'UniqueRelic').length;
  const ja = displayLang === 'ja';
  const normalLabel = ja ? '通常' : 'Relic';
  const deepLabel = ja ? '深層' : 'Deep';
  const uniqueLabel = ja ? '固有' : 'Unique';
  const total = relics.length;
  const totalLabel = ja ? '合計' : 'Total';
  const playerLabel = ja ? 'プレイヤー' : 'Player';
  const fileLabel = ja ? 'ファイル' : 'File';
  headerInfo.textContent =
    `${playerLabel}: ${relicData.characterName} | ${totalLabel}: ${total}  (${normalLabel}: ${normal} / ${deepLabel}: ${deep} / ${uniqueLabel}: ${unique}) | ${fileLabel}: ${loadedFileName}`;
}

function typeLabel(itemType) {
  const entry = TYPE_LABELS[itemType];
  return entry ? entry[displayLang] : itemType;
}

// === Result Count ===
function updateResultCount() {
  if (!relicData) return;
  const ja = displayLang === 'ja';
  const hit = filteredRelics.length;
  const total = relicData.totalRelics;
  const nR = filteredRelics.filter(r => r.itemType === 'Relic').length;
  const nD = filteredRelics.filter(r => r.itemType === 'DeepRelic').length;
  const nU = filteredRelics.filter(r => r.itemType === 'UniqueRelic').length;
  const hitLabel = ja ? 'ヒット' : 'hits';
  const normalLabel = ja ? '通常' : 'Relic';
  const deepLabel = ja ? '深層' : 'Deep';
  const uniqueLabel = ja ? '固有' : 'Unique';
  resultCount.textContent =
    `${hit} ${hitLabel}(${normalLabel}: ${nR} / ${deepLabel}: ${nD} / ${uniqueLabel}: ${nU})`;
}

// === Search Suggestions ===
function buildSearchTerms() {
  if (!relicData) { searchTerms = []; return; }
  const termSet = new Set();
  relicData.relics.forEach(r => {
    // Effect names
    r.effects.flat().forEach(e => {
      if (e.name_ja) termSet.add(e.name_ja);
      if (e.name_en) termSet.add(e.name_en);
    });
    // Item names
    if (r.itemNameJa) termSet.add(r.itemNameJa);
    if (r.itemNameEn) termSet.add(r.itemNameEn);
  });
  searchTerms = Array.from(termSet).sort((a, b) => a.localeCompare(b, 'ja'));
}

function updateSuggestions() {
  const query = searchInput.value.toLowerCase().trim();
  suggestionIndex = -1;
  if (!query || query.length < 1 || searchTerms.length === 0) {
    searchSuggestions.classList.add('hidden');
    return;
  }
  const matches = searchTerms
    .filter(t => t.toLowerCase().includes(query))
    .slice(0, 20);
  if (matches.length === 0 || (matches.length === 1 && matches[0].toLowerCase() === query)) {
    searchSuggestions.classList.add('hidden');
    return;
  }
  searchSuggestions.innerHTML = matches.map((m, i) => {
    const idx = m.toLowerCase().indexOf(query);
    const before = m.substring(0, idx);
    const match = m.substring(idx, idx + query.length);
    const after = m.substring(idx + query.length);
    return `<div class="suggestion-item" data-index="${i}">${before}<span class="suggestion-match">${match}</span>${after}</div>`;
  }).join('');
  searchSuggestions.classList.remove('hidden');
}

function selectSuggestion(text) {
  searchInput.value = text;
  searchClear.classList.toggle('hidden', !text);
  searchSuggestions.classList.add('hidden');
  suggestionIndex = -1;
  applyFilters();
}

// Suggestion click
searchSuggestions.addEventListener('mousedown', (e) => {
  const item = e.target.closest('.suggestion-item');
  if (item) selectSuggestion(item.textContent);
});

// Keyboard navigation
searchInput.addEventListener('keydown', (e) => {
  const items = searchSuggestions.querySelectorAll('.suggestion-item');
  if (items.length === 0 || searchSuggestions.classList.contains('hidden')) return;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    suggestionIndex = Math.min(suggestionIndex + 1, items.length - 1);
    items.forEach((el, i) => el.classList.toggle('active', i === suggestionIndex));
    items[suggestionIndex].scrollIntoView({ block: 'nearest' });
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    suggestionIndex = Math.max(suggestionIndex - 1, 0);
    items.forEach((el, i) => el.classList.toggle('active', i === suggestionIndex));
    items[suggestionIndex].scrollIntoView({ block: 'nearest' });
  } else if (e.key === 'Enter' && suggestionIndex >= 0) {
    e.preventDefault();
    selectSuggestion(items[suggestionIndex].textContent);
  } else if (e.key === 'Escape') {
    searchSuggestions.classList.add('hidden');
    suggestionIndex = -1;
  }
});

// Close suggestions on blur
searchInput.addEventListener('blur', () => {
  setTimeout(() => searchSuggestions.classList.add('hidden'), 150);
});
searchInput.addEventListener('focus', () => {
  if (searchInput.value.trim()) updateSuggestions();
});

// === Filter & Sort ===
function applyFilters() {
  if (!relicData) return;

  const query = searchInput.value.toLowerCase().trim();
  const colorFilter = colorFilterValue;
  const typeFilter = filterType.value;

  filteredRelics = relicData.relics.filter(r => {
    if (colorFilter && r.itemColor !== colorFilter) return false;
    if (typeFilter && r.itemType !== typeFilter) return false;
    if (query) {
      const effectTexts = r.effects
        .flat()
        .map(e => `${e.name_ja || ''} ${e.name_en || ''} ${e.key || ''}`)
        .join(' ')
        .toLowerCase();
      const itemText = `${r.itemKey || ''} ${r.itemNameEn || ''} ${r.itemNameJa || ''}`.toLowerCase();
      if (!effectTexts.includes(query) && !itemText.includes(query)) return false;
    }
    // Effect filter: AND between groups, OR within each group
    const activeGroups = andGroups.filter(g => g.size > 0);
    if (activeGroups.length > 0) {
      const relicEffectKeys = r.effects.flat().map(e => e.key);
      if (!activeGroups.every(g => relicEffectKeys.some(k => g.has(k)))) return false;
    }
    return true;
  });

  // Sort
  filteredRelics.sort((a, b) => {
    let va = a[sortColumn];
    let vb = b[sortColumn];
    if (va == null) va = '';
    if (vb == null) vb = '';
    if (typeof va === 'string') va = va.toLowerCase();
    if (typeof vb === 'string') vb = vb.toLowerCase();
    let cmp = va < vb ? -1 : va > vb ? 1 : 0;
    return sortDirection === 'desc' ? -cmp : cmp;
  });

  updateResultCount();
  renderTable();
}

// === Sort Indicators ===
function updateSortIndicators() {
  document.querySelectorAll('th.sortable').forEach(th => {
    th.classList.remove('sort-asc', 'sort-desc');
    if (th.dataset.sort === sortColumn) {
      th.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
    }
  });
}

// === Table Render ===
function renderTable() {
  relicTbody.innerHTML = '';

  const fragment = document.createDocumentFragment();
  filteredRelics.forEach((relic, idx) => {
    const tr = document.createElement('tr');
    if (relic.id === selectedRelicId) tr.classList.add('selected');
    tr.addEventListener('click', () => showDetail(relic));

    // # (row number)
    const tdNum = document.createElement('td');
    tdNum.textContent = idx + 1;
    tdNum.style.color = 'var(--text-muted)';
    tr.appendChild(tdNum);

    // Color
    const tdColor = document.createElement('td');
    tdColor.innerHTML =
      `<span class="color-badge ${relic.itemColor}"></span>` +
      `<span class="color-label">${relic.itemColor || '-'}</span>`;
    tr.appendChild(tdColor);

    // Type
    const tdType = document.createElement('td');
    tdType.innerHTML = `<span class="type-badge ${relic.itemType}">${typeLabel(relic.itemType)}</span>`;
    tr.appendChild(tdType);

    // Item Name
    const tdItem = document.createElement('td');
    tdItem.textContent = displayLang === 'ja'
      ? (relic.itemNameJa || relic.itemNameEn || relic.itemKey)
      : (relic.itemNameEn || relic.itemKey);
    tdItem.style.fontSize = '12px';
    tr.appendChild(tdItem);

    // Effects (single column, language based on displayLang)
    const tdEffects = document.createElement('td');
    tdEffects.innerHTML = relic.effects.map(group => {
      const main = group[0];
      const mainName = displayLang === 'ja'
        ? (main.name_ja || main.name_en || main.key)
        : (main.name_en || main.key);
      let html = `<div class="effect-item">`;
      html += `<div class="effect-main">${mainName}</div>`;
      // Debuffs linked to main effect
      for (let i = 1; i < group.length; i++) {
        const d = group[i];
        const debuffName = displayLang === 'ja'
          ? (d.name_ja || d.name_en || d.key)
          : (d.name_en || d.key);
        html += `<div class="effect-debuff">${debuffName}</div>`;
      }
      html += `</div>`;
      return html;
    }).join('');
    tr.appendChild(tdEffects);

    fragment.appendChild(tr);
  });
  relicTbody.appendChild(fragment);
  renderMinimap();
}

// === Detail Panel ===
function showDetail(relic) {
  selectedRelicId = relic.id;
  detailPanel.classList.remove('hidden');

  const itemName = displayLang === 'ja'
    ? (relic.itemNameJa || relic.itemNameEn || relic.itemKey)
    : (relic.itemNameEn || relic.itemKey);
  detailTitle.textContent = itemName;

  let html = '';

  // Basic info
  const ja = displayLang === 'ja';
  html += `<div class="detail-section">`;
  html += `<h3>${ja ? '基本情報' : 'Basic Info'}</h3>`;
  html += field('ID', relic.id);
  html += field(ja ? 'アイテムID' : 'Item ID', relic.itemId);
  html += field(ja ? 'アイテムKey' : 'Item Key', relic.itemKey);
  html += field(ja ? '色' : 'Color', `<span class="color-badge ${relic.itemColor}"></span> ${relic.itemColor}`);
  html += field(displayLang === 'ja' ? 'タイプ' : 'Type',
    `<span class="type-badge ${relic.itemType}">${typeLabel(relic.itemType)}</span>`);
  html += field(ja ? '座標' : 'Coordinates', `[${relic.coordinates.join(', ')}]`);
  html += field(ja ? '色別座標' : 'Color Coords', `[${relic.coordinatesByColor.join(', ')}]`);
  html += field(ja ? 'ソートキー' : 'Sort Key', relic.sortKey);
  html += `</div>`;

  // Effects
  html += `<div class="detail-section">`;
  html += `<h3>${ja ? '効果一覧' : 'Effects'}</h3>`;
  relic.effects.forEach((group) => {
    const main = group[0];
    const mainName = displayLang === 'ja'
      ? (main.name_ja || main.name_en || '-')
      : (main.name_en || '-');
    html += `<div class="detail-effect">`;
    html += `<div class="detail-effect-main">${mainName}</div>`;
    html += formatStackingInfo(main.id, ja);
    for (let i = 1; i < group.length; i++) {
      const d = group[i];
      const debuffName = displayLang === 'ja'
        ? (d.name_ja || d.name_en || '-')
        : (d.name_en || '-');
      html += `<div class="detail-effect-sub">`;
      html += `<div class="detail-effect-debuff-name">${debuffName}</div>`;
      html += formatStackingInfo(d.id, ja);
      html += `</div>`;
    }
    html += `</div>`;
  });
  html += `</div>`;

  detailBody.innerHTML = html;

  // Highlight selected row
  document.querySelectorAll('#relic-tbody tr').forEach(tr => tr.classList.remove('selected'));
  const rows = relicTbody.querySelectorAll('tr');
  const idx = filteredRelics.findIndex(r => r.id === relic.id);
  if (idx >= 0 && rows[idx]) rows[idx].classList.add('selected');
}

function closeDetail() {
  detailPanel.classList.add('hidden');
  selectedRelicId = null;
  document.querySelectorAll('#relic-tbody tr').forEach(tr => tr.classList.remove('selected'));
}

function field(label, value) {
  return `<div class="detail-field"><span class="label">${label}</span><span class="value">${value}</span></div>`;
}

function formatStackingInfo(effectId, ja) {
  const info = stackingLookup[String(effectId)];
  if (!info) return '';
  let stackLabel;
  if (info.stackable === true) {
    stackLabel = ja ? '重複: ○' : 'Stacking: Yes';
  } else if (info.stackable === 'conditional') {
    stackLabel = ja ? '重複: △' : 'Stacking: Conditional';
  } else {
    stackLabel = ja ? '重複: ×' : 'Stacking: No';
  }
  const notes = info.stackNotes
    ? `<span class="stacking-notes">${info.stackNotes}</span>`
    : '';
  return `<div class="detail-effect-stacking">${stackLabel}${notes}</div>`;
}

// === Minimap ===
const MINIMAP_COLORS = {
  Red: '#e74c3c',
  Blue: '#3498db',
  Yellow: '#f1c40f',
  Green: '#2ecc71',
};

function getMinimapHeaderOffset() {
  const thead = document.querySelector('#relic-table thead');
  return thead ? thead.offsetHeight : 0;
}

function renderMinimap() {
  if (filteredRelics.length === 0) return;

  // Wait for layout to settle
  requestAnimationFrame(() => {
    const mapH = minimap.clientHeight;
    const mapW = minimap.clientWidth;
    if (mapH === 0 || mapW === 0) return;

    const headerOffset = getMinimapHeaderOffset();
    const drawH = mapH - headerOffset; // drawable area below header

    const dpr = window.devicePixelRatio || 1;
    minimapCanvas.width = mapW * dpr;
    minimapCanvas.height = mapH * dpr;
    minimapCanvas.style.width = mapW + 'px';
    minimapCanvas.style.height = mapH + 'px';

    const ctx = minimapCanvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, mapW, mapH);

    const rowH = drawH / filteredRelics.length;

    filteredRelics.forEach((relic, i) => {
      const y = headerOffset + i * rowH;
      const color = MINIMAP_COLORS[relic.itemColor] || '#555';
      const h = Math.max(1, rowH - (rowH > 4 ? 1 : 0));

      // Background bar (color represents the relic)
      ctx.globalAlpha = 0.15;
      ctx.fillStyle = color;
      ctx.fillRect(4, y, mapW - 8, h);

      // Effect-count marks on the right side
      const n = Math.min(relic.effects.length, 5);
      if (n > 1 && rowH > 2) {
        ctx.globalAlpha = 0.1;
        ctx.fillStyle = '#fff';
        for (let e = 1; e < n; e++) {
          ctx.fillRect(mapW - 4 - e * 4, y, 2, h);
        }
      }
    });

    ctx.globalAlpha = 1;
    updateMinimapSlider();
  });
}

function updateMinimapSlider() {
  const totalH = tableContainer.scrollHeight;
  const visibleH = tableContainer.clientHeight;
  const scrollTop = tableContainer.scrollTop;
  const mapH = minimap.clientHeight;
  const headerOffset = getMinimapHeaderOffset();
  const availableH = mapH - headerOffset;

  if (totalH <= visibleH) {
    minimapSlider.style.top = headerOffset + 'px';
    minimapSlider.style.height = availableH + 'px';
    return;
  }

  const sliderH = Math.max(20, (visibleH / totalH) * availableH);
  const sliderTop = headerOffset + (scrollTop / (totalH - visibleH)) * (availableH - sliderH);

  minimapSlider.style.top = sliderTop + 'px';
  minimapSlider.style.height = sliderH + 'px';
}

// Sync minimap slider with table scroll
tableContainer.addEventListener('scroll', updateMinimapSlider);

// Click on minimap background → jump to that position
minimap.addEventListener('mousedown', (e) => {
  if (e.target === minimapSlider) return; // drag handled separately

  const rect = minimap.getBoundingClientRect();
  const clickY = e.clientY - rect.top;
  const mapH = minimap.clientHeight;
  const headerOffset = getMinimapHeaderOffset();
  const availableH = mapH - headerOffset;
  const totalH = tableContainer.scrollHeight;
  const visibleH = tableContainer.clientHeight;

  // Map click position (below header) to scroll ratio
  const ratio = Math.max(0, clickY - headerOffset) / availableH;
  const targetScroll = ratio * totalH - visibleH / 2;
  tableContainer.scrollTop = Math.max(0, Math.min(targetScroll, totalH - visibleH));
});

// Drag slider to scroll
let mmDragging = false;
let mmDragStartY = 0;
let mmDragStartScroll = 0;

minimapSlider.addEventListener('mousedown', (e) => {
  mmDragging = true;
  mmDragStartY = e.clientY;
  mmDragStartScroll = tableContainer.scrollTop;
  minimapSlider.classList.add('dragging');
  e.preventDefault();
  e.stopPropagation();
});

document.addEventListener('mousemove', (e) => {
  if (!mmDragging) return;

  const dy = e.clientY - mmDragStartY;
  const mapH = minimap.clientHeight;
  const headerOffset = getMinimapHeaderOffset();
  const availableH = mapH - headerOffset;
  const totalH = tableContainer.scrollHeight;
  const visibleH = tableContainer.clientHeight;
  const sliderH = Math.max(20, (visibleH / totalH) * availableH);

  const scrollRange = totalH - visibleH;
  const minimapRange = availableH - sliderH;

  const scrollDelta = (dy / minimapRange) * scrollRange;
  tableContainer.scrollTop = Math.max(0, Math.min(mmDragStartScroll + scrollDelta, scrollRange));
});

document.addEventListener('mouseup', () => {
  if (mmDragging) {
    mmDragging = false;
    minimapSlider.classList.remove('dragging');
  }
});

// Re-render minimap on window resize
window.addEventListener('resize', () => {
  if (filteredRelics.length > 0) renderMinimap();
});

// === Inspector ===
// Category definitions based on kamikouryaku.net wiki
const EFFECT_CATEGORIES = [
  { id: 'character',     ja: 'キャラクター固有',           en: 'Character-Specific' },
  { id: 'stats',         ja: '能力値',                    en: 'Stats' },
  { id: 'attack',        ja: '攻撃力',                    en: 'Attack Power' },
  { id: 'skill',         ja: 'スキル／アーツ',             en: 'Skill / Arts' },
  { id: 'magic',         ja: '魔術／祈祷',                en: 'Sorcery / Incantation' },
  { id: 'cutrate',       ja: 'カット率',                  en: 'Damage Negation' },
  { id: 'resist',        ja: '状態異常耐性',               en: 'Status Resistance' },
  { id: 'recovery',      ja: '回復',                      en: 'Recovery' },
  { id: 'action',        ja: 'アクション',                 en: 'Action' },
  { id: 'start_skill',   ja: '出撃時の武器（戦技）',       en: 'Sortie Weapon (Skill)' },
  { id: 'start_enchant', ja: '出撃時の武器（付加）',       en: 'Sortie Weapon (Enchant)' },
  { id: 'start_magic',   ja: '出撃時の武器（魔術／祈祷）', en: 'Sortie Weapon (Magic)' },
  { id: 'start_item',    ja: '出撃時のアイテム',           en: 'Starting Items' },
  { id: 'start_tear',    ja: '出撃時のアイテム（結晶の雫）', en: 'Starting Items (Crystal Tears)' },
  { id: 'mapenv',        ja: 'マップ環境',                 en: 'Map / Environment' },
  { id: 'team',          ja: 'チームメンバー',              en: 'Team Member' },
  { id: 'night',         ja: '夜の力',                     en: 'Night Power' },
  { id: 'demerit',       ja: 'デメリット',                  en: 'Demerits' },
  { id: 'other',         ja: 'その他',                     en: 'Other' },
];

function classifyEffect(name_ja, name_en, key) {
  const ja = name_ja || '';
  const en = (name_en || '').toLowerCase();
  // 1. Character-specific (【追跡者】etc.) or トーテム・ステラ (無頼漢固有)
  if (/【.+?】/.test(ja) || /トーテム・ステラ/.test(ja)) return 'character';
  // 2. Demerit: specific patterns first (before recovery catches 回復)
  if (/回復量低下/.test(ja)) return 'demerit';
  if (/低下|減少|悪化|持続減少|喪失|鈍化/.test(ja) && !/上昇|強化|回復|軽減|付加|全回復|なし|無効化|生成/.test(ja)) return 'demerit';
  if (/被ダメージ時.*蓄積|HP最大未満時.*蓄積|消費増加|被ダメージ増加/.test(ja)) return 'demerit';
  if (/impaired|reduced|continuous\s*loss/i.test(en) && !/improved|increased|restoration|discover|inflict|activat|consumption|cost|drop.*off/i.test(en)) return 'demerit';
  // 3. Night Power
  if (/^.+の力$/.test(ja) && !/攻撃力|の力を/.test(ja) || /の悲嘆/.test(ja) || /^power\s*of/i.test(en) || /grief/i.test(en)) return 'night';
  // 4. Sortie weapon / item subcategories (wiki: 出撃時の武器, 出撃時のアイテム)
  if (/出撃時の武器の戦技を/.test(ja)) return 'start_skill';
  if (/出撃時の武器に.*付加/.test(ja)) return 'start_enchant';
  if (/出撃時の武器の魔術を|出撃時の武器の祈祷を/.test(ja)) return 'start_magic';
  if (/出撃時に.*雫.*を持つ/.test(ja)) return 'start_tear';
  if (/出撃時に.*を持つ/.test(ja)) return 'start_item';
  // 5. Team member (BEFORE recovery — ally-focused effects)
  // 味方を含め = includes allies as secondary benefit → not team (let recovery handle)
  if (!/味方を含め/.test(ja) && (/味方/.test(ja) || /allies/i.test(en))) return 'team';
  // 6. Specific action patterns (before stats/attack/mapenv catch them)
  if (/致命の一撃で.*ルーン/.test(ja)) return 'action';
  if (/武器の持ち替え時.*付加/.test(ja)) return 'action';
  if (/被ダメージ時.*付加/.test(ja)) return 'action';
  if (/ガード中.*狙われ/.test(ja)) return 'action';
  if (/周囲で.*状態.*発生時/.test(ja) && !/回復/.test(ja)) return 'action';
  if (/カット率低下時.*無効化/.test(ja) || /nullify.*attack/i.test(en)) return 'action';
  if (/状態の敵に対する攻撃/.test(ja)) return 'action';
  if (/ジェスチャー/.test(ja) || /gesture/i.test(en)) return 'action';
  // 7. Specific cutrate (before stats catches 強靭度)
  if (/ダメージで吹き飛ばされた時.*カット率/.test(ja)) return 'cutrate';
  // 7b. Specific spell type enhancement → magic (before stats catches 信仰 in 王都古竜信仰)
  if (/の魔術を強化|の祈祷を強化|の祈祷強化/.test(ja)) return 'magic';
  // 8. Specific stats (before mapenv catches 発見力/ルーン)
  if (/小砦の強敵|大教会の強敵|大野営地の強敵|遺跡の強敵/.test(ja)) return 'stats';
  // 9. Stats
  if (/最大HP|最大FP|最大スタミナ|生命力|精神力|持久力|筋力|技量|知力|信仰|神秘|強靭度/.test(ja)) return 'stats';
  if (/vigor|mind\b|endurance|\bstrength\b|dexterity|intelligence|faith|arcane|poise|maximum\s*(hp|fp|stamina)/i.test(en)) return 'stats';
  // 10. Skill attack power → attack (before skill check)
  if (/スキル攻撃力|戦技攻撃力|スキルの攻撃力/.test(ja) || /skill\s*attack\s*power/i.test(en)) return 'attack';
  // 11. Skill / Arts
  if (/スキル|アーツ|クールタイム/.test(ja) || /skill|art\s*gauge|cooldown/i.test(en)) return 'skill';
  // 12. General sorcery/incantation enhancement → attack (wiki: 攻撃力)
  if (/^魔術強化|^祈祷強化/.test(ja)) return 'attack';
  // 12b. Sorcery / Incantation
  if (/魔術|祈祷|詠唱|ソウル/.test(ja) || /sorcery|sorceries|incantation|spell|casting/i.test(en)) return 'magic';
  // 13. Specific attack enhancements (wiki: 攻撃力 category)
  if (/ガードカウンター/.test(ja) || /guard\s*counter/i.test(en)) return 'attack';
  if (/投擲壺強化/.test(ja)) return 'attack';
  if (/調香術強化/.test(ja)) return 'attack';
  if (/咆哮.*強化|ブレス.*強化/.test(ja)) return 'attack';
  if (/体勢を崩す力/.test(ja) || /stance.*break.*power/i.test(en)) return 'attack';
  // 14. Damage Negation
  if (/カット率|ガード性能/.test(ja) || /damage\s*negation/i.test(en)) return 'cutrate';
  // 15. Status Resistance
  if (/耐性/.test(ja) || /resistance/i.test(en)) return 'resist';
  // 16. Recovery
  if (/回復|リゲイン|聖杯瓶|消費FP/.test(ja) || /restoration|recovery|restore|flask|reduced.*fp.*consumption/i.test(en)) return 'recovery';
  // 17. Attack Power
  if (/攻撃力|致命の一撃強化|通常攻撃の1段目/.test(ja) || /attack\s*power|critical.*damage/i.test(en)) return 'attack';
  // 18. Map / Environment
  if (/埋もれ宝|地図|発見力|ルーン|見つけやすくなる|死亡時/.test(ja) || /item\s*discovery|rune/i.test(en)) return 'mapenv';
  // 19. Action (broad)
  if (/ローリング|回避|二刀|両手持ち|タメ攻撃|連撃|遠距離|武器の持ち替え|刺突|ジャンプ|ガード崩し|波動ダッシュ|ガード成功|ガード連続|ガード中|致命の一撃|パリィ|歩行中|集団撃破|精密射撃|シールド|体勢が崩れ|竜餐|定期的に|状態になると|スタミナ消費|咆哮|ブレス|調香術|投擲/.test(ja)
    || /throwing|perfum|roar|breath|dodge|evasion|two.*hand|dual|charge|ranged|switch.*weapon|thrust|jump|stance.*break|critical.*hit/i.test(en)) return 'action';
  // 20. Broad attack-related
  if (/攻撃/.test(ja) || /attack/i.test(en)) return 'attack';
  return 'other';
}

function buildUniqueEffects() {
  if (!relicData) { allUniqueEffects = []; return; }
  // Build deepOnly lookup: effectKey -> boolean (from stackingLookup)
  const deepOnlyByKey = {};
  for (const [id, info] of Object.entries(stackingLookup)) {
    if (info.deepOnly && info.key) deepOnlyByKey[info.key] = true;
  }
  const effectMap = new Map(); // key -> { key, id, name_ja, name_en, count, category, deepOnly }
  // 1. Count effects from loaded relic data
  relicData.relics.forEach(r => {
    const seen = new Set();
    r.effects.flat().forEach(e => {
      if (!e.key || seen.has(e.key)) return;
      seen.add(e.key);
      if (effectMap.has(e.key)) {
        effectMap.get(e.key).count++;
      } else {
        effectMap.set(e.key, {
          key: e.key,
          id: e.id,
          name_ja: e.name_ja || e.name_en || e.key,
          name_en: e.name_en || e.key,
          count: 1,
          category: classifyEffect(e.name_ja, e.name_en, e.key),
          deepOnly: !!deepOnlyByKey[e.key],
        });
      }
    });
  });
  allUniqueEffects = Array.from(effectMap.values())
    .sort((a, b) => a.name_ja.localeCompare(b.name_ja, 'ja'));
}

function openInspector() {
  inspectorBackdrop.classList.remove('hidden');
  inspector.classList.add('open');
  inspectorSearch.value = '';
  // Default all categories to collapsed
  EFFECT_CATEGORIES.forEach(c => collapsedCategories.add(c.id));
  updateAndGroupTabs();
  renderInspectorEffects();
  inspectorSearch.focus();
}

function closeInspector() {
  inspectorBackdrop.classList.add('hidden');
  inspector.classList.remove('open');
}

// --- Inspector resize ---
function setupInspectorResize(inspectorEl) {
  const handle = inspectorEl.querySelector('.inspector-resize-handle');
  if (!handle) return;
  let startX, startWidth;
  handle.addEventListener('mousedown', (e) => {
    startX = e.clientX;
    startWidth = inspectorEl.offsetWidth;
    handle.classList.add('active');
    const onMove = (ev) => {
      const w = Math.max(280, Math.min(800, startWidth + (ev.clientX - startX)));
      inspectorEl.style.width = w + 'px';
      // If optimizer inspector, also update effect-select sub-panel position
      const effectSel = document.querySelector('.effect-select-inspector');
      if (effectSel && inspectorEl.id === 'optimizer-inspector') {
        effectSel.style.left = w + 'px';
      }
    };
    const onUp = () => {
      handle.classList.remove('active');
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    e.preventDefault();
  });
}
setupInspectorResize(document.getElementById('inspector'));
setupInspectorResize(document.getElementById('optimizer-inspector'));
setupInspectorResize(document.getElementById('effect-select-inspector'));

// --- Opt detail panel resize (left edge, right-side panel) ---
function setupOptDetailResize(panelEl) {
  const handle = panelEl.querySelector('.opt-detail-resize-handle');
  if (!handle) return;
  let startX, startWidth;
  handle.addEventListener('mousedown', (e) => {
    startX = e.clientX;
    startWidth = panelEl.offsetWidth;
    handle.classList.add('active');
    const onMove = (ev) => {
      const w = Math.max(280, Math.min(800, startWidth - (ev.clientX - startX)));
      panelEl.style.width = w + 'px';
    };
    const onUp = () => {
      handle.classList.remove('active');
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    e.preventDefault();
  });
}

function renderInspectorEffects() {
  const query = inspectorSearch.value.toLowerCase().trim();
  const filtered = query
    ? allUniqueEffects.filter(e =>
        e.name_ja.toLowerCase().includes(query) ||
        e.name_en.toLowerCase().includes(query) ||
        e.key.toLowerCase().includes(query))
    : allUniqueEffects;

  // Group by category
  const groups = new Map();
  filtered.forEach(e => {
    const catId = e.category;
    if (!groups.has(catId)) groups.set(catId, []);
    groups.get(catId).push(e);
  });

  // Count how many relics match each category's effects (hit count)
  const catHitCounts = new Map();
  if (relicData) {
    groups.forEach((items, catId) => {
      const catKeys = new Set(items.map(e => e.key));
      let hits = 0;
      relicData.relics.forEach(r => {
        const relicEffectKeys = r.effects.flat().map(e => e.key);
        if (relicEffectKeys.some(k => catKeys.has(k))) hits++;
      });
      catHitCounts.set(catId, hits);
    });
  }

  // Render in category order
  const catOrder = EFFECT_CATEGORIES.map(c => c.id);
  const ja = displayLang === 'ja';

  let html = '';
  catOrder.forEach(catId => {
    const items = groups.get(catId);
    if (!items || items.length === 0) return;
    const catDef = EFFECT_CATEGORIES.find(c => c.id === catId);
    const catName = catDef ? (ja ? catDef.ja : catDef.en) : (ja ? 'その他' : 'Other');
    const isCollapsed = collapsedCategories.has(catId);
    const hitCount = catHitCounts.get(catId) || 0;

    // Determine select-all checkbox state for this category
    const catKeys = items.map(e => e.key);
    const checkedInCat = catKeys.filter(k => andGroups.some(g => g.has(k))).length;
    const allChecked = checkedInCat === catKeys.length;
    const someChecked = checkedInCat > 0 && !allChecked;

    html += `<div class="inspector-group-header${isCollapsed ? ' collapsed' : ''}" data-cat="${catId}">`;
    html += `<span class="inspector-group-arrow">▼</span>`;
    html += `<input type="checkbox" class="inspector-group-checkbox" data-cat="${catId}" ${allChecked ? 'checked' : ''} ${someChecked ? 'data-indeterminate="true"' : ''} />`;
    html += `<span class="group-name">${catName}</span>`;
    html += `<span class="group-count">(${hitCount})</span>`;
    html += `</div>`;
    html += `<div class="inspector-group-items${isCollapsed ? ' collapsed' : ''}" data-cat="${catId}">`;
    items.forEach(e => {
      const name = ja ? e.name_ja : e.name_en;
      const groupIdx = andGroups.findIndex(g => g.has(e.key));
      const checked = groupIdx >= 0;
      html += `<label class="inspector-effect-item${checked ? ' checked' : ''}" data-key="${e.key}">
        <input type="checkbox" ${checked ? 'checked' : ''} />`;
      if (groupIdx >= 0) {
        html += `<span class="effect-group-dot" style="background:${AND_GROUP_COLORS[groupIdx]}"></span>`;
      }
      html += `<span class="inspector-effect-name" title="${name}">${name}</span>
        <span class="inspector-effect-count">${e.count}</span>
      </label>`;
    });
    html += `</div>`;
  });

  inspectorEffectList.innerHTML = html;

  // Set indeterminate state for group checkboxes (can't be set via HTML attribute)
  inspectorEffectList.querySelectorAll('.inspector-group-checkbox[data-indeterminate="true"]').forEach(cb => {
    cb.indeterminate = true;
  });

  // Attach click handlers for collapsible group headers
  inspectorEffectList.querySelectorAll('.inspector-group-header').forEach(header => {
    header.addEventListener('click', (e) => {
      if (e.target.classList.contains('inspector-group-checkbox')) return;
      const catId = header.dataset.cat;
      const itemsDiv = inspectorEffectList.querySelector(`.inspector-group-items[data-cat="${catId}"]`);
      if (collapsedCategories.has(catId)) {
        collapsedCategories.delete(catId);
        header.classList.remove('collapsed');
        itemsDiv.classList.remove('collapsed');
      } else {
        collapsedCategories.add(catId);
        header.classList.add('collapsed');
        itemsDiv.classList.add('collapsed');
      }
    });
  });

  updateInspectorCount();
}

function updateInspectorCount() {
  const ja = displayLang === 'ja';
  const parts = andGroups.map((g, i) => g.size > 0 ? `${ja ? '条件' : 'G'}${i + 1}:${g.size}` : null).filter(Boolean);
  if (parts.length > 0) {
    inspectorSelectedCount.textContent = parts.join(' AND ');
  } else {
    inspectorSelectedCount.textContent = ja ? '0件選択中' : '0 selected';
  }
}

function updateInspectorButton() {
  const ja = displayLang === 'ja';
  const activeCount = andGroups.filter(g => g.size > 0).length;
  if (activeCount > 0) {
    const total = andGroups.reduce((sum, g) => sum + g.size, 0);
    if (activeCount === 1) {
      btnInspectorLabel.textContent = ja ? `高度な検索 (${total})` : `Advanced (${total})`;
    } else {
      btnInspectorLabel.textContent = ja
        ? `高度な検索 (AND: ${activeCount}条件)`
        : `Advanced (AND: ${activeCount} groups)`;
    }
    btnInspector.classList.add('active');
  } else {
    btnInspectorLabel.textContent = ja ? '高度な検索' : 'Advanced';
    btnInspector.classList.remove('active');
  }
}

function updateAndGroupTabs() {
  document.querySelectorAll('.and-group-tab').forEach(tab => {
    const gi = parseInt(tab.dataset.group);
    const g = andGroups[gi];
    const ja = displayLang === 'ja';
    const label = ja ? `条件${gi + 1}(OR)` : `G${gi + 1}(OR)`;
    tab.classList.toggle('active', gi === activeAndGroup);
    tab.classList.toggle('has-items', g.size > 0 && gi !== activeAndGroup);
    tab.textContent = g.size > 0 ? `${label} [${g.size}]` : label;
  });
}

// Inspector event listeners
btnInspector.addEventListener('click', openInspector);
btnExportTable.addEventListener('click', exportRelicTableToHTML);
inspectorClose.addEventListener('click', closeInspector);
inspectorBackdrop.addEventListener('click', closeInspector);

inspectorSearch.addEventListener('input', () => {
  inspectorSearchClear.classList.toggle('hidden', !inspectorSearch.value);
  renderInspectorEffects();
});
inspectorSearchClear.addEventListener('click', () => {
  inspectorSearch.value = '';
  inspectorSearchClear.classList.add('hidden');
  renderInspectorEffects();
  inspectorSearch.focus();
});

// AND group tab clicks
document.getElementById('and-group-tabs').addEventListener('click', (e) => {
  const tab = e.target.closest('.and-group-tab');
  if (!tab) return;
  activeAndGroup = parseInt(tab.dataset.group);
  updateAndGroupTabs();
  renderInspectorEffects();
});

inspectorEffectList.addEventListener('change', (e) => {
  const checkbox = e.target;
  if (checkbox.type !== 'checkbox') return;

  // Group select-all checkbox
  if (checkbox.classList.contains('inspector-group-checkbox')) {
    const catId = checkbox.dataset.cat;
    const catItems = inspectorEffectList.querySelectorAll(`.inspector-group-items[data-cat="${catId}"] .inspector-effect-item`);
    const catKeys = Array.from(catItems).map(item => item.dataset.key);
    if (checkbox.checked) {
      catKeys.forEach(k => {
        andGroups.forEach(g => g.delete(k));
        andGroups[activeAndGroup].add(k);
      });
    } else {
      catKeys.forEach(k => {
        andGroups.forEach(g => g.delete(k));
      });
    }
    updateAndGroupTabs();
    renderInspectorEffects();
    updateInspectorCount();
    return;
  }

  // Individual effect checkbox
  const item = checkbox.closest('.inspector-effect-item');
  const key = item.dataset.key;
  if (checkbox.checked) {
    // Remove from any other group first
    andGroups.forEach(g => g.delete(key));
    andGroups[activeAndGroup].add(key);
  } else {
    andGroups[activeAndGroup].delete(key);
  }
  updateAndGroupTabs();
  renderInspectorEffects();
  updateInspectorCount();
});

inspectorApply.addEventListener('click', () => {
  closeInspector();
  updateInspectorButton();
  applyFilters();
});

inspectorClear.addEventListener('click', () => {
  andGroups.forEach(g => g.clear());
  updateAndGroupTabs();
  renderInspectorEffects();
  updateInspectorButton();
  applyFilters();
});

// ============================================================
// === Tab Management ===
// ============================================================

function renderTabBar() {
  // Keep main tab, remove dynamic tabs
  const existing = tabBar.querySelectorAll('.tab[data-tab]:not([data-tab="main"])');
  existing.forEach(el => el.remove());

  optimizerTabs.forEach((info, tabId) => {
    const tab = document.createElement('div');
    tab.className = 'tab' + (activeTab === tabId ? ' active' : '');
    tab.dataset.tab = tabId;

    if (info._loading) {
      const spinner = document.createElement('span');
      spinner.className = 'tab-spinner';
      tab.appendChild(spinner);
    } else if (info._error) {
      const errIcon = document.createElement('span');
      errIcon.className = 'tab-error-icon';
      errIcon.textContent = '!';
      tab.appendChild(errIcon);
    }

    const label = document.createElement('span');
    label.className = 'tab-label';
    label.textContent = info.label;
    tab.appendChild(label);

    const closeBtn = document.createElement('button');
    closeBtn.className = 'tab-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeTab(tabId);
    });
    tab.appendChild(closeBtn);

    tab.addEventListener('click', () => switchTab(tabId));
    tabBar.appendChild(tab);
  });

  // Update main tab active state
  const mainTab = tabBar.querySelector('[data-tab="main"]');
  if (mainTab) mainTab.className = 'tab' + (activeTab === 'main' ? ' active' : '');
}

// Main tab click handler (set once)
tabBar.querySelector('[data-tab="main"]').addEventListener('click', () => switchTab('main'));

function switchTab(tabId) {
  activeTab = tabId;

  // Toggle content visibility
  contentArea.classList.toggle('hidden', tabId !== 'main');

  // Show/hide optimizer tab wrappers
  optimizerTabs.forEach((info, tid) => {
    const wrapper = document.getElementById(`opt-wrapper-${tid}`);
    if (wrapper) wrapper.classList.toggle('hidden', tid !== tabId);
  });

  // Update toolbar visibility: show filters only on main tab
  const filterElements = toolbar.querySelectorAll('.search-wrapper, .filter-group, #result-count, #btn-inspector, #btn-export-table');
  filterElements.forEach(el => {
    if (tabId === 'main') {
      el.style.display = '';
    } else {
      el.style.display = 'none';
    }
  });

  renderTabBar();
}

function addOptimizerTab(label, data, params) {
  const tabId = `optimizer-${nextTabId++}`;

  optimizerTabs.set(tabId, { label, data, params });

  // Create wrapper (flex row: results list + detail panel)
  const wrapper = document.createElement('div');
  wrapper.id = `opt-wrapper-${tabId}`;
  wrapper.className = 'opt-tab-wrapper';

  // Results list
  const container = document.createElement('div');
  container.id = `opt-result-${tabId}`;
  container.className = 'optimizer-results-container';
  wrapper.appendChild(container);

  // Detail panel (hidden initially)
  const detail = document.createElement('div');
  detail.id = `opt-detail-${tabId}`;
  detail.className = 'opt-detail-panel hidden';
  detail.innerHTML = `
    <div class="opt-detail-resize-handle"></div>
    <div class="detail-header">
      <h2 class="opt-detail-title"></h2>
      <button class="btn-close opt-detail-close">&times;</button>
    </div>
    <div class="opt-detail-body detail-body"></div>`;
  setupOptDetailResize(detail);
  wrapper.appendChild(detail);

  document.getElementById('main-content').appendChild(wrapper);
  renderOptimizerResults(tabId, data, params);
  switchTab(tabId);
}

function addOptimizerTabLoading(label, params) {
  const tabId = `optimizer-${nextTabId++}`;
  const ja = displayLang === 'ja';

  optimizerTabs.set(tabId, { label, data: null, params, _loading: true });

  const wrapper = document.createElement('div');
  wrapper.id = `opt-wrapper-${tabId}`;
  wrapper.className = 'opt-tab-wrapper';

  const container = document.createElement('div');
  container.id = `opt-result-${tabId}`;
  container.className = 'optimizer-results-container opt-loading';
  container.innerHTML = `<div class="opt-loading-content">
    <div class="opt-loading-spinner"></div>
    <div class="opt-loading-title">${ja ? '計算中...' : 'Calculating...'}</div>
    <div class="opt-loading-progress" id="opt-progress-${tabId}">
      <div class="opt-progress-bar-track">
        <div class="opt-progress-bar-fill" id="opt-progress-fill-${tabId}"></div>
      </div>
      <div class="opt-progress-text" id="opt-progress-text-${tabId}">0%</div>
    </div>
    <div class="opt-loading-message">${ja ? '献器ごとに最適な組み合わせを探索しています' : 'Searching for optimal combinations per vessel'}</div>
  </div>`;
  wrapper.appendChild(container);

  const detail = document.createElement('div');
  detail.id = `opt-detail-${tabId}`;
  detail.className = 'opt-detail-panel hidden';
  detail.innerHTML = `
    <div class="opt-detail-resize-handle"></div>
    <div class="detail-header">
      <h2 class="opt-detail-title"></h2>
      <button class="btn-close opt-detail-close">&times;</button>
    </div>
    <div class="opt-detail-body detail-body"></div>`;
  setupOptDetailResize(detail);
  wrapper.appendChild(detail);

  document.getElementById('main-content').appendChild(wrapper);
  switchTab(tabId);
  return tabId;
}

function updateOptimizerTabProgress(tabId, current, total) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;
  const fill = document.getElementById(`opt-progress-fill-${tabId}`);
  const text = document.getElementById(`opt-progress-text-${tabId}`);
  if (fill) fill.style.width = `${pct}%`;
  if (text) {
    const ja = displayLang === 'ja';
    text.textContent = `${current} / ${total}${ja ? ' 献器' : ' vessels'} (${pct}%)`;
  }
}

function closeTab(tabId) {
  if (tabId === 'main') return;

  optimizerTabs.delete(tabId);
  const wrapper = document.getElementById(`opt-wrapper-${tabId}`);
  if (wrapper) wrapper.remove();

  if (activeTab === tabId) {
    switchTab('main');
  } else {
    renderTabBar();
  }
}

// ============================================================
// === Optimizer Inspector ===
// ============================================================

function updateOptimizerButton() {
  const ja = displayLang === 'ja';
  btnOptimizerLabel.textContent = ja ? 'ビルド探索' : 'Build Search';
}

async function openOptimizerInspector() {
  optimizerBackdrop.classList.remove('hidden');
  optimizerInspector.classList.add('open');

  // Load vessels data if not cached
  if (!vesselsData) {
    vesselsData = await window.api.loadVesselsData();
  }

  renderOptimizerCharacterSelect();
  renderOptimizerVesselList();
  updateOptEffectsCount();
}

function closeOptimizerInspector() {
  optimizerBackdrop.classList.add('hidden');
  optimizerInspector.classList.remove('open');
}

function renderOptimizerCharacterSelect() {
  if (!vesselsData) return;
  const ja = displayLang === 'ja';
  const prev = optCharacter.value;

  let html = '';
  const chars = vesselsData.characters || {};
  for (const [charJa, charData] of Object.entries(chars)) {
    const charName = ja ? charJa : (charData.nameEn || charJa);
    html += `<option value="${charJa}">${charName}</option>`;
  }
  optCharacter.innerHTML = html;

  // Restore previous selection if it still exists
  if (prev && optCharacter.querySelector(`option[value="${CSS.escape(prev)}"]`)) {
    optCharacter.value = prev;
  }
}

function renderOptimizerVesselList() {
  if (!vesselsData) return;
  const ja = displayLang === 'ja';

  // Save previous check states
  const prevChecked = new Set();
  let hasPrev = false;
  optVesselList.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    hasPrev = true;
    if (cb.checked) prevChecked.add(cb.value);
  });

  const vesselTypes = vesselsData.vesselTypes || [];
  let html = '';

  // Character-specific vessels
  vesselTypes.forEach(vt => {
    const vesselName = ja ? vt.nameJa : vt.nameEn;
    const checked = hasPrev ? prevChecked.has(vt.key) : true;
    html += `<label class="opt-vessel-item" data-vessel="${vt.key}">
      <input type="checkbox" ${checked ? 'checked' : ''} value="${vt.key}">
      <span>${vesselName}</span>
    </label>`;
  });

  // Universal vessels
  const universalVessels = vesselsData.universalVessels || [];
  universalVessels.forEach(uv => {
    const vesselName = ja ? uv.nameJa : uv.nameEn;
    const checked = hasPrev ? prevChecked.has(uv.key) : true;
    html += `<label class="opt-vessel-item" data-vessel="${uv.key}">
      <input type="checkbox" ${checked ? 'checked' : ''} value="${uv.key}">
      <span>${vesselName}</span>
    </label>`;
  });

  optVesselList.innerHTML = html;
  updateOptVesselCount();
}

function updateOptVesselCount() {
  const total = optVesselList.querySelectorAll('input[type="checkbox"]').length;
  const checked = optVesselList.querySelectorAll('input[type="checkbox"]:checked').length;
  const countEl = document.getElementById('opt-vessel-count');
  if (countEl) countEl.textContent = `${checked}/${total}`;
}

function toggleOptVesselCollapse() {
  optVesselCollapsed = !optVesselCollapsed;
  optVesselHeader.classList.toggle('collapsed', optVesselCollapsed);
  optVesselList.classList.toggle('collapsed', optVesselCollapsed);
}

// Render selected effects as tags in the optimizer inspector
function renderOptEffectsTags() {
  const ja = displayLang === 'ja';
  const groupOrder = [
    'required', 'preferred', 'nice_to_have',
    'exclude_required', 'exclude_preferred', 'exclude_nice_to_have',
  ];
  // Group effects by priority
  const groups = {};
  optSelectedEffects.forEach((priority, key) => {
    if (!groups[priority]) groups[priority] = [];
    groups[priority].push(key);
  });

  let html = '';
  for (const gp of groupOrder) {
    const keys = groups[gp];
    if (!keys || keys.length === 0) continue;
    const isExclude = gp.startsWith('exclude_');
    const groupLabel = PRIORITY_LABELS[gp]
      ? (ja ? PRIORITY_LABELS[gp].ja : PRIORITY_LABELS[gp].en) : gp;
    html += `<div class="opt-effect-group" data-priority="${gp}">`;
    html += `<div class="opt-effect-group-label ${gp}">${groupLabel}</div>`;
    html += `<div class="opt-effect-group-cards">`;
    keys.forEach((key, idx) => {
      const eff = allUniqueEffects.find(e => e.key === key);
      const name = eff ? (ja ? eff.name_ja : eff.name_en) : key;
      const rankHtml = `<span class="opt-effect-rank">${idx + 1}</span>`;
      const dragHandle = '<span class="opt-effect-drag-handle">&#x2630;</span>';
      html += `<div class="opt-effect-tag" data-key="${key}" data-priority="${gp}" draggable="true">
        ${rankHtml}
        <span class="opt-effect-tag-name" title="${key}">${name}</span>
        ${dragHandle}
        <button class="opt-effect-remove" data-key="${key}">&times;</button>
      </div>`;
    });
    html += '</div></div>';
  }
  optEffectsList.innerHTML = html;

  // Attach remove handlers
  optEffectsList.querySelectorAll('.opt-effect-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      optSelectedEffects.delete(btn.dataset.key);
      renderOptEffectsTags();
      updateOptEffectsCount();
    });
  });

  // Attach drag-and-drop handlers
  attachEffectDragHandlers();
  updateOptEffectsCount();
}

// === Effect card drag-and-drop reordering ===
function attachEffectDragHandlers() {
  let draggedEl = null;
  let draggedPriority = null;

  optEffectsList.querySelectorAll('.opt-effect-tag[draggable="true"]').forEach(tag => {
    tag.addEventListener('dragstart', (e) => {
      draggedEl = tag;
      draggedPriority = tag.closest('.opt-effect-group').dataset.priority;
      tag.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', tag.dataset.key);
    });
    tag.addEventListener('dragend', () => {
      if (draggedEl) draggedEl.classList.remove('dragging');
      optEffectsList.querySelectorAll('.drag-over-above, .drag-over-below').forEach(el => {
        el.classList.remove('drag-over-above', 'drag-over-below');
      });
      draggedEl = null;
      draggedPriority = null;
    });
  });

  optEffectsList.querySelectorAll('.opt-effect-group').forEach(group => {
    group.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!draggedEl || group.dataset.priority !== draggedPriority) return;
      e.dataTransfer.dropEffect = 'move';
      const target = e.target.closest('.opt-effect-tag');
      if (!target || target === draggedEl) return;
      // Clear previous indicators
      group.querySelectorAll('.drag-over-above, .drag-over-below').forEach(el => {
        el.classList.remove('drag-over-above', 'drag-over-below');
      });
      const rect = target.getBoundingClientRect();
      if (e.clientY < rect.top + rect.height / 2) {
        target.classList.add('drag-over-above');
      } else {
        target.classList.add('drag-over-below');
      }
    });

    group.addEventListener('dragleave', (e) => {
      const target = e.target.closest('.opt-effect-tag');
      if (target) target.classList.remove('drag-over-above', 'drag-over-below');
    });

    group.addEventListener('drop', (e) => {
      e.preventDefault();
      if (!draggedEl || group.dataset.priority !== draggedPriority) return;
      const target = e.target.closest('.opt-effect-tag');
      if (!target || target === draggedEl) return;
      const cardsContainer = group.querySelector('.opt-effect-group-cards');
      const rect = target.getBoundingClientRect();
      if (e.clientY < rect.top + rect.height / 2) {
        cardsContainer.insertBefore(draggedEl, target);
      } else {
        cardsContainer.insertBefore(draggedEl, target.nextSibling);
      }
      // Rebuild Map from DOM order and re-render
      rebuildEffectsMapFromDOM();
      renderOptEffectsTags();
    });
  });
}

function rebuildEffectsMapFromDOM() {
  const newMap = new Map();
  optEffectsList.querySelectorAll('.opt-effect-tag').forEach(tag => {
    const key = tag.dataset.key;
    const priority = tag.dataset.priority;
    newMap.set(key, priority);
  });
  optSelectedEffects = newMap;
}

function updateOptEffectsCount() {
  const count = optSelectedEffects.size;
  const ja = displayLang === 'ja';
  document.getElementById('opt-effects-count').textContent =
    ja ? `${count}件` : `${count} effects`;
}

function collectOptimizerParams() {
  const character = optCharacter.value;

  // Collect selected vessels
  const vesselChecks = optVesselList.querySelectorAll('input[type="checkbox"]:checked');
  const vessels = Array.from(vesselChecks).map(cb => cb.value);
  const vesselStr = vessels.length > 0 ? vessels.join(',') : undefined;

  const combined = optMode.value === 'combined';

  // Collect effects from optSelectedEffects map, with rank within priority group
  const effects = [];
  const rankCounters = {};
  optSelectedEffects.forEach((priority, key) => {
    if (priority.startsWith('exclude_')) {
      const rank = rankCounters[priority] || 0;
      rankCounters[priority] = rank + 1;
      effects.push({ key, priority: priority.replace('exclude_', ''), exclude: true, rank });
    } else {
      const rank = rankCounters[priority] || 0;
      rankCounters[priority] = rank + 1;
      effects.push({ key, priority, rank });
    }
  });

  const candidates = parseInt(optCandidates.value) || 30;
  const top = parseInt(optTop.value) || 50;

  return { character, vessel: vesselStr, combined, effects, candidates, top };
}

async function runOptimization() {
  if (!relicData) return;

  const params = collectOptimizerParams();

  // Disable run button during execution
  optimizerRunBtn.disabled = true;
  const ja = displayLang === 'ja';
  document.getElementById('optimizer-run-label').textContent =
    ja ? '実行中...' : 'Running...';

  // Build tab label
  const charName = ja ? params.character :
    (vesselsData && vesselsData.characters[params.character]
      ? vesselsData.characters[params.character].nameEn
      : params.character);
  const label = ja
    ? `${charName} #${nextTabId}`
    : `${charName} #${nextTabId}`;

  // Create tab immediately with loading state
  const tabId = addOptimizerTabLoading(label, params);

  closeOptimizerInspector();

  // Listen for progress updates
  const removeProgressListener = window.api.onOptimizerProgress((data) => {
    updateOptimizerTabProgress(tabId, data.current, data.total);
  });

  try {
    const result = await window.api.runOptimizer({
      relicData: relicData,
      character: params.character,
      vessel: params.vessel,
      combined: params.combined,
      effects: params.effects,
      candidates: params.candidates,
      top: params.top,
    });

    removeProgressListener();

    // Replace loading state with results
    optimizerTabs.set(tabId, { label, data: result, params });
    const container = document.getElementById(`opt-result-${tabId}`);
    if (container) {
      container.classList.remove('opt-loading');
      renderOptimizerResults(tabId, result, params);
    }
    // Update tab label (remove spinner icon)
    renderTabBar();
  } catch (err) {
    removeProgressListener();
    // Show error in the tab
    const container = document.getElementById(`opt-result-${tabId}`);
    if (container) {
      container.classList.remove('opt-loading');
      container.innerHTML = `<div class="opt-loading-content">
        <div class="opt-loading-error">${ja ? 'エラー' : 'Error'}</div>
        <div class="opt-loading-message">${String(err).substring(0, 300)}</div>
      </div>`;
    }
    // Mark tab as error
    const tabInfo = optimizerTabs.get(tabId);
    if (tabInfo) tabInfo._error = true;
    renderTabBar();
  } finally {
    optimizerRunBtn.disabled = false;
    document.getElementById('optimizer-run-label').textContent =
      ja ? '実行' : 'Run';
  }
}

// Optimizer inspector event listeners
btnOptimizer.addEventListener('click', openOptimizerInspector);
optimizerClose.addEventListener('click', closeOptimizerInspector);
optimizerBackdrop.addEventListener('click', closeOptimizerInspector);
optAddEffect.addEventListener('click', openEffectSelectInspector);
optimizerRunBtn.addEventListener('click', runOptimization);
optimizerClearBtn.addEventListener('click', () => {
  optSelectedEffects.clear();
  renderOptEffectsTags();
  renderOptimizerVesselList();
  optMode.value = 'combined';
  optCandidates.value = '30';
  optTop.value = '50';
});

// Vessel collapsible header
optVesselHeader.addEventListener('click', toggleOptVesselCollapse);
// Update vessel count when checkboxes change
optVesselList.addEventListener('change', updateOptVesselCount);

// Mode change: clear deep-relic-only effects when switching to normal
optMode.addEventListener('change', () => {
  if (optMode.value === 'normal') {
    const toRemove = [];
    optSelectedEffects.forEach((priority, key) => {
      const eff = allUniqueEffects.find(e => e.key === key);
      if (eff && eff.deepOnly) toRemove.push(key);
    });
    toRemove.forEach(k => optSelectedEffects.delete(k));
    if (toRemove.length > 0) renderOptEffectsTags();
  }
});

// Preset save/load
const optPresetSave = document.getElementById('opt-preset-save');
const optPresetLoad = document.getElementById('opt-preset-load');

optPresetSave.addEventListener('click', async () => {
  const params = collectOptimizerParams();
  const preset = {
    version: 1,
    character: params.character,
    vessel: params.vessel,
    combined: params.combined,
    effects: params.effects,
    candidates: params.candidates,
    top: params.top,
  };
  const jsonStr = JSON.stringify(preset, null, 2);
  await window.api.savePresetDialog(jsonStr);
});

optPresetLoad.addEventListener('click', async () => {
  const preset = await window.api.loadPresetDialog();
  if (!preset) return;

  // Apply character
  if (preset.character) optCharacter.value = preset.character;

  // Apply vessels: uncheck all, then check matching
  if (preset.vessel) {
    const vesselKeys = preset.vessel.split(',');
    optVesselList.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.checked = vesselKeys.includes(cb.value);
    });
    updateOptVesselCount();
  }

  // Apply mode
  if (preset.combined !== undefined) optMode.value = preset.combined ? 'combined' : 'normal';

  // Apply effects (sort by rank within each priority group to restore order)
  optSelectedEffects.clear();
  if (preset.effects && Array.isArray(preset.effects)) {
    const sorted = [...preset.effects].sort((a, b) => {
      if (a.priority !== b.priority) return 0;
      return (a.rank || 0) - (b.rank || 0);
    });
    sorted.forEach(e => {
      const priority = e.exclude
        ? `exclude_${e.priority || 'required'}`
        : (e.priority || 'required');
      optSelectedEffects.set(e.key, priority);
    });
  }
  renderOptEffectsTags();

  // Apply settings
  if (preset.candidates) optCandidates.value = preset.candidates;
  if (preset.top) optTop.value = preset.top;
});

// ============================================================
// === Effect Selection Inspector ===
// ============================================================

function openEffectSelectInspector() {
  effectSelectBackdrop.classList.remove('hidden');
  effectSelectInspector.classList.add('open');
  effectSelectSearch.value = '';
  effectSelectSearchClear.classList.add('hidden');
  // Default all categories to collapsed
  EFFECT_CATEGORIES.forEach(c => effectSelectCollapsed.add(c.id));
  renderEffectSelectList();
  effectSelectSearch.focus();
}

function closeEffectSelectInspector() {
  effectSelectBackdrop.classList.add('hidden');
  effectSelectInspector.classList.remove('open');
}

function renderEffectSelectList() {
  const query = effectSelectSearch.value.toLowerCase().trim();
  const isNormalOnly = optMode.value === 'normal';
  let base = allUniqueEffects;
  // In normal-only mode, hide deep-relic-only effects
  if (isNormalOnly) {
    base = base.filter(e => !e.deepOnly);
  }
  const filtered = query
    ? base.filter(e =>
        e.name_ja.toLowerCase().includes(query) ||
        e.name_en.toLowerCase().includes(query) ||
        e.key.toLowerCase().includes(query))
    : base;

  // Group by category
  const groups = new Map();
  filtered.forEach(e => {
    const catId = e.category;
    if (!groups.has(catId)) groups.set(catId, []);
    groups.get(catId).push(e);
  });

  const ja = displayLang === 'ja';
  const catOrder = EFFECT_CATEGORIES.map(c => c.id);

  let html = '';
  catOrder.forEach(catId => {
    const items = groups.get(catId);
    if (!items || items.length === 0) return;
    const catDef = EFFECT_CATEGORIES.find(c => c.id === catId);
    const catName = catDef ? (ja ? catDef.ja : catDef.en) : (ja ? 'その他' : 'Other');
    const isCollapsed = effectSelectCollapsed.has(catId);

    // Determine select-all checkbox state for this category
    const catKeys = items.map(e => e.key);
    const checkedInCat = catKeys.filter(k => optSelectedEffects.has(k)).length;
    const allCatChecked = checkedInCat === catKeys.length;
    const someCatChecked = checkedInCat > 0 && !allCatChecked;

    html += `<div class="inspector-group-header${isCollapsed ? ' collapsed' : ''}" data-cat="${catId}">`;
    html += `<span class="inspector-group-arrow">▼</span>`;
    html += `<input type="checkbox" class="inspector-group-checkbox" data-cat="${catId}" ${allCatChecked ? 'checked' : ''} ${someCatChecked ? 'data-indeterminate="true"' : ''} />`;
    html += `<span class="group-name">${catName}</span>`;
    html += `<span class="group-count">(${items.length})</span>`;
    html += `</div>`;
    html += `<div class="inspector-group-items${isCollapsed ? ' collapsed' : ''}" data-cat="${catId}">`;
    items.forEach(e => {
      const name = ja ? e.name_ja : e.name_en;
      const checked = optSelectedEffects.has(e.key);
      const priority = optSelectedEffects.get(e.key) || 'required';
      const priorityOptions = ['required', 'preferred', 'nice_to_have',
        'exclude_required', 'exclude_preferred', 'exclude_nice_to_have'];
      const optionsHtml = priorityOptions.map(p => {
        const label = ja ? PRIORITY_LABELS[p].ja : PRIORITY_LABELS[p].en;
        return `<option value="${p}"${priority === p ? ' selected' : ''}>${label}</option>`;
      }).join('');

      html += `<div class="effect-select-item${checked ? ' checked' : ''}" data-key="${e.key}">
        <input type="checkbox" ${checked ? 'checked' : ''} />
        <span class="effect-select-name" title="${name}">${name}</span>
        <select${checked ? '' : ' style="visibility:hidden"'}>${optionsHtml}</select>
        <span class="effect-select-count">${e.count}</span>
      </div>`;
    });
    html += `</div>`;
  });

  effectSelectList.innerHTML = html;

  // Set indeterminate state for group checkboxes
  effectSelectList.querySelectorAll('.inspector-group-checkbox[data-indeterminate="true"]').forEach(cb => {
    cb.indeterminate = true;
  });

  // Collapsible group headers
  effectSelectList.querySelectorAll('.inspector-group-header').forEach(header => {
    header.addEventListener('click', (e) => {
      if (e.target.classList.contains('inspector-group-checkbox')) return;
      const catId = header.dataset.cat;
      const itemsDiv = effectSelectList.querySelector(`.inspector-group-items[data-cat="${catId}"]`);
      if (effectSelectCollapsed.has(catId)) {
        effectSelectCollapsed.delete(catId);
        header.classList.remove('collapsed');
        itemsDiv.classList.remove('collapsed');
      } else {
        effectSelectCollapsed.add(catId);
        header.classList.add('collapsed');
        itemsDiv.classList.add('collapsed');
      }
    });
  });
}

// Effect select checkbox/priority change handlers (delegated)
effectSelectList.addEventListener('change', (e) => {
  // Group select-all checkbox
  if (e.target.classList.contains('inspector-group-checkbox')) {
    const catId = e.target.dataset.cat;
    const catItems = effectSelectList.querySelectorAll(`.inspector-group-items[data-cat="${catId}"] .effect-select-item`);
    if (e.target.checked) {
      catItems.forEach(item => {
        const key = item.dataset.key;
        if (!optSelectedEffects.has(key)) {
          const select = item.querySelector('select');
          optSelectedEffects.set(key, select.value);
        }
      });
    } else {
      catItems.forEach(item => {
        optSelectedEffects.delete(item.dataset.key);
      });
    }
    renderEffectSelectList();
    return;
  }

  const item = e.target.closest('.effect-select-item');
  if (!item) return;
  const key = item.dataset.key;

  if (e.target.type === 'checkbox') {
    const select = item.querySelector('select');
    if (e.target.checked) {
      optSelectedEffects.set(key, select.value);
      select.style.visibility = '';
      item.classList.add('checked');
    } else {
      optSelectedEffects.delete(key);
      select.style.visibility = 'hidden';
      item.classList.remove('checked');
    }
  } else if (e.target.tagName === 'SELECT') {
    if (optSelectedEffects.has(key)) {
      optSelectedEffects.set(key, e.target.value);
    }
  }
});

// Click on item text toggles checkbox; select clicks are excluded
effectSelectList.addEventListener('click', (e) => {
  if (e.target.tagName === 'SELECT' || e.target.tagName === 'OPTION' || e.target.tagName === 'INPUT') return;
  const item = e.target.closest('.effect-select-item');
  if (!item) return;
  const checkbox = item.querySelector('input[type="checkbox"]');
  if (checkbox) {
    checkbox.checked = !checkbox.checked;
    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
  }
});

effectSelectClose.addEventListener('click', closeEffectSelectInspector);
effectSelectBackdrop.addEventListener('click', closeEffectSelectInspector);

effectSelectSearch.addEventListener('input', () => {
  effectSelectSearchClear.classList.toggle('hidden', !effectSelectSearch.value);
  renderEffectSelectList();
});
effectSelectSearchClear.addEventListener('click', () => {
  effectSelectSearch.value = '';
  effectSelectSearchClear.classList.add('hidden');
  renderEffectSelectList();
  effectSelectSearch.focus();
});

effectSelectApplyBtn.addEventListener('click', () => {
  closeEffectSelectInspector();
  renderOptEffectsTags();
});

effectSelectClearBtn.addEventListener('click', () => {
  optSelectedEffects.clear();
  renderEffectSelectList();
});

// ============================================================
// === Optimizer Results Rendering ===
// ============================================================

function renderOptimizerResults(tabId, data, params, sortKey, sortDir) {
  const container = document.getElementById(`opt-result-${tabId}`);
  if (!container) return;
  const ja = displayLang === 'ja';

  sortKey = sortKey || 'score';
  sortDir = sortDir || 'desc';

  const bestResult = data.bestResult;
  const allResults = data.allResults || [];

  // Flatten all results across all vessels into a single sorted list
  const flatResults = [];
  allResults.forEach(vesselOutput => {
    const vesselInfo = vesselOutput.parameters && vesselOutput.parameters.vessel;
    (vesselOutput.results || []).forEach(res => {
      const vi = res.vessel || vesselInfo;
      flatResults.push({
        ...res,
        _vesselInfo: vi || null,
        _vesselNameJa: vi ? vi.nameJa : (vesselOutput.parameters.color || res._color || '?'),
        _vesselNameEn: vi ? vi.nameEn : (vesselOutput.parameters.color || res._color || '?'),
      });
    });
  });

  // Sort
  flatResults.sort((a, b) => {
    if (sortKey === 'score') {
      const cmp = (b.requiredMet === a.requiredMet) ? 0 : (b.requiredMet ? 1 : -1);
      if (cmp !== 0) return cmp;
      const scoreCmp = sortDir === 'desc' ? b.score - a.score : a.score - b.score;
      if (scoreCmp !== 0) return scoreCmp;
      // subScore tiebreaker (always descending)
      return (b.subScore || 0) - (a.subScore || 0);
    }
    return 0;
  });

  let html = '';

  // Summary header
  if (bestResult) {
    const best = bestResult.result;
    const vesselName = bestResult.parameters && bestResult.parameters.vessel
      ? (ja ? bestResult.parameters.vessel.nameJa : bestResult.parameters.vessel.nameEn)
      : '';
    html += `<div class="opt-results-summary">`;
    html += `<div class="opt-results-summary-title">${ja ? 'ビルド探索結果' : 'Build Search Results'}</div>`;
    html += `<div class="opt-results-summary-info">`;
    html += `<span>${ja ? '最高スコア' : 'Best Score'}: ${best.score}</span>`;
    html += `<span>${ja ? '献器' : 'Vessel'}: ${vesselName}</span>`;
    html += `<span>${ja ? '必須充足' : 'Required'}: ${best.requiredMet ? '✓' : '✗'}</span>`;
    html += `<span>${ja ? '総件数' : 'Total'}: ${flatResults.length}</span>`;
    html += `<button class="btn-export-optimizer" data-tab="${tabId}">&#128190; ${ja ? 'エクスポート' : 'Export'}</button>`;
    html += `</div></div>`;
  }

  // Search conditions
  html += `<div class="opt-conditions-summary">`;
  html += `<div class="opt-conditions-title">${ja ? '検索条件' : 'Search Conditions'}</div>`;
  html += `<div class="opt-conditions-row">`;
  html += `<span class="opt-conditions-label">${ja ? 'キャラクター' : 'Character'}:</span>`;
  html += `<span class="opt-conditions-value">${params.character || '-'}</span>`;
  html += `</div>`;
  if (params.vessel) {
    const vesselKeys = params.vessel.split(',');
    const vesselNames = vesselKeys.map(vk => {
      if (vesselsData) {
        const vt = (vesselsData.vesselTypes || []).find(v => v.key === vk);
        if (vt) return ja ? vt.nameJa : vt.nameEn;
        const uv = (vesselsData.universalVessels || []).find(v => v.key === vk);
        if (uv) return ja ? uv.nameJa : uv.nameEn;
      }
      return vk;
    });
    html += `<div class="opt-conditions-row">`;
    html += `<span class="opt-conditions-label">${ja ? '献器' : 'Vessels'}:</span>`;
    html += `<span class="opt-conditions-value">${vesselNames.join(', ')}</span>`;
    html += `</div>`;
  }
  html += `<div class="opt-conditions-row">`;
  html += `<span class="opt-conditions-label">${ja ? 'モード' : 'Mode'}:</span>`;
  html += `<span class="opt-conditions-value">${params.combined ? (ja ? '通常+深層' : 'Combined') : (ja ? '通常のみ' : 'Normal only')}</span>`;
  html += `</div>`;
  if (params.effects && params.effects.length > 0) {
    html += `<div class="opt-conditions-row">`;
    html += `<span class="opt-conditions-label">${ja ? '効果' : 'Effects'}:</span>`;
    html += `<div class="opt-conditions-effects">`;
    params.effects.forEach(e => {
      const eff = allUniqueEffects.find(u => u.key === e.key);
      const name = eff ? (ja ? eff.name_ja : eff.name_en) : e.key;
      const displayPriority = e.exclude ? `exclude_${e.priority}` : e.priority;
      const pLabel = PRIORITY_LABELS[displayPriority]
        ? (ja ? PRIORITY_LABELS[displayPriority].ja : PRIORITY_LABELS[displayPriority].en) : displayPriority;
      html += `<span class="opt-conditions-effect-tag ${displayPriority}">${name} <small>(${pLabel})</small></span>`;
    });
    html += `</div></div>`;
  }
  html += `</div>`;

  // Headline bar (column headers like the relic list)
  const scoreLabel = ja ? 'スコア' : 'Score';
  const vesselLabel = ja ? '献器' : 'Vessel';
  const reqLabel = ja ? '必須充足' : 'Required';
  const rankLabel = '#';
  const scoreArrow = sortKey === 'score' ? (sortDir === 'desc' ? ' ▼' : ' ▲') : '';
  html += `<div class="opt-result-headline">`;
  html += `<span class="opt-hl-rank">${rankLabel}</span>`;
  html += `<span class="opt-hl-score sortable${sortKey === 'score' ? ' active' : ''}" data-sort="score">${scoreLabel}${scoreArrow}</span>`;
  html += `<span class="opt-hl-req">${reqLabel}</span>`;
  html += `<span class="opt-hl-vessel">${vesselLabel}</span>`;
  html += `</div>`;

  // Render flat result list
  const bestKey = bestResult && bestResult.parameters && bestResult.parameters.vessel
    ? bestResult.parameters.vessel.key : null;
  const bestScore = bestResult ? bestResult.result.score : -1;

  flatResults.forEach((res, idx) => {
    const isBest = bestKey && res._vesselInfo && res._vesselInfo.key === bestKey
      && res.score === bestScore && res.rank === 1;
    html += renderResultCard(res, ja, isBest, params, idx);
  });

  if (flatResults.length === 0) {
    html += `<div class="opt-loading"><p>${ja ? '結果なし' : 'No results'}</p></div>`;
  }

  container.innerHTML = html;

  // Click handler: show detail panel on the right (entire card is clickable)
  container.querySelectorAll('.opt-result-card').forEach(card => {
    card.addEventListener('click', () => {
      const idx = parseInt(card.dataset.idx, 10);
      container.querySelectorAll('.opt-result-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      showOptResultDetail(tabId, flatResults[idx], params, idx);
    });
  });

  // Sort button handlers (headline columns)
  container.querySelectorAll('.opt-result-headline .sortable').forEach(col => {
    col.addEventListener('click', () => {
      const key = col.dataset.sort;
      let dir = 'desc';
      if (key === sortKey) dir = sortDir === 'desc' ? 'asc' : 'desc';
      renderOptimizerResults(tabId, data, params, key, dir);
    });
  });

  // Export button handler
  container.querySelectorAll('.btn-export-optimizer').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      exportOptimizerResultsToHTML(btn.dataset.tab);
    });
  });
}

function renderResultCard(res, ja, isBest, params, idx) {
  const cardClass = `opt-result-card${isBest ? ' best' : ''}`;
  const vesselName = ja ? res._vesselNameJa : res._vesselNameEn;
  const matchedSet = new Set(res.matchedEffects || []);
  const excludedSet = new Set(res.excludedPresent || []);
  const specKeys = new Set((params.effects || []).filter(e => !e.exclude).map(e => e.key));
  const excludeSpecKeys = new Set((params.effects || []).filter(e => e.exclude).map(e => e.key));

  let html = `<div class="${cardClass}" data-idx="${idx}">`;
  html += `<div class="opt-result-header">`;
  html += `<span class="opt-rank">#${idx + 1}</span>`;
  html += `<span class="opt-score">${ja ? 'スコア' : 'Score'}: ${res.score}</span>`;
  if (res.subScore) html += `<span class="opt-sub-score">(sub: ${res.subScore})</span>`;
  html += `<span class="opt-required-badge ${res.requiredMet ? 'met' : 'not-met'}">`;
  html += `${res.requiredMet ? '✓' : '✗'}</span>`;
  html += `<span class="opt-vessel-name">${vesselName}</span>`;
  html += `</div>`;

  // Card body: per-relic rows (relic name left, its effects right, aligned)
  const allRelics = [].concat(res.normalRelics || [], res.deepRelics || [], res.relics || []);
  if (allRelics.length > 0) {
    html += `<div class="opt-card-body">`;

    allRelics.forEach(r => {
      const rName = ja ? (r.itemNameJa || r.itemNameEn || r.itemKey) : (r.itemNameEn || r.itemKey);
      html += `<div class="opt-card-row">`;
      html += `<div class="opt-card-relic"><span class="color-badge ${r.itemColor}"></span>${rName}</div>`;
      html += `<div class="opt-card-effects">`;
      (r.effects || []).forEach(eff => {
        if (eff.isDebuff) return; // skip sub-effects for compact view
        const effName = ja ? (eff.name_ja || eff.name_en || eff.key) : (eff.name_en || eff.key);
        const isMatched = matchedSet.has(eff.key);
        const isExcluded = eff.excluded || excludedSet.has(eff.key);
        const isSpec = specKeys.has(eff.key);
        const isExcludeSpec = excludeSpecKeys.has(eff.key);
        let cls = 'opt-card-effect';
        if (isExcluded) {
          const exPriority = eff.excludePriority || 'required';
          cls += ` excluded exclude_${exPriority}`;
        } else if (isMatched) {
          const spec = params.effects.find(e => e.key === eff.key && !e.exclude);
          cls += ` matched ${spec ? spec.priority : 'nice_to_have'}`;
        } else if (isSpec) {
          cls += ' spec-miss';
        }
        html += `<span class="${cls}">${effName}</span>`;
      });
      html += `</div>`;
      html += `</div>`;
    });

    html += `</div>`;
  }

  html += `</div>`;
  return html;
}

function computeScoreBreakdown(res, params) {
  const allRelics = [...(res.normalRelics || []), ...(res.deepRelics || [])];
  const matchedKeys = new Set(res.matchedEffects || []);
  const excludedKeys = new Set(res.excludedPresent || []);

  // Count matched effect occurrences across all relics
  const matchedCounts = {};
  const excludedCounts = {};
  for (const relic of allRelics) {
    for (const eff of relic.effects) {
      if (eff.matched && matchedKeys.has(eff.key)) {
        matchedCounts[eff.key] = (matchedCounts[eff.key] || 0) + 1;
      }
      if (eff.excluded && excludedKeys.has(eff.key)) {
        excludedCounts[eff.key] = (excludedCounts[eff.key] || 0) + 1;
      }
    }
  }

  // Build key -> stackable lookup
  const keyToStackable = {};
  for (const [id, info] of Object.entries(stackingLookup)) {
    if (info.key) keyToStackable[info.key] = info.stackable;
  }

  // Compute per-effect score contribution
  const effects = [];
  let effectsTotal = 0;
  for (const key of (res.matchedEffects || [])) {
    const spec = params.effects.find(e => e.key === key && !e.exclude);
    const priority = spec ? spec.priority : 'nice_to_have';
    const w = PRIORITY_WEIGHTS[priority] || 1;
    const count = matchedCounts[key] || 1;
    const stackable = keyToStackable[key];

    let contribution;
    if (stackable === true) {
      contribution = w * count;
    } else if (stackable === 'conditional') {
      contribution = w;
      if (count > 1) contribution -= Math.trunc(w * 0.3) * (count - 1);
    } else {
      contribution = w;
      if (count > 1) contribution -= Math.trunc(w * 0.5) * (count - 1);
    }
    effects.push({ key, priority, weight: w, count, stackable, contribution });
    effectsTotal += contribution;
  }

  // Compute concentration bonus per relic
  let concentrationBonus = 0;
  const concentrationDetails = [];
  for (const relic of allRelics) {
    let matchedOnRelic = 0;
    const matchedNames = [];
    for (const eff of relic.effects) {
      if (eff.matched && matchedKeys.has(eff.key)) {
        matchedOnRelic++;
        matchedNames.push(eff.key);
      }
    }
    if (matchedOnRelic >= 2) {
      const bonus = Math.trunc(CONCENTRATION_BONUS * matchedOnRelic * (matchedOnRelic - 1) / 2);
      concentrationBonus += bonus;
      concentrationDetails.push({
        itemNameJa: relic.itemNameJa || relic.itemNameEn || relic.itemKey,
        itemNameEn: relic.itemNameEn || relic.itemKey,
        matchedCount: matchedOnRelic,
        matchedNames,
        bonus,
      });
    }
  }

  // Compute exclude penalty
  const excludeEffects = [];
  let excludePenalty = 0;
  for (const key of (res.excludedPresent || [])) {
    const spec = params.effects.find(e => e.key === key && e.exclude);
    const priority = spec ? spec.priority : 'nice_to_have';
    const w = PRIORITY_WEIGHTS[priority] || 1;
    const count = excludedCounts[key] || 1;
    const contribution = w * count;
    excludeEffects.push({ key, priority, count, contribution });
    excludePenalty += contribution;
  }

  return {
    effects,
    effectsTotal,
    concentrationBonus,
    concentrationDetails,
    excludeEffects,
    excludePenalty,
    total: effectsTotal + concentrationBonus - excludePenalty,
  };
}

// === Optimizer Result Detail Panel ===

function showOptResultDetail(tabId, res, params, idx) {
  const panel = document.getElementById(`opt-detail-${tabId}`);
  if (!panel) return;
  panel.classList.remove('hidden');
  const ja = displayLang === 'ja';

  const title = panel.querySelector('.opt-detail-title');
  const body = panel.querySelector('.opt-detail-body');
  const vesselName = ja ? res._vesselNameJa : res._vesselNameEn;
  title.textContent = `#${idx + 1} ${vesselName}`;

  let html = '';

  // Score info section
  html += `<div class="detail-section">`;
  html += `<h3>${ja ? 'スコア情報' : 'Score Info'}</h3>`;
  html += field(ja ? 'スコア' : 'Score', res.score);
  if (res.subScore) html += field(ja ? 'サブスコア' : 'Sub Score', res.subScore);
  html += field(ja ? '必須充足' : 'Required Met', res.requiredMet ? '✓' : '✗');
  html += field(ja ? '献器' : 'Vessel', vesselName);
  html += `</div>`;

  // Normal relics section
  if (res.normalRelics && res.normalRelics.length > 0) {
    html += `<div class="detail-section">`;
    html += `<h3>${ja ? '通常遺物' : 'Normal Relics'}</h3>`;
    res.normalRelics.forEach(r => { html += renderOptDetailRelic(r, ja); });
    html += `</div>`;
  }

  // Deep relics section
  if (res.deepRelics && res.deepRelics.length > 0) {
    html += `<div class="detail-section">`;
    html += `<h3>${ja ? '深層遺物' : 'Deep Relics'}</h3>`;
    res.deepRelics.forEach(r => { html += renderOptDetailRelic(r, ja); });
    html += `</div>`;
  }

  // Legacy relics (non-combined)
  if (res.relics && !res.normalRelics) {
    html += `<div class="detail-section">`;
    html += `<h3>${ja ? '遺物' : 'Relics'}</h3>`;
    res.relics.forEach(r => { html += renderOptDetailRelic(r, ja); });
    html += `</div>`;
  }

  // Score breakdown section
  const bd = computeScoreBreakdown(res, params);
  html += `<div class="detail-section">`;
  html += `<h3>${ja ? 'スコア内訳' : 'Score Breakdown'}</h3>`;

  // Matched effects with score contribution
  for (const ef of bd.effects) {
    const eff = allUniqueEffects.find(e => e.key === ef.key);
    const name = eff ? (ja ? eff.name_ja : eff.name_en) : ef.key;
    const pLabel = PRIORITY_LABELS[ef.priority]
      ? (ja ? PRIORITY_LABELS[ef.priority].ja : PRIORITY_LABELS[ef.priority].en) : ef.priority;
    const stackLabel = ef.stackable === true ? (ja ? '重複:○' : 'Stack:Y')
      : ef.stackable === 'conditional' ? (ja ? '重複:△' : 'Stack:C')
      : (ja ? '重複:×' : 'Stack:N');
    const countInfo = ef.count > 1 ? ` ×${ef.count}` : '';
    html += `<div class="detail-score-row">`;
    html += `<div class="detail-effect-main">${name}</div>`;
    html += `<div class="detail-effect-meta">${pLabel}${countInfo} ${stackLabel}</div>`;
    html += `<div class="detail-effect-score" style="color:#80d080">+${ef.contribution}</div>`;
    html += `</div>`;
  }

  // Missing required
  (res.missingRequired || []).forEach(key => {
    const eff = allUniqueEffects.find(e => e.key === key);
    const name = eff ? (ja ? eff.name_ja : eff.name_en) : key;
    html += `<div class="detail-score-row" style="opacity:0.5">`;
    html += `<div class="detail-effect-main" style="color:#e07070">${name}</div>`;
    html += `<div class="detail-effect-meta">${ja ? '未達' : 'Missing'}</div>`;
    html += `<div class="detail-effect-score"></div>`;
    html += `</div>`;
  });

  // Concentration bonus
  if (bd.concentrationBonus > 0) {
    html += `<div class="detail-score-row summary">`;
    html += `<div class="detail-effect-main">${ja ? '集中ボーナス' : 'Concentration Bonus'}</div>`;
    html += `<div class="detail-effect-meta"></div>`;
    html += `<div class="detail-effect-score" style="color:#80d080">+${bd.concentrationBonus}</div>`;
    html += `</div>`;
    for (const cd of bd.concentrationDetails) {
      const relicName = ja ? cd.itemNameJa : cd.itemNameEn;
      const effNames = cd.matchedNames.map(k => {
        const e = allUniqueEffects.find(u => u.key === k);
        return e ? (ja ? e.name_ja : e.name_en) : k;
      }).join(', ');
      html += `<div class="detail-score-row" style="padding-left:20px;opacity:0.7">`;
      html += `<div class="detail-effect-main" style="font-size:11px">${relicName} (${effNames})</div>`;
      html += `<div class="detail-effect-meta">×${cd.matchedCount}</div>`;
      html += `<div class="detail-effect-score" style="color:#80d080;font-size:11px">+${cd.bonus}</div>`;
      html += `</div>`;
    }
  }

  // Exclude effects with penalty
  for (const ef of bd.excludeEffects) {
    const eff = allUniqueEffects.find(e => e.key === ef.key);
    const name = eff ? (ja ? eff.name_ja : eff.name_en) : ef.key;
    const displayPriority = `exclude_${ef.priority}`;
    const pLabel = PRIORITY_LABELS[displayPriority]
      ? (ja ? PRIORITY_LABELS[displayPriority].ja : PRIORITY_LABELS[displayPriority].en) : displayPriority;
    const countInfo = ef.count > 1 ? ` ×${ef.count}` : '';
    html += `<div class="detail-score-row">`;
    html += `<div class="detail-effect-main" style="color:#e07070;text-decoration:line-through">${name}</div>`;
    html += `<div class="detail-effect-meta">${pLabel}${countInfo}</div>`;
    html += `<div class="detail-effect-score" style="color:#e07070">-${ef.contribution}</div>`;
    html += `</div>`;
  }

  // Total
  html += `<div class="detail-score-row total">`;
  html += `<div class="detail-effect-main">${ja ? '合計' : 'Total'}</div>`;
  html += `<div class="detail-effect-meta"></div>`;
  html += `<div class="detail-effect-score">${bd.total}</div>`;
  html += `</div>`;

  html += `</div>`;

  body.innerHTML = html;

  // Close button
  panel.querySelector('.opt-detail-close').onclick = () => {
    panel.classList.add('hidden');
    const container = document.getElementById(`opt-result-${tabId}`);
    if (container) container.querySelectorAll('.opt-result-card').forEach(c => c.classList.remove('selected'));
  };
}

function renderOptDetailRelic(relic, ja) {
  const itemName = ja
    ? (relic.itemNameJa || relic.itemNameEn || relic.itemKey)
    : (relic.itemNameEn || relic.itemKey);
  const typeBadge = TYPE_LABELS[relic.itemType];
  const typeStr = typeBadge ? typeBadge[ja ? 'ja' : 'en'] : relic.itemType;

  let html = `<div class="detail-effect">`;
  html += `<div class="detail-effect-main">`;
  html += `<span class="color-badge ${relic.itemColor}"></span> `;
  html += `<span class="type-badge ${relic.itemType}" style="font-size:10px;padding:1px 5px">${typeStr}</span> `;
  html += itemName;
  html += `</div>`;

  // Group effects: main + sub-effects
  const effectGroups = [];
  let currentGroup = null;
  (relic.effects || []).forEach(eff => {
    if (eff.isDebuff && currentGroup) {
      currentGroup.debuffs.push(eff);
    } else {
      currentGroup = { main: eff, debuffs: [] };
      effectGroups.push(currentGroup);
    }
  });

  effectGroups.forEach(group => {
    const mainName = ja
      ? (group.main.name_ja || group.main.name_en || group.main.key)
      : (group.main.name_en || group.main.key);
    const matched = group.main.matched;
    const excluded = group.main.excluded;
    let effCls = 'opt-detail-effect-name';
    if (excluded) effCls += ' excluded';
    else if (matched) effCls += ' matched';
    html += `<div class="opt-detail-effect-item">`;
    html += `<div class="${effCls}">${mainName}</div>`;
    group.debuffs.forEach(d => {
      const dName = ja ? (d.name_ja || d.name_en || d.key) : (d.name_en || d.key);
      const isDemerit = classifyEffect(d.name_ja, d.name_en, d.key) === 'demerit';
      html += `<div class="opt-detail-effect-sub ${isDemerit ? 'demerit' : ''}">${dName}</div>`;
    });
    html += `</div>`;
  });

  html += `</div>`;
  return html;
}

// ============================================================
// === HTML Export ===
// ============================================================

const EXPORT_CSS = `
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg-primary: #1a1a1a; --bg-secondary: #242424; --bg-tertiary: #2d2d2d;
  --bg-hover: #363636; --text-primary: #e0e0e0; --text-secondary: #a0a0a0;
  --text-muted: #707070; --accent: #4cc9b0; --accent-hover: #5cd4bc;
  --border: #3a3a3a; --color-red: #e74c3c; --color-blue: #3498db;
  --color-yellow: #f1c40f; --color-green: #2ecc71;
}
body {
  font-family: 'Segoe UI', 'Meiryo', sans-serif;
  background: var(--bg-primary); color: var(--text-primary);
  padding: 24px; line-height: 1.5;
}
.export-header { margin-bottom: 20px; }
.export-header h1 { font-size: 20px; color: var(--accent); margin-bottom: 4px; }
.export-meta {
  display: flex; gap: 16px; flex-wrap: wrap;
  font-size: 12px; color: var(--text-secondary);
  padding: 10px 14px; background: var(--bg-secondary);
  border-radius: 6px; border: 1px solid var(--border); margin-bottom: 16px;
}
.export-meta span { white-space: nowrap; }
.export-section { margin-top: 28px; }
.export-section-title {
  font-size: 16px; color: var(--accent); font-weight: 600;
  border-bottom: 2px solid var(--border); padding-bottom: 6px; margin-bottom: 14px;
}
.export-footer {
  margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);
  text-align: center; font-size: 11px; color: var(--text-muted);
}
/* Table */
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead th {
  background: var(--bg-tertiary); color: var(--accent);
  padding: 10px 12px; text-align: left; font-weight: 600;
  font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border); white-space: nowrap;
}
td { padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
tbody tr:hover { background: var(--bg-hover); }
/* Badges */
.color-badge {
  display: inline-block; width: 14px; height: 14px;
  border-radius: 3px; margin-right: 6px; vertical-align: middle;
}
.color-badge.Red { background: var(--color-red); }
.color-badge.Blue { background: var(--color-blue); }
.color-badge.Yellow { background: var(--color-yellow); }
.color-badge.Green { background: var(--color-green); }
.color-label { vertical-align: middle; }
.type-badge {
  display: inline-block; padding: 2px 8px; border-radius: 3px;
  font-size: 11px; font-weight: 600;
}
.type-badge.Relic { background: rgba(76,201,176,0.15); color: var(--accent); border: 1px solid rgba(76,201,176,0.3); }
.type-badge.DeepRelic { background: rgba(128,0,255,0.15); color: #b080ff; border: 1px solid rgba(128,0,255,0.3); }
.type-badge.UniqueRelic { background: rgba(231,76,60,0.15); color: #ff8070; border: 1px solid rgba(231,76,60,0.3); }
/* Effects in table */
.effect-item { position: relative; padding-left: 14px; margin-bottom: 4px; }
.effect-item::before { content: '•'; position: absolute; left: 0; top: 0; color: var(--accent); font-size: 14px; line-height: 1.6; }
.effect-main { line-height: 1.6; font-size: 12px; }
.effect-debuff { color: #e07070; font-size: 11px; line-height: 1.5; padding-left: 10px; position: relative; }
.effect-debuff::before { content: '└'; position: absolute; left: -2px; top: -1px; color: #e07070; font-size: 11px; }
/* Optimizer cards */
.opt-results-summary {
  margin-bottom: 16px; padding: 12px 16px; background: var(--bg-secondary);
  border-radius: 6px; border: 1px solid var(--border);
}
.opt-results-summary-title { font-size: 14px; color: var(--accent); font-weight: 600; margin-bottom: 6px; }
.opt-results-summary-info { font-size: 12px; color: var(--text-secondary); display: flex; gap: 16px; flex-wrap: wrap; }
.opt-conditions-summary {
  margin-bottom: 12px; padding: 10px 14px; background: var(--bg-secondary);
  border-radius: 6px; border: 1px solid var(--border); font-size: 12px;
}
.opt-conditions-title { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.opt-conditions-row { display: flex; gap: 6px; margin-bottom: 3px; align-items: flex-start; }
.opt-conditions-label { color: var(--text-secondary); flex-shrink: 0; }
.opt-conditions-value { color: var(--text-primary); }
.opt-conditions-effects { display: flex; flex-wrap: wrap; gap: 4px; }
.opt-conditions-effect-tag { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 11px; }
.opt-conditions-effect-tag.required { background: rgba(76,201,176,0.15); color: var(--accent); }
.opt-conditions-effect-tag.preferred { background: rgba(52,152,219,0.15); color: var(--color-blue); }
.opt-conditions-effect-tag.nice_to_have { background: rgba(241,196,15,0.15); color: var(--color-yellow); }
.opt-conditions-effect-tag.exclude_required { background: rgba(231,76,60,0.2); color: #e07070; text-decoration: line-through; }
.opt-conditions-effect-tag.exclude_preferred { background: rgba(231,76,60,0.12); color: #d4877a; text-decoration: line-through; }
.opt-conditions-effect-tag.exclude_nice_to_have { background: rgba(231,76,60,0.08); color: #c09080; text-decoration: line-through; }
.opt-conditions-effect-tag small { opacity: 0.7; }
.opt-result-card {
  background: var(--bg-secondary); border: 1px solid var(--border);
  border-radius: 4px; margin-bottom: 2px; overflow: hidden;
}
.opt-result-card.best { border-color: var(--accent); }
.opt-result-header { display: flex; align-items: center; gap: 10px; padding: 10px 14px; }
.opt-rank { font-size: 12px; color: var(--text-muted); font-weight: 600; width: 36px; text-align: center; flex-shrink: 0; }
.opt-score { font-size: 13px; color: var(--text-primary); font-weight: 600; width: 120px; flex-shrink: 0; }
.opt-sub-score { font-size: 11px; color: var(--text-muted); }
.opt-required-badge { font-size: 11px; padding: 2px 8px; border-radius: 3px; font-weight: 600; width: 80px; flex-shrink: 0; text-align: center; }
.opt-required-badge.met { background: rgba(46,204,113,0.15); color: var(--color-green); border: 1px solid rgba(46,204,113,0.3); }
.opt-required-badge.not-met { background: rgba(231,76,60,0.15); color: var(--color-red); border: 1px solid rgba(231,76,60,0.3); }
.opt-vessel-name { font-size: 12px; color: var(--text-secondary); flex: 1; }
.opt-card-body { display: flex; flex-direction: column; gap: 2px; padding: 0 14px 8px; font-size: 11px; }
.opt-card-row { display: flex; align-items: baseline; gap: 10px; min-height: 20px; }
.opt-card-relic { flex-shrink: 0; display: flex; align-items: center; gap: 3px; color: var(--text-secondary); font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 180px; min-width: 0; }
.opt-card-relic .color-badge { width: 8px; height: 8px; margin-right: 2px; flex-shrink: 0; }
.opt-card-effects { flex: 1; display: flex; flex-wrap: wrap; gap: 3px; align-items: baseline; min-width: 0; }
.opt-card-effect { display: inline-block; padding: 1px 5px; border-radius: 3px; font-size: 10px; background: var(--bg-tertiary); color: var(--text-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.5; }
.opt-card-effect.matched.required { background: rgba(76,201,176,0.2); color: var(--accent); font-weight: 600; }
.opt-card-effect.matched.preferred { background: rgba(52,152,219,0.2); color: var(--color-blue); font-weight: 600; }
.opt-card-effect.matched.nice_to_have { background: rgba(241,196,15,0.2); color: var(--color-yellow); font-weight: 600; }
.opt-card-effect.excluded { background: rgba(231,76,60,0.15); color: #e07070; text-decoration: line-through; }
.opt-card-effect.excluded.exclude_required { background: rgba(231,76,60,0.25); font-weight: 600; }
/* Detail / Score breakdown */
.detail-section { margin-bottom: 18px; }
.detail-section h3 { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.detail-field { display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; }
.detail-field .label { color: var(--text-secondary); }
.detail-field .value { color: var(--text-primary); font-weight: 500; }
.detail-effect { background: var(--bg-tertiary); border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; }
.detail-effect-main { font-size: 13px; color: var(--text-primary); font-weight: 500; }
.detail-score-row { background: var(--bg-tertiary); border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
.detail-score-row .detail-effect-main { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.detail-effect-meta { font-size: 11px; color: var(--text-secondary); white-space: nowrap; flex-shrink: 0; }
.detail-effect-score { font-size: 13px; font-weight: 600; font-family: 'Consolas','Monaco',monospace; white-space: nowrap; flex-shrink: 0; min-width: 48px; text-align: right; }
.detail-score-row.summary { border-top: 1px solid var(--border); margin-top: 4px; padding-top: 10px; }
.detail-score-row.total { border-top: 2px solid var(--text-secondary); margin-top: 4px; padding-top: 10px; background: transparent; }
.detail-score-row.total .detail-effect-main { font-size: 14px; font-weight: 700; }
.detail-score-row.total .detail-effect-score { font-size: 14px; font-weight: 700; color: var(--text-primary); }
/* Relic detail in optimizer */
.opt-relic-section { margin-bottom: 8px; }
.opt-relic-section h5 { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.opt-relic-card { display: flex; align-items: flex-start; gap: 8px; padding: 6px 8px; background: var(--bg-tertiary); border-radius: 4px; margin-bottom: 4px; }
.opt-relic-name { font-size: 12px; color: var(--text-primary); font-weight: 500; min-width: 120px; }
.opt-relic-effects { display: flex; flex-direction: column; gap: 3px; flex: 1; }
.opt-effect-group { display: flex; flex-wrap: wrap; align-items: center; gap: 3px; }
.opt-effect { font-size: 11px; padding: 1px 6px; border-radius: 3px; background: var(--bg-primary); color: var(--text-secondary); }
.opt-effect.matched { background: rgba(76,201,176,0.12); color: var(--accent); font-weight: 500; }
.opt-effect.matched-required { background: rgba(76,201,176,0.2); color: var(--accent); font-weight: 600; }
.opt-effect.debuff { color: #e07070; background: rgba(224,112,112,0.1); font-size: 10px; }
.opt-effect-debuff-link { font-size: 10px; color: #e07070; margin-left: 2px; }
`;

function downloadHTML(filename, htmlContent) {
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function buildExportHTML(title, bodyHTML, metaItems) {
  const metaHTML = metaItems.map(m => `<span>${m}</span>`).join('');
  return `<!DOCTYPE html>
<html lang="${displayLang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${title}</title>
<style>${EXPORT_CSS}</style>
</head>
<body>
<div class="export-header">
<h1>${title}</h1>
</div>
<div class="export-meta">${metaHTML}</div>
${bodyHTML}
<div class="export-footer">ERN RelicForge ${APP_NIGHTREIGN_VERSION} — Exported ${new Date().toLocaleString()}</div>
</body>
</html>`;
}

// --- Relic Table Export ---
function exportRelicTableToHTML() {
  if (!filteredRelics || filteredRelics.length === 0) return;
  const ja = displayLang === 'ja';

  const metaItems = [];
  if (loadedFileName) metaItems.push(`${ja ? 'ファイル' : 'File'}: ${loadedFileName}`);
  metaItems.push(`${ja ? '件数' : 'Count'}: ${filteredRelics.length}`);
  if (colorFilterValue) metaItems.push(`${ja ? '色' : 'Color'}: ${colorFilterValue}`);
  const typeVal = filterType.value;
  if (typeVal) metaItems.push(`${ja ? 'タイプ' : 'Type'}: ${typeLabel(typeVal)}`);
  const searchVal = searchInput.value.trim();
  if (searchVal) metaItems.push(`${ja ? '検索' : 'Search'}: ${searchVal}`);

  let html = `<table><thead><tr>`;
  html += `<th>#</th>`;
  html += `<th>${ja ? '色' : 'Color'}</th>`;
  html += `<th>${ja ? 'タイプ' : 'Type'}</th>`;
  html += `<th>${ja ? 'アイテム' : 'Item'}</th>`;
  html += `<th>${ja ? '効果' : 'Effects'}</th>`;
  html += `</tr></thead><tbody>`;

  filteredRelics.forEach((relic, idx) => {
    html += `<tr>`;
    html += `<td style="color:var(--text-muted)">${idx + 1}</td>`;
    html += `<td><span class="color-badge ${relic.itemColor}"></span><span class="color-label">${relic.itemColor || '-'}</span></td>`;
    html += `<td><span class="type-badge ${relic.itemType}">${typeLabel(relic.itemType)}</span></td>`;
    const itemName = ja
      ? (relic.itemNameJa || relic.itemNameEn || relic.itemKey)
      : (relic.itemNameEn || relic.itemKey);
    html += `<td style="font-size:12px">${itemName}</td>`;
    html += `<td>`;
    relic.effects.forEach(group => {
      const main = group[0];
      const mainName = ja ? (main.name_ja || main.name_en || main.key) : (main.name_en || main.key);
      html += `<div class="effect-item"><div class="effect-main">${mainName}</div>`;
      for (let i = 1; i < group.length; i++) {
        const d = group[i];
        const dName = ja ? (d.name_ja || d.name_en || d.key) : (d.name_en || d.key);
        html += `<div class="effect-debuff">${dName}</div>`;
      }
      html += `</div>`;
    });
    html += `</td></tr>`;
  });

  html += `</tbody></table>`;

  const title = ja ? '遺物一覧 — ERN RelicForge' : 'Relic List — ERN RelicForge';
  const fullHTML = buildExportHTML(title, html, metaItems);
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  downloadHTML(`relicforge_relics_${ts}.html`, fullHTML);
}

// --- Optimizer Results Export ---
function exportOptimizerResultsToHTML(tabId) {
  const tabData = optimizerTabs.get(tabId);
  if (!tabData || !tabData.data) return;
  const ja = displayLang === 'ja';
  const { data, params, label } = tabData;

  const flatResults = [];
  (data.allResults || []).forEach(vesselOutput => {
    const vesselInfo = vesselOutput.parameters && vesselOutput.parameters.vessel;
    (vesselOutput.results || []).forEach(res => {
      const vi = res.vessel || vesselInfo;
      flatResults.push({
        ...res,
        _vesselInfo: vi || null,
        _vesselNameJa: vi ? vi.nameJa : (vesselOutput.parameters.color || res._color || '?'),
        _vesselNameEn: vi ? vi.nameEn : (vesselOutput.parameters.color || res._color || '?'),
      });
    });
  });
  flatResults.sort((a, b) => {
    const cmp = (b.requiredMet === a.requiredMet) ? 0 : (b.requiredMet ? 1 : -1);
    if (cmp !== 0) return cmp;
    const scoreCmp = b.score - a.score;
    if (scoreCmp !== 0) return scoreCmp;
    return (b.subScore || 0) - (a.subScore || 0);
  });

  const metaItems = [];
  if (loadedFileName) metaItems.push(`${ja ? 'ファイル' : 'File'}: ${loadedFileName}`);
  metaItems.push(`${ja ? '件数' : 'Results'}: ${flatResults.length}`);
  if (params.character) metaItems.push(`${ja ? 'キャラクター' : 'Character'}: ${params.character}`);

  let bodyHTML = '';

  bodyHTML += `<div class="opt-conditions-summary">`;
  bodyHTML += `<div class="opt-conditions-title">${ja ? '検索条件' : 'Search Conditions'}</div>`;
  bodyHTML += `<div class="opt-conditions-row"><span class="opt-conditions-label">${ja ? 'キャラクター' : 'Character'}:</span><span class="opt-conditions-value">${params.character || '-'}</span></div>`;
  if (params.vessel) {
    const vesselKeys = params.vessel.split(',');
    const vesselNames = vesselKeys.map(vk => {
      if (vesselsData) {
        const vt = (vesselsData.vesselTypes || []).find(v => v.key === vk);
        if (vt) return ja ? vt.nameJa : vt.nameEn;
        const uv = (vesselsData.universalVessels || []).find(v => v.key === vk);
        if (uv) return ja ? uv.nameJa : uv.nameEn;
      }
      return vk;
    });
    bodyHTML += `<div class="opt-conditions-row"><span class="opt-conditions-label">${ja ? '献器' : 'Vessels'}:</span><span class="opt-conditions-value">${vesselNames.join(', ')}</span></div>`;
  }
  bodyHTML += `<div class="opt-conditions-row"><span class="opt-conditions-label">${ja ? 'モード' : 'Mode'}:</span><span class="opt-conditions-value">${params.combined ? (ja ? '通常+深層' : 'Combined') : (ja ? '通常のみ' : 'Normal only')}</span></div>`;
  if (params.effects && params.effects.length > 0) {
    bodyHTML += `<div class="opt-conditions-row"><span class="opt-conditions-label">${ja ? '効果' : 'Effects'}:</span><div class="opt-conditions-effects">`;
    params.effects.forEach(e => {
      const eff = allUniqueEffects.find(u => u.key === e.key);
      const name = eff ? (ja ? eff.name_ja : eff.name_en) : e.key;
      const displayPriority = e.exclude ? `exclude_${e.priority}` : e.priority;
      const pLabel = PRIORITY_LABELS[displayPriority]
        ? (ja ? PRIORITY_LABELS[displayPriority].ja : PRIORITY_LABELS[displayPriority].en) : displayPriority;
      bodyHTML += `<span class="opt-conditions-effect-tag ${displayPriority}">${name} <small>(${pLabel})</small></span>`;
    });
    bodyHTML += `</div></div>`;
  }
  bodyHTML += `</div>`;

  const bestResult = data.bestResult;
  const bestKey = bestResult && bestResult.parameters && bestResult.parameters.vessel
    ? bestResult.parameters.vessel.key : null;
  const bestScore = bestResult ? bestResult.result.score : -1;

  flatResults.forEach((res, idx) => {
    const isBest = bestKey && res._vesselInfo && res._vesselInfo.key === bestKey
      && res.score === bestScore && res.rank === 1;
    bodyHTML += renderResultCard(res, ja, isBest, params, idx);

    bodyHTML += `<div style="margin: 0 0 12px 0; padding: 12px 16px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0 0 6px 6px; border-top: none;">`;

    if (res.normalRelics && res.normalRelics.length > 0) {
      bodyHTML += `<div class="detail-section"><h3>${ja ? '通常遺物' : 'Normal Relics'}</h3>`;
      res.normalRelics.forEach(r => { bodyHTML += renderOptDetailRelic(r, ja); });
      bodyHTML += `</div>`;
    }
    if (res.deepRelics && res.deepRelics.length > 0) {
      bodyHTML += `<div class="detail-section"><h3>${ja ? '深層遺物' : 'Deep Relics'}</h3>`;
      res.deepRelics.forEach(r => { bodyHTML += renderOptDetailRelic(r, ja); });
      bodyHTML += `</div>`;
    }
    if (res.relics && !res.normalRelics) {
      bodyHTML += `<div class="detail-section"><h3>${ja ? '遺物' : 'Relics'}</h3>`;
      res.relics.forEach(r => { bodyHTML += renderOptDetailRelic(r, ja); });
      bodyHTML += `</div>`;
    }

    const bd = computeScoreBreakdown(res, params);
    bodyHTML += `<div class="detail-section"><h3>${ja ? 'スコア内訳' : 'Score Breakdown'}</h3>`;
    for (const ef of bd.effects) {
      const eff = allUniqueEffects.find(e => e.key === ef.key);
      const name = eff ? (ja ? eff.name_ja : eff.name_en) : ef.key;
      const pLabel = PRIORITY_LABELS[ef.priority]
        ? (ja ? PRIORITY_LABELS[ef.priority].ja : PRIORITY_LABELS[ef.priority].en) : ef.priority;
      const stackLabel = ef.stackable === true ? (ja ? '重複:○' : 'Stack:Y')
        : ef.stackable === 'conditional' ? (ja ? '重複:△' : 'Stack:C')
        : (ja ? '重複:×' : 'Stack:N');
      const countInfo = ef.count > 1 ? ` ×${ef.count}` : '';
      bodyHTML += `<div class="detail-score-row">`;
      bodyHTML += `<div class="detail-effect-main">${name}</div>`;
      bodyHTML += `<div class="detail-effect-meta">${pLabel}${countInfo} ${stackLabel}</div>`;
      bodyHTML += `<div class="detail-effect-score" style="color:#80d080">+${ef.contribution}</div>`;
      bodyHTML += `</div>`;
    }
    (res.missingRequired || []).forEach(key => {
      const eff = allUniqueEffects.find(e => e.key === key);
      const name = eff ? (ja ? eff.name_ja : eff.name_en) : key;
      bodyHTML += `<div class="detail-score-row" style="opacity:0.5">`;
      bodyHTML += `<div class="detail-effect-main" style="color:#e07070">${name}</div>`;
      bodyHTML += `<div class="detail-effect-meta">${ja ? '未達' : 'Missing'}</div>`;
      bodyHTML += `<div class="detail-effect-score"></div></div>`;
    });
    if (bd.concentrationBonus > 0) {
      bodyHTML += `<div class="detail-score-row summary">`;
      bodyHTML += `<div class="detail-effect-main">${ja ? '集中ボーナス' : 'Concentration Bonus'}</div>`;
      bodyHTML += `<div class="detail-effect-meta"></div>`;
      bodyHTML += `<div class="detail-effect-score" style="color:#80d080">+${bd.concentrationBonus}</div></div>`;
      for (const cd of bd.concentrationDetails) {
        const relicName = ja ? cd.itemNameJa : cd.itemNameEn;
        const effNames = cd.matchedNames.map(k => {
          const e = allUniqueEffects.find(u => u.key === k);
          return e ? (ja ? e.name_ja : e.name_en) : k;
        }).join(', ');
        bodyHTML += `<div class="detail-score-row" style="padding-left:20px;opacity:0.7">`;
        bodyHTML += `<div class="detail-effect-main" style="font-size:11px">${relicName} (${effNames})</div>`;
        bodyHTML += `<div class="detail-effect-meta">×${cd.matchedCount}</div>`;
        bodyHTML += `<div class="detail-effect-score" style="color:#80d080;font-size:11px">+${cd.bonus}</div></div>`;
      }
    }
    for (const ef of bd.excludeEffects) {
      const eff = allUniqueEffects.find(e => e.key === ef.key);
      const name = eff ? (ja ? eff.name_ja : eff.name_en) : ef.key;
      const displayPriority = `exclude_${ef.priority}`;
      const pLabel = PRIORITY_LABELS[displayPriority]
        ? (ja ? PRIORITY_LABELS[displayPriority].ja : PRIORITY_LABELS[displayPriority].en) : displayPriority;
      const countInfo = ef.count > 1 ? ` ×${ef.count}` : '';
      bodyHTML += `<div class="detail-score-row">`;
      bodyHTML += `<div class="detail-effect-main" style="color:#e07070;text-decoration:line-through">${name}</div>`;
      bodyHTML += `<div class="detail-effect-meta">${pLabel}${countInfo}</div>`;
      bodyHTML += `<div class="detail-effect-score" style="color:#e07070">-${ef.contribution}</div></div>`;
    }
    bodyHTML += `<div class="detail-score-row total">`;
    bodyHTML += `<div class="detail-effect-main">${ja ? '合計' : 'Total'}</div>`;
    bodyHTML += `<div class="detail-effect-meta"></div>`;
    bodyHTML += `<div class="detail-effect-score">${bd.total}</div></div>`;
    bodyHTML += `</div>`;

    bodyHTML += `</div>`;
  });

  if (flatResults.length === 0) {
    bodyHTML += `<p style="color:var(--text-muted)">${ja ? '結果なし' : 'No results'}</p>`;
  }

  const title = ja ? `ビルド探索結果 — ${label}` : `Build Results — ${label}`;
  const fullHTML = buildExportHTML(title, bodyHTML, metaItems);
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  downloadHTML(`relicforge_optimizer_${ts}.html`, fullHTML);
}

// ============================================================
// === Language UI updates for new elements ===
// ============================================================

const _origUpdateLangUI = updateLangUI;
updateLangUI = function() {
  _origUpdateLangUI();
  const ja = displayLang === 'ja';

  // Tab bar
  const mainTabLabel = document.getElementById('main-tab-label');
  if (mainTabLabel) mainTabLabel.textContent = ja ? '遺物一覧' : 'Relic List';

  // Optimizer button
  updateOptimizerButton();

  // Export button
  btnExportTableLabel.textContent = ja ? 'エクスポート' : 'Export';

  // Optimizer inspector labels
  document.getElementById('optimizer-title').textContent = ja ? 'ビルド探索' : 'Build Search';
  document.getElementById('opt-character-label').textContent = ja ? 'キャラクター' : 'Character';
  document.getElementById('opt-vessel-label').textContent = ja ? '献器' : 'Vessel';
  document.getElementById('opt-mode-label').textContent = ja ? 'モード' : 'Mode';
  const modeSelect = document.getElementById('opt-mode');
  modeSelect.options[0].textContent = ja ? '通常+深層' : 'Normal+Deep';
  modeSelect.options[1].textContent = ja ? '通常のみ' : 'Normal Only';
  document.getElementById('opt-effects-label').textContent = ja ? '効果指定' : 'Effect Specs';
  document.getElementById('opt-add-effect-label').textContent = ja ? '効果を追加' : 'Add Effect';
  // Effect selection inspector labels
  document.getElementById('effect-select-title').textContent = ja ? '効果を選択' : 'Select Effects';
  effectSelectSearch.placeholder = ja ? '効果名で絞り込み...' : 'Filter effects...';
  document.getElementById('effect-select-clear-label').textContent = ja ? 'クリア' : 'Clear';
  document.getElementById('effect-select-apply-label').textContent = ja ? '適用' : 'Apply';
  document.getElementById('opt-settings-label').textContent = ja ? '設定' : 'Settings';
  document.getElementById('opt-candidates-label').textContent = ja ? '上位抽出数/色' : 'Top per Color';
  document.getElementById('opt-top-label').textContent = ja ? '出力件数' : 'Result Count';
  document.getElementById('optimizer-clear-label').textContent = ja ? 'クリア' : 'Clear';
  document.getElementById('optimizer-run-label').textContent = ja ? '実行' : 'Run';
  document.getElementById('opt-preset-label').textContent = ja ? '検索条件プリセット:' : 'Search Preset:';
  document.getElementById('opt-preset-save').title = ja ? '検索条件プリセット保存' : 'Save Search Preset';
  document.getElementById('opt-preset-save-label').textContent = ja ? '保存' : 'Save';
  document.getElementById('opt-preset-load').title = ja ? '検索条件プリセット読込' : 'Load Search Preset';
  document.getElementById('opt-preset-load-label').textContent = ja ? '読込' : 'Load';

  // Re-render character/vessel if open
  if (optimizerInspector.classList.contains('open')) {
    renderOptimizerCharacterSelect();
    renderOptimizerVesselList();
    renderOptEffectsTags();
  }
  if (effectSelectInspector.classList.contains('open')) {
    renderEffectSelectList();
  }

  updateOptEffectsCount();

  // Re-render active optimizer tab
  if (activeTab !== 'main' && optimizerTabs.has(activeTab)) {
    const info = optimizerTabs.get(activeTab);
    renderOptimizerResults(activeTab, info.data, info.params);
  }
};
