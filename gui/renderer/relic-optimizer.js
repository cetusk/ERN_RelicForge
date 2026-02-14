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
    const item = d[i];
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (this._compare(item, d[parent]) < 0) {
        d[i] = d[parent];
        i = parent;
      } else break;
    }
    d[i] = item;
  }

  _siftDown(i) {
    const d = this._data;
    const n = d.length;
    const item = d[i];
    while (true) {
      let smallest = i;
      const left = 2 * i + 1;
      const right = 2 * i + 2;
      if (left < n && this._compare(d[left], d[smallest]) < 0) smallest = left;
      if (right < n && this._compare(d[right], d[smallest]) < 0) smallest = right;
      if (smallest !== i) {
        d[i] = d[smallest];
        i = smallest;
      } else break;
    }
    d[i] = item;
  }

  // Compare tuples: [-score, -subScore, counter]
  _compare(a, b) {
    if (a[0] !== b[0]) return a[0] - b[0];
    if (a[1] !== b[1]) return a[1] - b[1];
    return (a[2] || 0) - (b[2] || 0);
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
    const nSpec = this._specKeyList.length;
    this._nSpec = nSpec;

    // TypedArrays for hot-loop data (cache-friendly, no boxing)
    // Stacking codes: 0=non-stackable, 1=stackable, 2=conditional
    this._specWeights = new Int32Array(nSpec);
    this._specStackingInt = new Int8Array(nSpec);
    this._specPenalty30 = new Int32Array(nSpec); // Math.trunc(w * 0.3) for conditional
    this._specPenalty50 = new Int32Array(nSpec); // Math.trunc(w * 0.5) for non-stackable
    this._isRequired = new Uint8Array(nSpec);    // 1 if required, 0 otherwise
    this._requiredIdxSet = new Set(); // kept for non-hot-path usage

    for (let i = 0; i < nSpec; i++) {
      const k = this._specKeyList[i];
      const w = this.effectLookup[k].weight;
      this._specWeights[i] = w;
      const s = this.stackingData[k];
      this._specStackingInt[i] = s === true ? 1 : s === 'conditional' ? 2 : 0;
      this._specPenalty30[i] = Math.trunc(w * 0.3);
      this._specPenalty50[i] = Math.trunc(w * 0.5);
      if (this.effectLookup[k].priority === 'required') {
        this._isRequired[i] = 1;
        this._requiredIdxSet.add(i);
      }
    }

    // Bitmask of all required effect indices (for O(1) coverage check)
    // Disabled when nSpec >= 32 because JS bitwise ops wrap at 32 bits
    let fullReqMask = 0;
    if (nSpec < 32) {
      for (const idx of this._requiredIdxSet) {
        fullReqMask |= (1 << idx);
      }
    }
    this._fullReqMask = fullReqMask;

    // Sub-priority rank values (for tiebreaker scoring)
    // Tier multipliers ensure required always dominates preferred,
    // which always dominates nice_to_have, regardless of group sizes.
    const SUB_RANK_TIER = { required: 10000, preferred: 100, nice_to_have: 1 };
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
    this._specSubRankValues = new Int32Array(nSpec);
    for (const [priority, entries] of Object.entries(priorityGroups)) {
      const groupSize = entries.length;
      const tier = SUB_RANK_TIER[priority] || 1;
      for (const [idx, rank] of entries) {
        this._specSubRankValues[idx] = (groupSize - rank) * tier;
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

    // Exclude sub-priority rank values (same tier formula as include)
    const exclPriorityGroups = {};
    for (const spec of excludeSpecs) {
      const key = spec.key;
      if (key && key in this._exclKeyToIdx) {
        const idx = this._exclKeyToIdx[key];
        const p = spec.priority || 'nice_to_have';
        if (!exclPriorityGroups[p]) exclPriorityGroups[p] = [];
        exclPriorityGroups[p].push([idx, spec.rank || 0]);
      }
    }
    this._exclSubRankValues = new Int32Array(this._nExcl);
    for (const [priority, entries] of Object.entries(exclPriorityGroups)) {
      const groupSize = entries.length;
      const tier = SUB_RANK_TIER[priority] || 1;
      for (const [idx, rank] of entries) {
        this._exclSubRankValues[idx] = (groupSize - rank) * tier;
      }
    }

    // Relic by id lookup
    this._relicById = {};
    for (const r of relics) {
      this._relicById[r.id] = r;
    }

    // Phase cache for cross-vessel reuse
    this._phaseCache = {};

    // Compact relic map: rid -> specIndices (populated by _compactRelic)
    this._compactMap = {};
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
    // Note: character parameter is accepted but no longer used for filtering.
    // Relics with other-character effects (e.g. 【無頼漢】) are kept in the pool
    // because the relic itself is equippable by any character — only the
    // character-specific effect is inactive.  Scoring already ignores
    // effects not in the user's spec list.
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
      for (const e of group) {
        const k = e.key;
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
    const w = this._specWeights;
    const st = this._specStackingInt;
    const p30 = this._specPenalty30;
    const p50 = this._specPenalty50;
    const n = this._nSpec;
    for (let i = 0; i < n; i++) {
      const c = counts[i];
      if (c === 0) continue;
      if (st[i] === 1) {        // stackable
        score += w[i] * c;
      } else if (st[i] === 2) { // conditional
        score += w[i];
        if (c > 1) score -= p30[i] * (c - 1);
      } else {                   // non-stackable
        score += w[i];
        if (c > 1) score -= p50[i] * (c - 1);
      }
    }
    return score;
  }

  _fastSubScore(counts) {
    let sub = 0;
    const sr = this._specSubRankValues;
    const n = this._nSpec;
    for (let i = 0; i < n; i++) {
      if (counts[i] > 0) sub += sr[i];
    }
    return sub;
  }

  _compactRelic(relic) {
    const rid = relic.id;
    const specKeys = this._getSpecKeys(relic);
    const specIndices = specKeys.map(k => this._specKeyToIdx[k]);
    // Cache specIndices for Phase 3 counts rebuild
    this._compactMap[rid] = specIndices;

    const exclKeys = this._getExcludeKeys(relic);
    let exclPenalty = 0;
    let hasExclReq = false;
    let exclSubRank = 0;
    for (const k of exclKeys) {
      const idx = this._exclKeyToIdx[k];
      exclPenalty += this._exclWeights[idx];
      if (this._exclIsRequired[idx]) hasExclReq = true;
      exclSubRank += this._exclSubRankValues[idx];
    }

    const nSk = specIndices.length;
    const concBonus = nSk >= 2 ? Math.trunc(CONCENTRATION_BONUS * nSk * (nSk - 1) / 2) : 0;

    // Bitmask of which required effect indices this relic covers
    // Only computed when nSpec < 32 (fullReqMask != 0 guard handles this)
    let reqMask = 0;
    if (this._nSpec < 32) {
      for (const idx of specIndices) {
        if (this._isRequired[idx]) reqMask |= (1 << idx);
      }
    }

    return [rid, specIndices, exclPenalty, hasExclReq, concBonus, exclSubRank, reqMask];
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
    } else if (nSlots === 3) {
      return this._enumWithOverlap(compactCands, nSpec);
    } else {
      return this._enumGeneral(compactCands, nSpec);
    }
  }

  // Lightweight combo scoring: reuses pre-allocated counts, returns score + subScore only
  // Avoids cloning counts (deferred to _rebuildCounts for top-N only)
  _inlineScoreAndReset(counts, ri, rj, rk) {
    const w = this._specWeights;
    const st = this._specStackingInt;
    const p30 = this._specPenalty30;
    const p50 = this._specPenalty50;
    const sr = this._specSubRankValues;
    // Populate counts & track touched indices
    let touchedLen = 0;
    const touched = this._touchedBuf;
    for (const idx of ri[1]) { if (counts[idx]++ === 0) touched[touchedLen++] = idx; }
    for (const idx of rj[1]) { if (counts[idx]++ === 0) touched[touchedLen++] = idx; }
    for (const idx of rk[1]) { if (counts[idx]++ === 0) touched[touchedLen++] = idx; }
    let score = 0, sub = 0;
    for (let t = 0; t < touchedLen; t++) {
      const i = touched[t];
      const c = counts[i];
      counts[i] = 0; // reset immediately
      if (st[i] === 1) {
        score += w[i] * c;
      } else if (st[i] === 2) {
        score += w[i];
        if (c > 1) score -= p30[i] * (c - 1);
      } else {
        score += w[i];
        if (c > 1) score -= p50[i] * (c - 1);
      }
      sub += sr[i];
    }
    score += ri[4] + rj[4] + rk[4]; // concentration bonus
    score -= ri[2] + rj[2] + rk[2]; // exclusion penalty
    const exclSub = ri[5] + rj[5] + rk[5]; // exclude sub-rank sum
    return [score, sub, ri[4] + rj[4] + rk[4], ri[2] + rj[2] + rk[2], ri[3] || rj[3] || rk[3], exclSub, ri[6] | rj[6] | rk[6]];
  }

  // Enum result format (lightweight): [score, rids, cb, ep, her, subScore, exclSub]
  // No counts array — rebuilt later for top-N only via _rebuildCounts()

  _enumAllSame(cands, nSpec) {
    const results = [];
    const n = cands.length;
    const counts = new Int32Array(nSpec);
    this._touchedBuf = new Int32Array(nSpec);
    for (let i = 0; i < n; i++) {
      const ri = cands[i];
      for (let j = i + 1; j < n; j++) {
        const rj = cands[j];
        for (let k = j + 1; k < n; k++) {
          const rk = cands[k];
          const [sc, sub, cb, ep, her, esr, rm] = this._inlineScoreAndReset(counts, ri, rj, rk);
          results.push([sc, [ri[0], rj[0], rk[0]], cb, ep, her, sub, esr, rm]);
        }
      }
    }
    return results;
  }

  _enumAllDiff(compactCands, nSpec) {
    const results = [];
    const [c0, c1, c2] = compactCands;
    const counts = new Int32Array(nSpec);
    this._touchedBuf = new Int32Array(nSpec);
    for (let a = 0; a < c0.length; a++) {
      const ri = c0[a];
      for (let b = 0; b < c1.length; b++) {
        const rj = c1[b];
        for (let g = 0; g < c2.length; g++) {
          const [sc, sub, cb, ep, her, esr, rm] = this._inlineScoreAndReset(counts, ri, rj, c2[g]);
          results.push([sc, [ri[0], rj[0], c2[g][0]], cb, ep, her, sub, esr, rm]);
        }
      }
    }
    return results;
  }

  _enumTwoSame(compactCands, slotColors, nSpec) {
    const results = [];
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
    const counts = new Int32Array(nSpec);
    this._touchedBuf = new Int32Array(nSpec);

    for (let i = 0; i < nSame; i++) {
      const ri = sameCands[i];
      for (let j = i + 1; j < nSame; j++) {
        const rj = sameCands[j];
        for (let g = 0; g < diffCands.length; g++) {
          const rk = diffCands[g];
          if (rk[0] === ri[0] || rk[0] === rj[0]) continue;
          const [sc, sub, cb, ep, her, esr, rm] = this._inlineScoreAndReset(counts, ri, rj, rk);
          results.push([sc, [ri[0], rj[0], rk[0]], cb, ep, her, sub, esr, rm]);
        }
      }
    }
    return results;
  }

  // Optimized flat-loop enum for 3 slots with possible overlap (e.g. "Any" slots)
  _enumWithOverlap(compactCands, nSpec) {
    const results = [];
    const seen = new Set();
    const [c0, c1, c2] = compactCands;
    const counts = new Int32Array(nSpec);
    this._touchedBuf = new Int32Array(nSpec);

    for (let a = 0; a < c0.length; a++) {
      const ri = c0[a];
      const riId = ri[0];
      for (let b = 0; b < c1.length; b++) {
        const rj = c1[b];
        const rjId = rj[0];
        if (rjId === riId) continue;
        for (let g = 0; g < c2.length; g++) {
          const rk = c2[g];
          const rkId = rk[0];
          if (rkId === riId || rkId === rjId) continue;

          // Dedup: canonical sorted ID triple
          let lo, mid, hi;
          if (riId <= rjId) {
            if (rjId <= rkId) { lo = riId; mid = rjId; hi = rkId; }
            else if (riId <= rkId) { lo = riId; mid = rkId; hi = rjId; }
            else { lo = rkId; mid = riId; hi = rjId; }
          } else {
            if (riId <= rkId) { lo = rjId; mid = riId; hi = rkId; }
            else if (rjId <= rkId) { lo = rjId; mid = rkId; hi = riId; }
            else { lo = rkId; mid = rjId; hi = riId; }
          }
          const key = lo + ',' + mid + ',' + hi;
          if (seen.has(key)) continue;
          seen.add(key);

          const [sc, sub, cb, ep, her, esr, rm] = this._inlineScoreAndReset(counts, ri, rj, rk);
          results.push([sc, [lo, mid, hi], cb, ep, her, sub, esr, rm]);
        }
      }
    }
    return results;
  }

  _enumGeneral(compactCands, nSpec) {
    const results = [];
    const seen = new Set();
    const nSlots = compactCands.length;
    // Pre-allocated mutable state for recursion (avoids spread copies)
    const chosenIds = new Array(nSlots);
    const chosenSi = new Array(nSlots);
    let partialEp = 0, partialHer = false, partialCb = 0, partialEsr = 0, partialReqMask = 0;

    const self = this;
    const recurse = (slotIdx) => {
      if (slotIdx === nSlots) {
        // Canonical key for deduplication (sort IDs numerically)
        const sorted = chosenIds.slice(0, nSlots).sort((a, b) => a - b);
        const canon = sorted[0] + ',' + sorted[1] + ',' + sorted[2];
        if (seen.has(canon)) return;
        seen.add(canon);
        const counts = new Int32Array(nSpec);
        const touched = [];
        for (let s = 0; s < nSlots; s++) {
          for (const idx of chosenSi[s]) { if (counts[idx]++ === 0) touched.push(idx); }
        }
        const w = self._specWeights, st = self._specStackingInt;
        const p30 = self._specPenalty30, p50 = self._specPenalty50;
        const sr = self._specSubRankValues;
        let score = 0, sub = 0;
        for (let t = 0; t < touched.length; t++) {
          const i = touched[t], c = counts[i];
          counts[i] = 0;
          if (st[i] === 1) score += w[i] * c;
          else if (st[i] === 2) { score += w[i]; if (c > 1) score -= p30[i] * (c - 1); }
          else { score += w[i]; if (c > 1) score -= p50[i] * (c - 1); }
          sub += sr[i];
        }
        score += partialCb - partialEp;
        results.push([score, sorted.slice(), partialCb, partialEp, partialHer, sub, partialEsr, partialReqMask]);
        return;
      }

      const slot = compactCands[slotIdx];
      for (let ci = 0; ci < slot.length; ci++) {
        const cand = slot[ci];
        const rid = cand[0];
        // Check for duplicate relic (linear scan on small array)
        let dup = false;
        for (let d = 0; d < slotIdx; d++) { if (chosenIds[d] === rid) { dup = true; break; } }
        if (dup) continue;

        // Save state
        chosenIds[slotIdx] = rid;
        chosenSi[slotIdx] = cand[1];
        const savedEp = partialEp, savedHer = partialHer, savedCb = partialCb, savedEsr = partialEsr, savedReqMask = partialReqMask;
        partialEp += cand[2];
        partialHer = partialHer || cand[3];
        partialCb += cand[4];
        partialEsr += cand[5];
        partialReqMask |= cand[6];

        recurse(slotIdx + 1);

        // Restore state
        partialEp = savedEp;
        partialHer = savedHer;
        partialCb = savedCb;
        partialEsr = savedEsr;
        partialReqMask = savedReqMask;
      }
    };

    recurse(0);
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

      let mustInclude = candidates.filter(r => wantedIds.has(r.id));
      // Cap must_include to prevent unbounded candidate lists (esp. for "Any" slots)
      if (mustInclude.length > candidatesPerSlot) {
        mustInclude.sort((a, b) => this.scoreRelic(b) - this.scoreRelic(a));
        mustInclude = mustInclude.slice(0, candidatesPerSlot);
      }
      const mustIds = new Set(mustInclude.map(r => r.id));

      const remaining = candidatesPerSlot - mustInclude.length;
      let topOthers;
      if (remaining > 0) {
        const others = candidates.filter(r => !mustIds.has(r.id))
          .map(r => [this.scoreRelic(r), r])
          .sort((a, b) => b[0] - a[0]);
        topOthers = others.slice(0, remaining).map(x => x[1]);
      } else {
        topOthers = [];
      }

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

    // Lightweight combo format: [score, rids, cb, ep, her, subScore, exclSub]
    // Sort each side by score descending
    normalCombos.sort((a, b) => b[0] - a[0]);
    deepCombos.sort((a, b) => b[0] - a[0]);

    const nSpec = this._nSpec;
    const specWeights = this._specWeights;
    const specStackingInt = this._specStackingInt;
    const specPenalty30 = this._specPenalty30;
    const specPenalty50 = this._specPenalty50;
    const isRequired = this._isRequired;
    const requiredIdxSet = this._requiredIdxSet;

    // Handle single-side cases
    if (!normalCombos.length) {
      return this._combosToResultsCompact(deepCombos.slice(0, topN), true);
    }
    if (!deepCombos.length) {
      return this._combosToResultsCompact(normalCombos.slice(0, topN), false);
    }

    // Phase 3: Cross-pair with bitmask pre-filter + two-tier heap pruning
    // Adaptive maxPairs: with few specs, scores are clustered so score-based pruning
    // is ineffective. Reducing candidate count avoids evaluating millions of ~equal pairs.
    const maxPairs = Math.min(500, Math.max(150, nSpec * 50));
    const nTop = Math.min(normalCombos.length, maxPairs);
    const dTop = Math.min(deepCombos.length, maxPairs);

    const normalTop = normalCombos.slice(0, nTop);
    const deepTop = deepCombos.slice(0, dTop);
    const bestDeepScore = deepTop[0][0];

    // Build rid -> specIndices lookup from compact cache for counts rebuild
    const compactMap = this._compactMap;

    // Rebuild counts for top combos only (lazy, from relic IDs)
    const rebuildCounts = (rids) => {
      const cts = new Int32Array(nSpec);
      for (const rid of rids) {
        const si = compactMap[rid];
        if (si) for (const idx of si) cts[idx]++;
      }
      return cts;
    };

    // Pre-build counts for top combos
    const nCountsArr = new Array(nTop);
    for (let i = 0; i < nTop; i++) nCountsArr[i] = rebuildCounts(normalTop[i][1]);
    const dCountsArr = new Array(dTop);
    for (let i = 0; i < dTop; i++) dCountsArr[i] = rebuildCounts(deepTop[i][1]);

    // Bitmask pre-filter setup
    const fullReqMask = this._fullReqMask;
    const hasAnyRequired = fullReqMask !== 0;

    // Two-tier heap: separate heaps for required_met=true and false
    // This eliminates pruning threshold oscillation between the two categories
    const heapTrue = new MinHeap();   // entries where required_met = true
    const heapFalse = new MinHeap();  // entries where required_met = false
    const resultMap = new Map();
    let counter = 0;
    let trueFull = false; // once heapTrue.size >= topN, stop accepting false entries
    const subRankValues = this._specSubRankValues;

    for (let ni = 0; ni < nTop; ni++) {
      const nCombo = normalTop[ni];
      const ns = nCombo[0], nRids = nCombo[1], nConc = nCombo[2], nEp = nCombo[3], nHer = nCombo[4], nExclSub = nCombo[6] || 0;
      const nReqMask = nCombo[7] || 0;
      const nCts = nCountsArr[ni];

      // Outer pruning: if trueFull, use heapTrue threshold for score-only pruning
      if (trueFull) {
        const h = heapTrue.peek();
        if (-(ns + bestDeepScore) >= h[0]) break;
      }

      for (let di = 0; di < dTop; di++) {
        const dCombo = deepTop[di];
        const ds = dCombo[0], dRids = dCombo[1], dConc = dCombo[2], dEp = dCombo[3], dHer = dCombo[4], dExclSub = dCombo[6] || 0;
        const dReqMask = dCombo[7] || 0;
        const dCts = dCountsArr[di];

        // Inner pruning (score-only, against heapTrue only)
        // Note: pruning against heapFalse is unsafe — it can skip pairs
        // whose merged score is low but still satisfy all required effects
        // (reqMet=true), missing entries that should go into heapTrue.
        if (trueFull) {
          const h = heapTrue.peek();
          if (-(ns + ds) >= h[0]) break;
        }

        // Bitmask pre-filter: skip pairs that can NEVER satisfy all required include-effects
        if (hasAnyRequired && ((nReqMask | dReqMask) !== fullReqMask)) {
          if (trueFull) continue; // true side full — skip entirely
          // Otherwise still score — may enter heapFalse as fallback
        }

        // Inline merged scoring (integer stacking codes, pre-computed penalties)
        let score = 0;
        let hasAllRequired = true;
        let subScore = 0;
        for (let i = 0; i < nSpec; i++) {
          const c = nCts[i] + dCts[i];
          if (c === 0) {
            if (isRequired[i]) hasAllRequired = false;
            continue;
          }
          const si = specStackingInt[i];
          if (si === 1) {
            score += specWeights[i] * c;
          } else if (si === 2) {
            score += specWeights[i];
            if (c > 1) score -= specPenalty30[i] * (c - 1);
          } else {
            score += specWeights[i];
            if (c > 1) score -= specPenalty50[i] * (c - 1);
          }
          subScore += subRankValues[i];
        }
        subScore -= (nExclSub + dExclSub);

        score += nConc + dConc - nEp - dEp;
        const hasExclReq = nHer || dHer;
        const reqMet = hasAllRequired && !hasExclReq;

        // Heap key: [-score, -subScore, counter] (no reqMet — heaps are separate)
        const heapKey = [-score, -subScore, counter];

        if (reqMet) {
          // Insert into heapTrue
          if (heapTrue.size < topN) {
            heapTrue.push(heapKey);
            resultMap.set(counter, [true, score, subScore, nCts, dCts, nRids, dRids]);
            if (heapTrue.size >= topN) trueFull = true;
          } else if (this._heapCompare3(heapKey, heapTrue.peek()) < 0) {
            const evicted = heapTrue.replace(heapKey);
            resultMap.delete(evicted[2]);
            resultMap.set(counter, [true, score, subScore, nCts, dCts, nRids, dRids]);
          }
        } else if (!trueFull) {
          // Insert into heapFalse only if heapTrue not yet full
          if (heapFalse.size < topN) {
            heapFalse.push(heapKey);
            resultMap.set(counter, [false, score, subScore, nCts, dCts, nRids, dRids]);
          } else if (this._heapCompare3(heapKey, heapFalse.peek()) < 0) {
            const evicted = heapFalse.replace(heapKey);
            resultMap.delete(evicted[2]);
            resultMap.set(counter, [false, score, subScore, nCts, dCts, nRids, dRids]);
          }
        }

        counter++;
      }
    }

    // Build full results from both heaps
    const buildResult = (hk) => {
      const data = resultMap.get(hk[2]);
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

      return {
        required_met: reqMet,
        score,
        sub_score: subScore,
        matched_keys: matchedKeys,
        missing_required: missing,
        excluded_present: excludedPresent,
        relics: [...nRelics, ...dRelics],
        normal_relics: nRelics,
        deep_relics: dRelics,
      };
    };

    // Deterministic sort: score desc, sub_score desc, sorted relic IDs asc
    const _resultCmp = (a, b) => {
      const sc = b.score - a.score;
      if (sc !== 0) return sc;
      const ss = (b.sub_score || 0) - (a.sub_score || 0);
      if (ss !== 0) return ss;
      const aIds = a.relics.map(r => r.id).sort((x, y) => x - y);
      const bIds = b.relics.map(r => r.id).sort((x, y) => x - y);
      for (let i = 0; i < Math.min(aIds.length, bIds.length); i++) {
        if (aIds[i] !== bIds[i]) return aIds[i] - bIds[i];
      }
      return aIds.length - bIds.length;
    };

    // Drain heapTrue (all true entries)
    const trueResults = [];
    while (heapTrue.size > 0) trueResults.push(buildResult(heapTrue.pop()));
    trueResults.sort(_resultCmp);

    // Drain heapFalse (all false entries)
    const falseResults = [];
    while (heapFalse.size > 0) falseResults.push(buildResult(heapFalse.pop()));
    falseResults.sort(_resultCmp);

    // Merge: true first, fill remainder with false up to topN
    const results = [...trueResults];
    const need = topN - results.length;
    if (need > 0) {
      for (let i = 0; i < Math.min(need, falseResults.length); i++) {
        results.push(falseResults[i]);
      }
    }

    return results;
  }

  _heapCompare3(a, b) {
    if (a[0] !== b[0]) return a[0] - b[0];
    if (a[1] !== b[1]) return a[1] - b[1];
    return a[2] - b[2];
  }

  // New lightweight format: [score, rids, cb, ep, her, subScore, exclSub]
  _combosToResultsCompact(combos, isDeepOnly) {
    const nSpec = this._nSpec;
    const compactMap = this._compactMap;
    const results = [];
    for (const combo of combos) {
      const score = combo[0], rids = combo[1], her = combo[4], comboSubScore = combo[5], exclSubSum = combo[6] || 0;
      // Rebuild counts from rids
      const counts = new Int32Array(nSpec);
      for (const rid of rids) {
        const si = compactMap[rid];
        if (si) for (const idx of si) counts[idx]++;
      }

      const matchedKeys = new Set();
      for (let i = 0; i < nSpec; i++) {
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
      const subScore = (comboSubScore !== undefined ? comboSubScore : 0) - exclSubSum;
      results.push({
        required_met: missing.length === 0 && !her,
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
        const subMatched = matchedKeys.has(group[si].key);
        const subEntry = {
          key: group[si].key,
          name_ja: group[si].name_ja || '',
          name_en: group[si].name_en || '',
          matched: subMatched,
          isDebuff: true,
        };
        if (subMatched && group[si].key in this.effectLookup) {
          subEntry.priority = this.effectLookup[group[si].key].priority;
        }
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
    const ss = (b.subScore || 0) - (a.subScore || 0);
    if (ss !== 0) return ss;
    // Deterministic tiebreaker: sorted relic IDs (ascending)
    const aIds = [...(a.normalRelics || []), ...(a.deepRelics || []), ...(a.relics || [])].map(r => r.id).sort((x, y) => x - y);
    const bIds = [...(b.normalRelics || []), ...(b.deepRelics || []), ...(b.relics || [])].map(r => r.id).sort((x, y) => x - y);
    for (let i = 0; i < Math.min(aIds.length, bIds.length); i++) {
      if (aIds[i] !== bIds[i]) return aIds[i] - bIds[i];
    }
    return aIds.length - bIds.length;
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
