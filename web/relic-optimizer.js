/**
 * Relic Combination Optimizer - JavaScript Version (Web Worker)
 * Port of src/relic_optimizer.py
 *
 * Usage: As a Web Worker, receives messages with optimization parameters
 * and posts back results and progress updates.
 */

// === Priority Weights ===
const PRIORITY_WEIGHTS = {
  required: 100,
  preferred: 10,
  nice_to_have: 1,
};

const CONCENTRATION_BONUS = 5;

// === Character Name Mapping ===
const CHARACTER_NAMES = {
  '追跡者': 'Wylder',
  '守護者': 'Guardian',
  '鉄の目': 'Iron Eye',
  'レディ': 'Duchess',
  '無頼漢': 'Raider',
  '復讐者': 'Revenant',
  '隠者': 'Recluse',
  '執行者': 'Executor',
  '学者': 'Scholar',
  '葬儀屋': 'Undertaker',
};

const CHARACTER_NAMES_REV = {};
for (const [ja, en] of Object.entries(CHARACTER_NAMES)) {
  CHARACTER_NAMES_REV[en.toLowerCase()] = ja;
}

function resolveCharacterNameJa(name) {
  if (name.startsWith('\u3010') && name.endsWith('\u3011')) {
    return name.slice(1, -1);
  }
  if (CHARACTER_NAMES[name]) return name;
  const lower = name.toLowerCase();
  if (CHARACTER_NAMES_REV[lower]) return CHARACTER_NAMES_REV[lower];
  return name;
}

// === MinHeap (heapq equivalent) ===
class MinHeap {
  constructor() { this._data = []; }
  get size() { return this._data.length; }
  peek() { return this._data[0]; }

  push(item) {
    this._data.push(item);
    this._siftUp(this._data.length - 1);
  }

  pop() {
    const top = this._data[0];
    const last = this._data.pop();
    if (this._data.length > 0) {
      this._data[0] = last;
      this._siftDown(0);
    }
    return top;
  }

  replace(item) {
    const top = this._data[0];
    this._data[0] = item;
    this._siftDown(0);
    return top;
  }

  _siftUp(i) {
    const d = this._data;
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (this._compare(d[i], d[parent]) < 0) {
        [d[i], d[parent]] = [d[parent], d[i]];
        i = parent;
      } else break;
    }
  }

  _siftDown(i) {
    const d = this._data;
    const n = d.length;
    while (true) {
      let smallest = i;
      const left = 2 * i + 1;
      const right = 2 * i + 2;
      if (left < n && this._compare(d[left], d[smallest]) < 0) smallest = left;
      if (right < n && this._compare(d[right], d[smallest]) < 0) smallest = right;
      if (smallest !== i) {
        [d[i], d[smallest]] = [d[smallest], d[i]];
        i = smallest;
      } else break;
    }
  }

  // Compare tuples: [reqMetInt, negScore, negSubScore, counter]
  _compare(a, b) {
    if (a[0] !== b[0]) return a[0] - b[0];
    if (a[1] !== b[1]) return a[1] - b[1];
    if (a[2] !== b[2]) return a[2] - b[2];
    return a[3] - b[3];
  }
}

// === Stacking Data Loader ===
function loadStackingData(effectsData) {
  const keyStackable = {};
  for (const [eid, entry] of Object.entries(effectsData.effects || {})) {
    const key = entry.key;
    const stackable = entry.stackable !== undefined ? entry.stackable : false;
    if (!(key in keyStackable)) {
      keyStackable[key] = stackable === true ? true : stackable === 'conditional' ? 'conditional' : false;
    } else if (stackable === true) {
      keyStackable[key] = true;
    } else if (stackable === 'conditional' && keyStackable[key] === false) {
      keyStackable[key] = 'conditional';
    }
  }
  return keyStackable;
}

// === RelicOptimizer ===
class RelicOptimizer {
  constructor(relics, effectSpecs, vesselsData, stackingData) {
    this.allRelics = relics;
    this.effectSpecs = effectSpecs;
    this.vesselsData = vesselsData;
    this.stackingData = stackingData || {};

    // Caches
    this._effectKeysCache = {};
    this._specKeysCache = {};
    this._scoreCache = {};
    this._excludeKeysCache = {};

    // Separate include and exclude specs
    const includeSpecs = effectSpecs.filter(s => !s.exclude);
    const excludeSpecs = effectSpecs.filter(s => s.exclude);

    // Build include effect lookup
    this.effectLookup = {};
    for (const spec of includeSpecs) {
      const key = spec.key;
      const weight = PRIORITY_WEIGHTS[spec.priority] || 1;
      if (key) {
        this.effectLookup[key] = { priority: spec.priority, weight, spec };
      }
      if (spec.name_ja || spec.name_en) {
        this._resolveNameMatches(spec.name_ja, spec.name_en, spec, weight, this.effectLookup);
      }
    }

    // Build exclude effect lookup
    this.excludeLookup = {};
    for (const spec of excludeSpecs) {
      const key = spec.key;
      const weight = PRIORITY_WEIGHTS[spec.priority] || 1;
      if (key) {
        this.excludeLookup[key] = { priority: spec.priority, weight, spec };
      }
      if (spec.name_ja || spec.name_en) {
        this._resolveNameMatches(spec.name_ja, spec.name_en, spec, weight, this.excludeLookup);
      }
    }

    // Integer-indexed arrays for fast scoring
    this._specKeyList = Object.keys(this.effectLookup).sort();
    this._specKeyToIdx = {};
    for (let i = 0; i < this._specKeyList.length; i++) {
      this._specKeyToIdx[this._specKeyList[i]] = i;
    }
    this._nSpec = this._specKeyList.length;
    this._specWeights = this._specKeyList.map(k => this.effectLookup[k].weight);
    this._specStacking = this._specKeyList.map(k => this.stackingData[k] !== undefined ? this.stackingData[k] : false);
    this._requiredIdxSet = new Set();
    for (let i = 0; i < this._specKeyList.length; i++) {
      if (this.effectLookup[this._specKeyList[i]].priority === 'required') {
        this._requiredIdxSet.add(i);
      }
    }

    // Sub-priority rank values (for tiebreaker scoring)
    const priorityGroups = {};
    for (const spec of includeSpecs) {
      const key = spec.key;
      if (key && key in this._specKeyToIdx) {
        const idx = this._specKeyToIdx[key];
        const p = spec.priority || 'nice_to_have';
        if (!priorityGroups[p]) priorityGroups[p] = [];
        priorityGroups[p].push([idx, spec.rank || 0]);
      }
    }
    this._specSubRankValues = new Array(this._nSpec).fill(0);
    for (const [priority, entries] of Object.entries(priorityGroups)) {
      const groupSize = entries.length;
      const pw = PRIORITY_WEIGHTS[priority] || 1;
      for (const [idx, rank] of entries) {
        this._specSubRankValues[idx] = (groupSize - 1 - rank) * pw;
      }
    }

    // Exclude keys indexed
    this._exclKeyList = Object.keys(this.excludeLookup).sort();
    this._exclKeyToIdx = {};
    for (let i = 0; i < this._exclKeyList.length; i++) {
      this._exclKeyToIdx[this._exclKeyList[i]] = i;
    }
    this._nExcl = this._exclKeyList.length;
    this._exclWeights = this._exclKeyList.map(k => this.excludeLookup[k].weight);
    this._exclIsRequired = this._exclKeyList.map(k => this.excludeLookup[k].priority === 'required');

    // Relic by id lookup
    this._relicById = {};
    for (const r of relics) {
      this._relicById[r.id] = r;
    }

    // Phase cache for cross-vessel reuse
    this._phaseCache = {};
  }

  _resolveNameMatches(nameJa, nameEn, spec, weight, targetLookup) {
    for (const relic of this.allRelics) {
      for (const group of relic.effects) {
        for (const eff of group) {
          let matched = false;
          if (nameJa && (eff.name_ja || '').includes(nameJa)) matched = true;
          if (nameEn && (eff.name_en || '').toLowerCase().includes(nameEn.toLowerCase())) matched = true;
          if (matched && !(eff.key in targetLookup)) {
            targetLookup[eff.key] = { priority: spec.priority, weight, spec };
          }
        }
      }
    }
  }

  filterRelics(types, character, color) {
    let filtered = this.allRelics;
    if (types) {
      const typeSet = new Set(types);
      filtered = filtered.filter(r => typeSet.has(r.itemType));
    }
    if (color) {
      filtered = filtered.filter(r => r.itemColor === color);
    }
    if (character) {
      const charJa = resolveCharacterNameJa(character);
      filtered = filtered.filter(r => {
        for (const group of r.effects) {
          const mainEff = group[0];
          const name = mainEff.name_ja || '';
          const m = name.match(/^【(.+?)】/);
          if (m && m[1] !== charJa) return false;
        }
        return true;
      });
    }
    return filtered;
  }

  getRelicEffectKeys(relic) {
    const rid = relic.id;
    if (this._effectKeysCache[rid]) return this._effectKeysCache[rid];
    const keys = new Set();
    for (const group of relic.effects) {
      if (group.length > 0) keys.add(group[0].key);
    }
    this._effectKeysCache[rid] = keys;
    return keys;
  }

  _getSpecKeys(relic) {
    const rid = relic.id;
    if (this._specKeysCache[rid]) return this._specKeysCache[rid];
    const keys = [];
    for (const group of relic.effects) {
      if (group.length > 0) {
        const k = group[0].key;
        if (k in this.effectLookup) keys.push(k);
      }
    }
    this._specKeysCache[rid] = keys;
    return keys;
  }

  _getExcludeKeys(relic) {
    const rid = relic.id;
    if (this._excludeKeysCache[rid]) return this._excludeKeysCache[rid];
    const keys = [];
    for (const group of relic.effects) {
      for (const e of group) {
        const k = e.key;
        if (k in this.excludeLookup) keys.push(k);
      }
    }
    this._excludeKeysCache[rid] = keys;
    return keys;
  }

  scoreRelic(relic) {
    const rid = relic.id;
    if (this._scoreCache[rid] !== undefined) return this._scoreCache[rid];
    let score = 0;
    const specKeys = this._getSpecKeys(relic);
    for (const key of specKeys) {
      score += this.effectLookup[key].weight;
    }
    const n = specKeys.length;
    if (n >= 2) score += CONCENTRATION_BONUS * n * (n - 1) / 2;
    for (const key of this._getExcludeKeys(relic)) {
      score -= this.excludeLookup[key].weight;
    }
    this._scoreCache[rid] = score;
    return score;
  }

  _fastStackingScore(counts) {
    let score = 0;
    const weights = this._specWeights;
    const stacking = this._specStacking;
    for (let i = 0; i < this._nSpec; i++) {
      const c = counts[i];
      if (c === 0) continue;
      const w = weights[i];
      const s = stacking[i];
      if (s === true) {
        score += w * c;
      } else if (s === 'conditional') {
        score += w;
        if (c > 1) score -= Math.trunc(w * 0.3 * (c - 1));
      } else {
        score += w;
        if (c > 1) score -= Math.trunc(w * 0.5 * (c - 1));
      }
    }
    return score;
  }

  _fastSubScore(counts) {
    let sub = 0;
    const subRanks = this._specSubRankValues;
    for (let i = 0; i < this._nSpec; i++) {
      if (counts[i] > 0) sub += subRanks[i];
    }
    return sub;
  }

  _compactRelic(relic) {
    const rid = relic.id;
    const specKeys = this._getSpecKeys(relic);
    const specIndices = specKeys.map(k => this._specKeyToIdx[k]);

    const exclKeys = this._getExcludeKeys(relic);
    let exclPenalty = 0;
    let hasExclReq = false;
    for (const k of exclKeys) {
      const idx = this._exclKeyToIdx[k];
      exclPenalty += this._exclWeights[idx];
      if (this._exclIsRequired[idx]) hasExclReq = true;
    }

    const nSk = specIndices.length;
    const concBonus = nSk >= 2 ? Math.trunc(CONCENTRATION_BONUS * nSk * (nSk - 1) / 2) : 0;

    return [rid, specIndices, exclPenalty, hasExclReq, concBonus];
  }

  _enumerateCombos(compactCands, slotColors) {
    const nSpec = this._nSpec;
    const nSlots = slotColors.length;
    const hasAny = slotColors.includes('Any');
    const colorsNoAny = slotColors.filter(c => c !== 'Any');
    const uniqueColors = new Set(colorsNoAny);

    if (nSlots === 3 && !hasAny && uniqueColors.size === 1) {
      return this._enumAllSame(compactCands[0], nSpec);
    } else if (nSlots === 3 && !hasAny && uniqueColors.size === 3) {
      return this._enumAllDiff(compactCands, nSpec);
    } else if (nSlots === 3 && !hasAny && uniqueColors.size === 2) {
      return this._enumTwoSame(compactCands, slotColors, nSpec);
    } else {
      return this._enumGeneral(compactCands, nSpec);
    }
  }

  _enumAllSame(cands, nSpec) {
    const results = [];
    const n = cands.length;
    for (let i = 0; i < n; i++) {
      const [riId, riSi, riEp, riHer, riCb] = cands[i];
      for (let j = i + 1; j < n; j++) {
        const [rjId, rjSi, rjEp, rjHer, rjCb] = cands[j];
        for (let k = j + 1; k < n; k++) {
          const [rkId, rkSi, rkEp, rkHer, rkCb] = cands[k];
          const counts = new Array(nSpec).fill(0);
          for (const idx of riSi) counts[idx]++;
          for (const idx of rjSi) counts[idx]++;
          for (const idx of rkSi) counts[idx]++;
          let score = this._fastStackingScore(counts);
          score += riCb + rjCb + rkCb;
          score -= riEp + rjEp + rkEp;
          const her = riHer || rjHer || rkHer;
          const subScore = this._fastSubScore(counts);
          results.push([score, counts, riCb + rjCb + rkCb, riEp + rjEp + rkEp, her, [riId, rjId, rkId], subScore]);
        }
      }
    }
    return results;
  }

  _enumAllDiff(compactCands, nSpec) {
    const results = [];
    const [c0, c1, c2] = compactCands;
    for (const [riId, riSi, riEp, riHer, riCb] of c0) {
      for (const [rjId, rjSi, rjEp, rjHer, rjCb] of c1) {
        for (const [rkId, rkSi, rkEp, rkHer, rkCb] of c2) {
          const counts = new Array(nSpec).fill(0);
          for (const idx of riSi) counts[idx]++;
          for (const idx of rjSi) counts[idx]++;
          for (const idx of rkSi) counts[idx]++;
          let score = this._fastStackingScore(counts);
          score += riCb + rjCb + rkCb;
          score -= riEp + rjEp + rkEp;
          const her = riHer || rjHer || rkHer;
          const subScore = this._fastSubScore(counts);
          results.push([score, counts, riCb + rjCb + rkCb, riEp + rjEp + rkEp, her, [riId, rjId, rkId], subScore]);
        }
      }
    }
    return results;
  }

  _enumTwoSame(compactCands, slotColors, nSpec) {
    const results = [];
    // Count colors
    const colorCounts = {};
    for (const c of slotColors) colorCounts[c] = (colorCounts[c] || 0) + 1;
    let sameColor = null;
    let maxCount = 0;
    for (const [c, cnt] of Object.entries(colorCounts)) {
      if (cnt > maxCount) { maxCount = cnt; sameColor = c; }
    }
    const sameIdx = [];
    let diffIdx = 0;
    for (let i = 0; i < slotColors.length; i++) {
      if (slotColors[i] === sameColor) sameIdx.push(i);
      else diffIdx = i;
    }

    const sameCands = compactCands[sameIdx[0]];
    const diffCands = compactCands[diffIdx];
    const nSame = sameCands.length;

    for (let i = 0; i < nSame; i++) {
      const [riId, riSi, riEp, riHer, riCb] = sameCands[i];
      for (let j = i + 1; j < nSame; j++) {
        const [rjId, rjSi, rjEp, rjHer, rjCb] = sameCands[j];
        for (const [rkId, rkSi, rkEp, rkHer, rkCb] of diffCands) {
          if (rkId === riId || rkId === rjId) continue;
          const counts = new Array(nSpec).fill(0);
          for (const idx of riSi) counts[idx]++;
          for (const idx of rjSi) counts[idx]++;
          for (const idx of rkSi) counts[idx]++;
          let score = this._fastStackingScore(counts);
          score += riCb + rjCb + rkCb;
          score -= riEp + rjEp + rkEp;
          const her = riHer || rjHer || rkHer;
          const subScore = this._fastSubScore(counts);
          results.push([score, counts, riCb + rjCb + rkCb, riEp + rjEp + rkEp, her, [riId, rjId, rkId], subScore]);
        }
      }
    }
    return results;
  }

  _enumGeneral(compactCands, nSpec) {
    const results = [];
    const seen = new Set();

    const recurse = (slotIdx, chosenIds, partialSi, partialEp, partialHer, partialCb) => {
      if (slotIdx === compactCands.length) {
        const canon = [...chosenIds].sort((a, b) => a - b).join(',');
        if (seen.has(canon)) return;
        seen.add(canon);
        const counts = new Array(nSpec).fill(0);
        for (const siList of partialSi) {
          for (const idx of siList) counts[idx]++;
        }
        let score = this._fastStackingScore(counts);
        score += partialCb - partialEp;
        const subScore = this._fastSubScore(counts);
        results.push([score, counts, partialCb, partialEp, partialHer, [...chosenIds], subScore]);
        return;
      }

      for (const [rid, si, ep, her, cb] of compactCands[slotIdx]) {
        if (chosenIds.includes(rid)) continue;
        recurse(
          slotIdx + 1,
          [...chosenIds, rid],
          [...partialSi, si],
          partialEp + ep,
          partialHer || her,
          partialCb + cb
        );
      }
    };

    recurse(0, [], [], 0, false, 0);
    return results;
  }

  getVesselConfigs(character, vesselTypes) {
    if (!this.vesselsData) return [];

    const charJa = resolveCharacterNameJa(character);
    const charData = (this.vesselsData.characters || {})[charJa];
    if (!charData) return [];

    const vesselTypeInfo = {};
    for (const vt of (this.vesselsData.vesselTypes || [])) {
      vesselTypeInfo[vt.key] = vt;
    }

    const configs = [];
    for (const [vkey, vdata] of Object.entries(charData.vessels || {})) {
      if (vesselTypes && !vesselTypes.includes(vkey)) continue;
      const vtInfo = vesselTypeInfo[vkey] || {};
      configs.push({
        key: vkey,
        nameJa: `${charJa}の${vtInfo.nameJa || vkey}`,
        nameEn: `${charData.nameEn || charJa}'s ${vtInfo.nameEn || vkey}`,
        normalSlots: vdata.normalSlots || [],
        deepSlots: vdata.deepSlots || [],
      });
    }

    // Universal vessels
    if (!vesselTypes) {
      for (const uv of (this.vesselsData.universalVessels || [])) {
        configs.push({
          key: uv.key,
          nameJa: uv.nameJa,
          nameEn: uv.nameEn,
          normalSlots: uv.normalSlots || [],
          deepSlots: uv.deepSlots || [],
          universal: true,
        });
      }
    }

    return configs;
  }

  _buildSlotCandidates(slotColors, filtered, candidatesPerSlot) {
    const byColor = {};
    for (const r of filtered) {
      const c = r.itemColor || '';
      if (!byColor[c]) byColor[c] = [];
      byColor[c].push(r);
    }

    const wantedIds = new Set();
    for (const r of filtered) {
      if (this._getSpecKeys(r).length > 0) wantedIds.add(r.id);
    }

    const slotCandidates = [];
    for (const slotColor of slotColors) {
      const candidates = slotColor === 'Any' ? filtered : (byColor[slotColor] || []);

      const mustInclude = candidates.filter(r => wantedIds.has(r.id));
      const mustIds = new Set(mustInclude.map(r => r.id));

      const others = candidates.filter(r => !mustIds.has(r.id))
        .map(r => [this.scoreRelic(r), r])
        .sort((a, b) => b[0] - a[0]);

      const remaining = candidatesPerSlot - mustInclude.length;
      const topOthers = remaining > 0 ? others.slice(0, remaining).map(x => x[1]) : [];

      const combined = [...mustInclude, ...topOthers];
      combined.sort((a, b) => this.scoreRelic(b) - this.scoreRelic(a));
      slotCandidates.push(combined);
    }

    return slotCandidates;
  }

  optimizeCombined(normalSlotColors, deepSlotColors, opts = {}) {
    const {
      normalTypes = ['Relic', 'UniqueRelic'],
      deepTypes = ['DeepRelic'],
      character = null,
      candidatesPerSlot = 15,
      topN = 10,
    } = opts;

    const normalFiltered = this.filterRelics(normalTypes, character);
    const deepFiltered = this.filterRelics(deepTypes, character);

    const normalCands = this._buildSlotCandidates(normalSlotColors, normalFiltered, candidatesPerSlot);
    const deepCands = this._buildSlotCandidates(deepSlotColors, deepFiltered, candidatesPerSlot);

    // Phase 1: Enumerate normal combos
    const nCacheKey = [...normalSlotColors].sort().join(',');
    let normalCombos;
    if (this._phaseCache[nCacheKey]) {
      normalCombos = this._phaseCache[nCacheKey];
    } else if (normalCands.every(sc => sc.length > 0)) {
      const compactN = normalCands.map(sc => sc.map(r => this._compactRelic(r)));
      normalCombos = this._enumerateCombos(compactN, normalSlotColors);
      this._phaseCache[nCacheKey] = normalCombos;
    } else {
      normalCombos = [];
    }

    // Phase 2: Enumerate deep combos
    const dCacheKey = 'deep,' + [...deepSlotColors].sort().join(',');
    let deepCombos;
    if (this._phaseCache[dCacheKey]) {
      deepCombos = this._phaseCache[dCacheKey];
    } else if (deepCands.every(sc => sc.length > 0)) {
      const compactD = deepCands.map(sc => sc.map(r => this._compactRelic(r)));
      deepCombos = this._enumerateCombos(compactD, deepSlotColors);
      this._phaseCache[dCacheKey] = deepCombos;
    } else {
      deepCombos = [];
    }

    if (!normalCombos.length && !deepCombos.length) return [];

    // Sort each side by score descending
    normalCombos.sort((a, b) => b[0] - a[0]);
    deepCombos.sort((a, b) => b[0] - a[0]);

    const nSpec = this._nSpec;
    const specWeights = this._specWeights;
    const specStacking = this._specStacking;
    const requiredIdxSet = this._requiredIdxSet;

    // Handle single-side cases
    if (!normalCombos.length) {
      return this._combosToResultsCompact(deepCombos.slice(0, topN), true);
    }
    if (!deepCombos.length) {
      return this._combosToResultsCompact(normalCombos.slice(0, topN), false);
    }

    // Phase 3: Cross-pair with heap-based top-N and pruning
    const maxPairs = 500;
    const nTop = Math.min(normalCombos.length, maxPairs);
    const dTop = Math.min(deepCombos.length, maxPairs);

    const normalTop = normalCombos.slice(0, nTop);
    const deepTop = deepCombos.slice(0, dTop);
    const bestDeepScore = deepTop[0][0];

    // Fix pruning: check if req_met=True is achievable
    let reqMetBound = true;
    if (requiredIdxSet.size > 0) {
      const possibleFromNormal = new Set();
      for (const [, nCts, , , ,] of normalTop) {
        for (let i = 0; i < nSpec; i++) {
          if (nCts[i] > 0) possibleFromNormal.add(i);
        }
      }
      const possibleFromDeep = new Set();
      for (const [, dCts, , , ,] of deepTop) {
        for (let i = 0; i < nSpec; i++) {
          if (dCts[i] > 0) possibleFromDeep.add(i);
        }
      }
      const possibleAll = new Set([...possibleFromNormal, ...possibleFromDeep]);
      for (const idx of requiredIdxSet) {
        if (!possibleAll.has(idx)) { reqMetBound = false; break; }
      }
    }
    if (reqMetBound) {
      const hasNNoExcl = normalTop.some(x => !x[4]);
      const hasDNoExcl = deepTop.some(x => !x[4]);
      if (!(hasNNoExcl && hasDNoExcl)) reqMetBound = false;
    }
    const boundReqInt = reqMetBound ? -1 : 0;

    // Min-heap for top-N
    const heap = new MinHeap();
    const resultMap = {};
    let counter = 0;

    for (const [ns, nCts, nConc, nEp, nHer, nRids] of normalTop) {
      // Outer pruning
      if (heap.size >= topN) {
        const h = heap.peek();
        if (boundReqInt >= h[0] && -(ns + bestDeepScore) >= h[1]) break;
      }

      for (const [ds, dCts, dConc, dEp, dHer, dRids] of deepTop) {
        // Inner pruning
        if (heap.size >= topN) {
          const h = heap.peek();
          if (boundReqInt >= h[0] && -(ns + ds) >= h[1]) break;
        }

        // Inline merged scoring
        let score = 0;
        let hasAllRequired = true;
        for (let i = 0; i < nSpec; i++) {
          const c = nCts[i] + dCts[i];
          if (c === 0) {
            if (requiredIdxSet.has(i)) hasAllRequired = false;
            continue;
          }
          const w = specWeights[i];
          const s = specStacking[i];
          if (s === true) {
            score += w * c;
          } else if (s === 'conditional') {
            score += w;
            if (c > 1) score -= Math.trunc(w * 0.3 * (c - 1));
          } else {
            score += w;
            if (c > 1) score -= Math.trunc(w * 0.5 * (c - 1));
          }
        }

        score += nConc + dConc - nEp - dEp;
        const hasExclReq = nHer || dHer;
        const reqMet = hasAllRequired && !hasExclReq;

        // Calculate sub_score for tiebreaker
        let subScore = 0;
        const subRankValues = this._specSubRankValues;
        for (let i = 0; i < nSpec; i++) {
          if (nCts[i] + dCts[i] > 0) subScore += subRankValues[i];
        }

        const heapKey = [reqMet ? -1 : 0, -score, -subScore, counter];

        if (heap.size < topN) {
          heap.push(heapKey);
          resultMap[counter] = [reqMet, score, subScore, nCts, dCts, nRids, dRids];
        } else if (this._heapCompare(heapKey, heap.peek()) < 0) {
          const evicted = heap.replace(heapKey);
          delete resultMap[evicted[3]];
          resultMap[counter] = [reqMet, score, subScore, nCts, dCts, nRids, dRids];
        }

        counter++;
      }
    }

    // Build full results
    const results = [];
    while (heap.size > 0) {
      const hk = heap.pop();
      const data = resultMap[hk[3]];
      const [reqMet, score, subScore, nCts, dCts, nRids, dRids] = data;

      const matchedKeys = new Set();
      for (let i = 0; i < nSpec; i++) {
        if (nCts[i] + dCts[i] > 0) matchedKeys.add(this._specKeyList[i]);
      }
      const missing = [];
      for (const i of requiredIdxSet) {
        if (nCts[i] + dCts[i] === 0) missing.push(this._specKeyList[i]);
      }
      missing.sort();

      const excludedPresent = new Set();
      const allRids = [...nRids, ...dRids];
      for (const rid of allRids) {
        for (const k of this._getExcludeKeys(this._relicById[rid])) {
          excludedPresent.add(k);
        }
      }

      const nRelics = nRids.map(rid => this._relicById[rid]);
      const dRelics = dRids.map(rid => this._relicById[rid]);

      results.push({
        required_met: reqMet,
        score,
        sub_score: subScore,
        matched_keys: matchedKeys,
        missing_required: missing,
        excluded_present: excludedPresent,
        relics: [...nRelics, ...dRelics],
        normal_relics: nRelics,
        deep_relics: dRelics,
      });
    }

    results.sort((a, b) => {
      if (a.required_met !== b.required_met) return b.required_met ? 1 : -1;
      const sc = b.score - a.score;
      if (sc !== 0) return sc;
      return (b.sub_score || 0) - (a.sub_score || 0);
    });

    return results;
  }

  _heapCompare(a, b) {
    if (a[0] !== b[0]) return a[0] - b[0];
    if (a[1] !== b[1]) return a[1] - b[1];
    if (a[2] !== b[2]) return a[2] - b[2];
    return a[3] - b[3];
  }

  _combosToResultsCompact(combos, isDeepOnly) {
    const results = [];
    for (const [score, counts, conc, exclPen, hasExclReq, rids, comboSubScore] of combos) {
      const matchedKeys = new Set();
      for (let i = 0; i < this._nSpec; i++) {
        if (counts[i] > 0) matchedKeys.add(this._specKeyList[i]);
      }
      const missing = [];
      for (const i of this._requiredIdxSet) {
        if (counts[i] === 0) missing.push(this._specKeyList[i]);
      }
      missing.sort();

      const excludedPresent = new Set();
      for (const rid of rids) {
        for (const k of this._getExcludeKeys(this._relicById[rid])) {
          excludedPresent.add(k);
        }
      }

      const relics = rids.map(rid => this._relicById[rid]);
      const subScore = comboSubScore !== undefined ? comboSubScore : this._fastSubScore(counts);
      results.push({
        required_met: missing.length === 0 && !hasExclReq,
        score,
        sub_score: subScore,
        matched_keys: matchedKeys,
        missing_required: missing,
        excluded_present: excludedPresent,
        relics: relics,
        normal_relics: isDeepOnly ? [] : relics,
        deep_relics: isDeepOnly ? relics : [],
      });
    }
    return results;
  }

  _formatRelic(relic, matchedKeys, excludedKeys) {
    const effectsOut = [];
    const exclSet = excludedKeys || new Set();
    for (const group of relic.effects) {
      const mainEff = group[0];
      const matched = matchedKeys.has(mainEff.key);
      const excluded = exclSet.has(mainEff.key);
      const effEntry = {
        key: mainEff.key,
        name_ja: mainEff.name_ja || '',
        name_en: mainEff.name_en || '',
        matched,
      };
      if (matched && mainEff.key in this.effectLookup) {
        effEntry.priority = this.effectLookup[mainEff.key].priority;
      }
      if (excluded) {
        effEntry.excluded = true;
        effEntry.excludePriority = this.excludeLookup[mainEff.key].priority;
      }
      effectsOut.push(effEntry);
      for (let si = 1; si < group.length; si++) {
        const subEntry = {
          key: group[si].key,
          name_ja: group[si].name_ja || '',
          name_en: group[si].name_en || '',
          matched: false,
          isDebuff: true,
        };
        if (group[si].key in this.excludeLookup) {
          subEntry.excluded = true;
          subEntry.excludePriority = this.excludeLookup[group[si].key].priority;
        }
        effectsOut.push(subEntry);
      }
    }

    return {
      id: relic.id,
      itemKey: relic.itemKey,
      itemNameJa: relic.itemNameJa || '',
      itemNameEn: relic.itemNameEn || '',
      itemColor: relic.itemColor || '',
      itemType: relic.itemType || '',
      effects: effectsOut,
    };
  }

  formatResults(results, vesselInfo, params) {
    const isCombined = params.combined;
    const formattedResults = [];

    for (let rank = 0; rank < results.length; rank++) {
      const res = results[rank];
      const matchedKeys = res.matched_keys;
      const excludedKeys = res.excluded_present;

      let entry;
      if (isCombined && res.normal_relics) {
        const normalOut = res.normal_relics.map(r => this._formatRelic(r, matchedKeys, excludedKeys));
        const deepOut = res.deep_relics.map(r => this._formatRelic(r, matchedKeys, excludedKeys));
        entry = {
          rank: rank + 1,
          score: res.score,
          subScore: res.sub_score || 0,
          requiredMet: res.required_met,
          normalRelics: normalOut,
          deepRelics: deepOut,
          matchedEffects: [...matchedKeys].sort(),
          missingRequired: res.missing_required,
          excludedPresent: [...excludedKeys].sort(),
        };
      } else {
        const relicsOut = res.relics.map(r => this._formatRelic(r, matchedKeys, excludedKeys));
        entry = {
          rank: rank + 1,
          score: res.score,
          subScore: res.sub_score || 0,
          requiredMet: res.required_met,
          relics: relicsOut,
          matchedEffects: [...matchedKeys].sort(),
          missingRequired: res.missing_required,
          excludedPresent: [...excludedKeys].sort(),
        };
      }

      if (vesselInfo) entry.vessel = vesselInfo;
      formattedResults.push(entry);
    }

    const output = {
      parameters: {
        character: params.character,
        types: params.types || [],
        candidates: params.candidates,
        effects: this.effectSpecs.map(s => ({
          key: s.key || '',
          name_ja: s.name_ja || '',
          name_en: s.name_en || '',
          priority: s.priority,
          exclude: !!s.exclude,
        })),
      },
      results: formattedResults,
    };

    if (vesselInfo) {
      output.parameters.vessel = vesselInfo;
    }

    return output;
  }
}

// === Output Builder ===
function buildOutput(allOutput, topN = 50) {
  const flat = [];
  for (const vesselOutput of allOutput) {
    const params = vesselOutput.parameters || {};
    const vesselInfo = params.vessel;
    for (const res of (vesselOutput.results || [])) {
      const entry = { ...res };
      if (vesselInfo && !entry.vessel) entry.vessel = vesselInfo;
      flat.push(entry);
    }
  }

  flat.sort((a, b) => {
    if (a.requiredMet !== b.requiredMet) return b.requiredMet ? 1 : -1;
    const sc = (b.score || 0) - (a.score || 0);
    if (sc !== 0) return sc;
    return (b.subScore || 0) - (a.subScore || 0);
  });

  const trimmed = flat.slice(0, topN);
  for (let i = 0; i < trimmed.length; i++) {
    trimmed[i].rank = i + 1;
  }

  const output = {};
  if (trimmed.length > 0) {
    output.bestResult = {
      parameters: allOutput[0] ? allOutput[0].parameters : {},
      result: trimmed[0],
    };
    if (trimmed[0].vessel) {
      output.bestResult.parameters = { ...output.bestResult.parameters, vessel: trimmed[0].vessel };
    }
  }

  // Group by vessel
  const grouped = {};
  for (const entry of trimmed) {
    const vessel = entry.vessel;
    const groupKey = vessel ? (vessel.key || '') : '_unknown';
    if (!grouped[groupKey]) {
      let srcParams = {};
      for (const vo of allOutput) {
        const p = vo.parameters || {};
        const v = p.vessel;
        if (vessel && v && v.key === groupKey) { srcParams = p; break; }
      }
      grouped[groupKey] = { parameters: srcParams, results: [] };
    }
    grouped[groupKey].results.push(entry);
  }

  output.allResults = Object.values(grouped);
  return output;
}

// === Web Worker Message Handler ===
if (typeof self !== 'undefined' && typeof self.postMessage === 'function' && typeof window === 'undefined') {
  self.onmessage = function(e) {
    const { relics, effectSpecs, vesselsData, stackingData, params } = e.data;

    try {
      const optimizer = new RelicOptimizer(relics, effectSpecs, vesselsData, stackingData);

      if (params.character && vesselsData) {
        const vesselTypes = params.vessel ? params.vessel.split(',') : null;
        const vesselConfigs = optimizer.getVesselConfigs(params.character, vesselTypes);

        if (vesselConfigs.length === 0) {
          self.postMessage({ error: `No vessel configs found for ${params.character}` });
          return;
        }

        const allOutput = [];
        const totalVessels = vesselConfigs.length;

        for (let vi = 0; vi < totalVessels; vi++) {
          self.postMessage({ progress: { current: vi, total: totalVessels } });
          const vc = vesselConfigs[vi];
          const vesselInfo = {
            key: vc.key,
            nameJa: vc.nameJa,
            nameEn: vc.nameEn,
          };

          if (params.combined) {
            vesselInfo.normalSlots = vc.normalSlots;
            vesselInfo.deepSlots = vc.deepSlots;

            const results = optimizer.optimizeCombined(
              vc.normalSlots, vc.deepSlots,
              { character: params.character, candidatesPerSlot: params.candidates || 30, topN: params.top || 10 }
            );

            const formatted = optimizer.formatResults(results, vesselInfo, {
              character: params.character,
              types: ['Relic', 'DeepRelic'],
              candidates: params.candidates,
              combined: true,
            });
            allOutput.push(formatted);
          } else {
            const results = optimizer.optimizeCombined(
              vc.normalSlots, vc.deepSlots,
              {
                normalTypes: ['Relic', 'UniqueRelic'],
                deepTypes: [],
                character: params.character,
                candidatesPerSlot: params.candidates || 30,
                topN: params.top || 10,
              }
            );

            const formatted = optimizer.formatResults(results, vesselInfo, {
              character: params.character,
              types: ['Relic', 'UniqueRelic'],
              candidates: params.candidates,
              combined: false,
            });
            allOutput.push(formatted);
          }
        }

        self.postMessage({ progress: { current: totalVessels, total: totalVessels } });
        const outputData = buildOutput(allOutput, params.top || 50);
        self.postMessage({ result: outputData });
      } else {
        self.postMessage({ error: 'Character and vessel data are required' });
      }
    } catch (err) {
      self.postMessage({ error: err.message || String(err) });
    }
  };
}
