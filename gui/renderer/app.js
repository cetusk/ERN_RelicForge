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
const AND_GROUP_COLORS = ['#e74c3c', '#3498db', '#2ecc71']; // group indicator colors

// === Type Display Names ===
const TYPE_LABELS = {
  Relic:       { ja: '通常', en: 'Relic' },
  DeepRelic:   { ja: '深層', en: 'Deep' },
  UniqueRelic: { ja: '固有', en: 'Unique' },
};

// === DOM Elements ===
const btnOpen = document.getElementById('btn-open');
const btnOpenWelcome = document.getElementById('btn-open-welcome');
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
const inspectorEffectList = document.getElementById('inspector-effect-list');
const inspectorSelectedCount = document.getElementById('inspector-selected-count');
const inspectorClear = document.getElementById('inspector-clear');
const inspectorApply = document.getElementById('inspector-apply');

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

  showView('loading');

  try {
    relicData = await window.api.parseSaveFile(filePath);
    loadedFileName = filePath.split(/[/\\]/).pop();
    buildSearchTerms();
    buildUniqueEffects();
    andGroups.forEach(g => g.clear());
    updateHeaderInfo();
    toolbar.classList.remove('hidden');
    btnInspector.classList.remove('hidden');
    updateInspectorButton();
    sortColumn = 'sortKey';
    sortDirection = 'desc';
    updateSortIndicators();
    applyFilters();
    showView('content');
  } catch (err) {
    alert(`解析エラー:\n${err}`);
    showView('welcome');
  }
}

// === View Management ===
function showView(name) {
  welcome.classList.toggle('hidden', name !== 'welcome');
  loading.classList.toggle('hidden', name !== 'loading');
  contentArea.classList.toggle('hidden', name !== 'content');
}

// === Language UI ===
function updateLangUI() {
  const ja = displayLang === 'ja';
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
    `${hit} ${hitLabel} / ${total}  (${normalLabel}: ${nR} / ${deepLabel}: ${nD} / ${uniqueLabel}: ${nU})`;
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
    html += `<div class="detail-effect-id">ID: ${main.id} | Key: ${main.key}</div>`;
    for (let i = 1; i < group.length; i++) {
      const d = group[i];
      const debuffName = displayLang === 'ja'
        ? (d.name_ja || d.name_en || '-')
        : (d.name_en || '-');
      html += `<div class="detail-effect-sub">`;
      html += `<div class="detail-effect-debuff-name">${debuffName}</div>`;
      html += `<div class="detail-effect-id">ID: ${d.id} | Key: ${d.key}</div>`;
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
  { id: 'character', ja: 'キャラクター固有', en: 'Character-Specific' },
  { id: 'stats',     ja: '能力値',          en: 'Stats' },
  { id: 'attack',    ja: '攻撃力',          en: 'Attack Power' },
  { id: 'skill',     ja: 'スキル／アーツ',   en: 'Skill / Arts' },
  { id: 'magic',     ja: '魔術／祈祷',      en: 'Sorcery / Incantation' },
  { id: 'cutrate',   ja: 'カット率',        en: 'Damage Negation' },
  { id: 'resist',    ja: '状態異常耐性',     en: 'Status Resistance' },
  { id: 'recovery',  ja: '回復',            en: 'Recovery' },
  { id: 'action',    ja: 'アクション',       en: 'Action' },
  { id: 'start',     ja: '開始ボーナス',     en: 'Start Bonus' },
  { id: 'mapenv',    ja: 'マップ／ルーン',   en: 'Map / Runes' },
  { id: 'team',      ja: 'チームメンバー',   en: 'Team Member' },
  { id: 'night',     ja: '夜の力',          en: 'Night Power' },
  { id: 'demerit',   ja: 'デメリット',       en: 'Demerits' },
  { id: 'other',     ja: 'その他',          en: 'Other' },
];

function classifyEffect(name_ja, name_en, key) {
  const ja = name_ja || '';
  const en = (name_en || '').toLowerCase();
  // Character-specific (【追跡者】etc.)
  if (/【.+?】/.test(ja)) return 'character';
  // Demerits
  if (/低下|減少|悪化|持続減少|喪失/.test(ja) && !/上昇|強化|回復/.test(ja)) return 'demerit';
  if (/被ダメージ時.*蓄積|HP最大未満時.*蓄積|消費増加|被ダメージ増加/.test(ja)) return 'demerit';
  if (/impaired|reduced(?!.*restoration)|loss(?!.*rune)|continuous.*loss/i.test(en) && !/improved|increased|restoration/i.test(en)) return 'demerit';
  // Night Power
  if (/^.+の力$/.test(ja) && !/攻撃力|の力を/.test(ja) || /の悲嘆/.test(ja) || /^power\s*of/i.test(en) || /grief/i.test(en)) return 'night';
  // Start bonus
  if (/出撃時|戦技変更|付加する|見つけやすくなる/.test(ja) || /sortie|starting/i.test(en)) return 'start';
  // Stats
  if (/最大HP|最大FP|最大スタミナ|生命力|精神力|持久力|筋力|技量|知力|信仰|神秘|強靭度/.test(ja)) return 'stats';
  if (/vigor|mind|endurance|strength|dexterity|intelligence|faith|arcane|poise|maximum\s*(hp|fp|stamina)/i.test(en)) return 'stats';
  // Skill / Arts
  if (/スキル|アーツ|クールタイム/.test(ja) || /skill|art\s*gauge|cooldown/i.test(en)) return 'skill';
  // Sorcery / Incantation
  if (/魔術|祈祷|詠唱|ソウル|FP消費/.test(ja) || /sorcery|sorceries|incantation|spell|casting/i.test(en)) return 'magic';
  // Damage Negation
  if (/カット率|ガード性能/.test(ja) || /damage\s*negation|guarding/i.test(en)) return 'cutrate';
  // Status Resistance
  if (/耐性/.test(ja) || /resistance/i.test(en)) return 'resist';
  // Recovery
  if (/回復|リゲイン|聖杯瓶/.test(ja) || /restoration|recovery|restore|flask/i.test(en)) return 'recovery';
  // Attack Power
  if (/攻撃力|致命の一撃強化|通常攻撃の1段目/.test(ja) || /attack\s*power|critical.*damage/i.test(en)) return 'attack';
  // Team member
  if (/味方|周囲で|ヘイト|狙われ/.test(ja) || /allies|nearby|aggro/i.test(en)) return 'team';
  // Map / Runes
  if (/強敵を倒す度|発見力|ルーン|死亡時|埋もれ宝|地図/.test(ja) || /item\s*discovery|rune|death/i.test(en)) return 'mapenv';
  // Action
  if (/ガードカウンター|投擲壺|調香術|咆哮|ブレス|ローリング|回避|二刀|両手持ち|タメ攻撃|連撃|遠距離|武器の持ち替え|刺突|ジャンプ|ガード崩し|崩す力|体勢を崩す|波動ダッシュ|ガード成功|ガード連続|ガード中|致命の一撃|パリィ|歩行中|集団撃破|精密射撃|シールド|体勢が崩れ|竜餐|定期的に|状態になると|スタミナ消費/.test(ja)
    || /guard\s*counter|throwing|perfum|roar|breath|dodge|evasion|two.*hand|dual|charge|ranged|switch.*weapon|thrust|jump|stance.*break|critical.*hit/i.test(en)) return 'action';
  // Broad attack-related
  if (/攻撃/.test(ja) || /attack/i.test(en)) return 'attack';
  return 'other';
}

function buildUniqueEffects() {
  if (!relicData) { allUniqueEffects = []; return; }
  const effectMap = new Map(); // key -> { key, id, name_ja, name_en, count, category }
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

    html += `<div class="inspector-group-header${isCollapsed ? ' collapsed' : ''}" data-cat="${catId}">`;
    html += `<span class="inspector-group-arrow">▼</span>`;
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

  // Attach click handlers for collapsible group headers
  inspectorEffectList.querySelectorAll('.inspector-group-header').forEach(header => {
    header.addEventListener('click', () => {
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
inspectorClose.addEventListener('click', closeInspector);
inspectorBackdrop.addEventListener('click', closeInspector);

inspectorSearch.addEventListener('input', renderInspectorEffects);

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
