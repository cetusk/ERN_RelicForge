#!/usr/bin/env python3
"""
遺物組み合わせ最適化ツール
relic_parser の出力 JSON を入力とし、献器のスロット色制約に基づいて
最適な遺物の組み合わせ候補を提案する。
"""
import json
import os
import re
import sys
import argparse
import heapq
from itertools import combinations, product
from typing import List, Dict, Set, Tuple, Optional


# === Priority weights ===
PRIORITY_WEIGHTS = {
    'required': 100,
    'preferred': 10,
    'nice_to_have': 1,
}

# Concentration bonus: reward for multiple desired effects on a single relic
CONCENTRATION_BONUS = 5

# Character name mapping (JA -> EN)
CHARACTER_NAMES = {
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
}

CHARACTER_NAMES_REV = {v.lower(): k for k, v in CHARACTER_NAMES.items()}


def load_effects_config(config_file: str) -> List[Dict]:
    """効果指定ファイルの読み込み"""
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    effects = data.get('effects', [])
    for eff in effects:
        if eff.get('priority') not in PRIORITY_WEIGHTS:
            print(f"Warning: Unknown priority '{eff.get('priority')}' for effect "
                  f"'{eff.get('key', eff.get('name_ja', '?'))}', defaulting to 'nice_to_have'",
                  file=sys.stderr)
            eff['priority'] = 'nice_to_have'
    return effects


def load_vessels_data(vessels_file: str) -> Dict:
    """献器データの読み込み"""
    with open(vessels_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_stacking_data(effects_data_file: str) -> Dict:
    """効果の重複可否データを読み込み

    effects_data.json から各効果キーの stackable 値を取得。
    返り値: key -> True (完全スタック可) / False (不可) / "conditional" (条件付き)
    優先度: True > "conditional" > False
    """
    with open(effects_data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    key_stackable: Dict = {}
    for eid, entry in data.get('effects', {}).items():
        key = entry['key']
        stackable = entry.get('stackable', False)
        if key not in key_stackable:
            if stackable is True:
                key_stackable[key] = True
            elif stackable == 'conditional':
                key_stackable[key] = 'conditional'
            else:
                key_stackable[key] = False
        elif stackable is True:
            key_stackable[key] = True
        elif stackable == 'conditional' and key_stackable[key] is False:
            key_stackable[key] = 'conditional'
    return key_stackable


def _extract_base_key_and_level(key: str):
    """PlusN サフィックスからベースキーとレベルを抽出

    例: 'physicalAttackUpPlus4' -> ('physicalAttackUp', 4)
        'improvedDodging'       -> ('improvedDodging', None)
    """
    m = re.match(r'^(.+?)Plus(\d+)$', key)
    if m:
        return m.group(1), int(m.group(2))
    return key, None


def resolve_character_name_ja(name: str) -> str:
    """キャラクター名を日本語に正規化"""
    if name.startswith('【') and name.endswith('】'):
        return name[1:-1]
    if name in CHARACTER_NAMES:
        return name
    lower = name.lower()
    if lower in CHARACTER_NAMES_REV:
        return CHARACTER_NAMES_REV[lower]
    return name


class RelicOptimizer:
    def __init__(self, relics: List[Dict], effect_specs: List[Dict],
                 vessels_data: Optional[Dict] = None,
                 stacking_data: Optional[Dict] = None):
        self.all_relics = relics
        self.effect_specs = effect_specs
        self.vessels_data = vessels_data
        self.stacking_data: Dict[str, bool] = stacking_data or {}

        # Pre-computed caches (populated on demand)
        self._effect_keys_cache: Dict[int, Set[str]] = {}
        self._spec_keys_cache: Dict[int, Tuple] = {}
        self._score_cache: Dict[int, int] = {}
        self._exclude_keys_cache: Dict[int, Tuple] = {}

        # Separate include and exclude specs
        include_specs = [s for s in effect_specs if not s.get('exclude')]
        exclude_specs = [s for s in effect_specs if s.get('exclude')]

        # Build include effect lookup: key -> { priority, weight }
        self.effect_lookup: Dict[str, Dict] = {}
        for spec in include_specs:
            key = spec.get('key')
            name_ja = spec.get('name_ja')
            name_en = spec.get('name_en')
            weight = PRIORITY_WEIGHTS[spec['priority']]
            if key:
                self.effect_lookup[key] = {
                    'priority': spec['priority'],
                    'weight': weight,
                    'spec': spec,
                }
            if name_ja or name_en:
                self._resolve_name_matches(
                    name_ja, name_en, spec, weight, self.effect_lookup)

        # Build exclude effect lookup: key -> { priority, weight }
        self.exclude_lookup: Dict[str, Dict] = {}
        for spec in exclude_specs:
            key = spec.get('key')
            name_ja = spec.get('name_ja')
            name_en = spec.get('name_en')
            weight = PRIORITY_WEIGHTS[spec['priority']]
            if key:
                self.exclude_lookup[key] = {
                    'priority': spec['priority'],
                    'weight': weight,
                    'spec': spec,
                }
            if name_ja or name_en:
                self._resolve_name_matches(
                    name_ja, name_en, spec, weight, self.exclude_lookup)

        # === Integer-indexed arrays for fast scoring ===
        # Spec keys → contiguous int indices
        self._spec_key_list = sorted(self.effect_lookup.keys())
        self._spec_key_to_idx = {k: i for i, k in enumerate(self._spec_key_list)}
        n_spec = len(self._spec_key_list)
        self._n_spec = n_spec
        self._spec_weights = [self.effect_lookup[k]['weight']
                              for k in self._spec_key_list]
        # Stacking codes: 0=non-stackable, 1=stackable, 2=conditional
        self._spec_stacking_int = []
        self._spec_penalty30 = []
        self._spec_penalty50 = []
        self._is_required = [False] * n_spec
        for i, k in enumerate(self._spec_key_list):
            s = self.stacking_data.get(k, False)
            self._spec_stacking_int.append(1 if s is True else 2 if s == 'conditional' else 0)
            w = self._spec_weights[i]
            self._spec_penalty30.append(int(w * 0.3))
            self._spec_penalty50.append(int(w * 0.5))
            if self.effect_lookup[k]['priority'] == 'required':
                self._is_required[i] = True
        self._required_idx_set = frozenset(
            i for i in range(n_spec) if self._is_required[i])
        # Keep original for backward compatibility
        self._spec_stacking = [self.stacking_data.get(k, False)
                               for k in self._spec_key_list]

        # Sub-priority rank values (for tiebreaker scoring)
        # Tier multipliers ensure required always dominates preferred,
        # which always dominates nice_to_have, regardless of group sizes.
        SUB_RANK_TIER = {'required': 10000, 'preferred': 100, 'nice_to_have': 1}
        priority_groups: Dict[str, list] = {}
        for spec in include_specs:
            key = spec.get('key')
            if key and key in self._spec_key_to_idx:
                idx = self._spec_key_to_idx[key]
                p = spec['priority']
                priority_groups.setdefault(p, []).append(
                    (idx, spec.get('rank', 0)))

        self._spec_sub_rank_values = [0] * self._n_spec
        for priority, entries in priority_groups.items():
            group_size = len(entries)
            tier = SUB_RANK_TIER.get(priority, 1)
            for idx, rank in entries:
                self._spec_sub_rank_values[idx] = (group_size - rank) * tier

        # Exclude keys → contiguous int indices
        self._excl_key_list = sorted(self.exclude_lookup.keys())
        self._excl_key_to_idx = {k: i for i, k in enumerate(self._excl_key_list)}
        self._n_excl = len(self._excl_key_list)
        self._excl_weights = [self.exclude_lookup[k]['weight']
                              for k in self._excl_key_list]
        self._excl_is_required = [self.exclude_lookup[k]['priority'] == 'required'
                                  for k in self._excl_key_list]

        # Exclude sub-priority rank values (same tier formula as include)
        excl_priority_groups: Dict[str, list] = {}
        for spec in exclude_specs:
            key = spec.get('key')
            if key and key in self._excl_key_to_idx:
                idx = self._excl_key_to_idx[key]
                p = spec['priority']
                excl_priority_groups.setdefault(p, []).append(
                    (idx, spec.get('rank', 0)))

        self._excl_sub_rank_values = [0] * self._n_excl
        for priority, entries in excl_priority_groups.items():
            group_size = len(entries)
            tier = SUB_RANK_TIER.get(priority, 1)
            for idx, rank in entries:
                self._excl_sub_rank_values[idx] = (group_size - rank) * tier

        # Relic-by-id lookup for deferred result construction
        self._relic_by_id = {r['id']: r for r in relics}

        # Phase cache for cross-vessel reuse
        self._phase_cache: Dict[tuple, list] = {}

    def _resolve_name_matches(self, name_ja: Optional[str], name_en: Optional[str],
                               spec: Dict, weight: int,
                               target_lookup: Dict[str, Dict]):
        """Resolve name_ja/name_en partial matches to effect keys from relic data"""
        for relic in self.all_relics:
            for group in relic['effects']:
                for eff in group:
                    matched = False
                    if name_ja and name_ja in eff.get('name_ja', ''):
                        matched = True
                    if name_en and name_en.lower() in eff.get('name_en', '').lower():
                        matched = True
                    if matched and eff['key'] not in target_lookup:
                        target_lookup[eff['key']] = {
                            'priority': spec['priority'],
                            'weight': weight,
                            'spec': spec,
                        }

    def filter_relics(self, types: Optional[List[str]] = None,
                      character: Optional[str] = None,
                      color: Optional[str] = None) -> List[Dict]:
        """前処理フィルタリング"""
        filtered = self.all_relics

        if types:
            type_set = set(types)
            filtered = [r for r in filtered if r.get('itemType') in type_set]

        if color:
            filtered = [r for r in filtered if r.get('itemColor') == color]

        # Note: character parameter is accepted but no longer used for filtering.
        # Relics with other-character effects (e.g. 【無頼漢】) are kept in the pool
        # because the relic itself is equippable by any character — only the
        # character-specific effect is inactive.  Scoring already ignores
        # effects not in the user's spec list.

        return filtered

    def get_relic_effect_keys(self, relic: Dict) -> Set[str]:
        """遺物のメイン効果キーを取得（デバフ副効果は除外、キャッシュ付き）"""
        rid = relic['id']
        if rid in self._effect_keys_cache:
            return self._effect_keys_cache[rid]
        keys = set()
        for group in relic['effects']:
            if group:
                keys.add(group[0]['key'])
        self._effect_keys_cache[rid] = keys
        return keys

    def _get_spec_keys(self, relic: Dict) -> Tuple:
        """遺物の効果キーのうち指定効果にマッチするもののみ返す（キャッシュ付き）
        サブ効果（デメリット等）も含め全効果を走査する。"""
        rid = relic['id']
        if rid in self._spec_keys_cache:
            return self._spec_keys_cache[rid]
        keys = []
        for group in relic['effects']:
            for e in group:
                k = e['key']
                if k in self.effect_lookup:
                    keys.append(k)
        result = tuple(keys)
        self._spec_keys_cache[rid] = result
        return result

    def _get_exclude_keys(self, relic: Dict) -> Tuple:
        """遺物の効果キーのうち除外対象にマッチするもののみ返す（キャッシュ付き）
        サブ効果（デメリット等）も含め全効果を走査する。"""
        rid = relic['id']
        if rid in self._exclude_keys_cache:
            return self._exclude_keys_cache[rid]
        keys = []
        for group in relic['effects']:
            for e in group:
                k = e['key']
                if k in self.exclude_lookup:
                    keys.append(k)
        result = tuple(keys)
        self._exclude_keys_cache[rid] = result
        return result

    # === Fast scoring and compact representations for optimize_combined ===

    def _fast_stacking_score(self, counts):
        """配列ベースの高速スコア計算。counts: list[int], 長さ n_spec"""
        score = 0
        weights = self._spec_weights
        stacking_int = self._spec_stacking_int
        penalty30 = self._spec_penalty30
        penalty50 = self._spec_penalty50
        for i in range(self._n_spec):
            c = counts[i]
            if c == 0:
                continue
            si = stacking_int[i]
            if si == 1:  # stackable
                score += weights[i] * c
            elif si == 2:  # conditional
                score += weights[i]
                if c > 1:
                    score -= penalty30[i] * (c - 1)
            else:  # non-stackable
                score += weights[i]
                if c > 1:
                    score -= penalty50[i] * (c - 1)
        return score

    def _fast_sub_score(self, counts):
        """サブ優先度タイブレーカースコア。存在判定のみ (count>0)"""
        sub = 0
        sub_ranks = self._spec_sub_rank_values
        for i in range(self._n_spec):
            if counts[i] > 0:
                sub += sub_ranks[i]
        return sub

    def _compact_relic(self, relic: Dict) -> Tuple:
        """レリックをコンパクトなタプルに変換
        Returns: (rid, spec_indices, excl_penalty, has_excl_req,
                  conc_bonus, excl_sub_rank)
        """
        rid = relic['id']
        spec_keys = self._get_spec_keys(relic)
        spec_indices = tuple(self._spec_key_to_idx[k] for k in spec_keys)

        excl_keys = self._get_exclude_keys(relic)
        excl_penalty = 0
        has_excl_req = False
        excl_sub_rank = 0
        for k in excl_keys:
            idx = self._excl_key_to_idx[k]
            excl_penalty += self._excl_weights[idx]
            if self._excl_is_required[idx]:
                has_excl_req = True
            excl_sub_rank += self._excl_sub_rank_values[idx]

        n_sk = len(spec_indices)
        conc_bonus = CONCENTRATION_BONUS * n_sk * (n_sk - 1) // 2 \
            if n_sk >= 2 else 0

        return (rid, spec_indices, excl_penalty, has_excl_req,
                conc_bonus, excl_sub_rank)

    def _enumerate_combos(self, compact_cands, slot_colors):
        """スロット色パターンに応じた最適なコンボ列挙
        Returns: list of (score, counts_tuple, conc, excl_pen,
                          has_excl_req, relic_ids, excl_sub_sum)
        """
        n_spec = self._n_spec
        n_slots = len(slot_colors)

        # Classify the slot pattern
        has_any = 'Any' in slot_colors
        colors_no_any = [c for c in slot_colors if c != 'Any']
        unique_colors = set(colors_no_any)

        if n_slots == 3 and not has_any and len(unique_colors) == 1:
            return self._enum_all_same(compact_cands[0], n_spec)
        elif n_slots == 3 and not has_any and len(unique_colors) == 3:
            return self._enum_all_diff(compact_cands, n_spec)
        elif n_slots == 3 and not has_any and len(unique_colors) == 2:
            return self._enum_two_same(compact_cands, slot_colors, n_spec)
        else:
            return self._enum_general(compact_cands, n_spec)

    def _enum_all_same(self, cands, n_spec):
        """全スロット同色: C(n,3) で列挙"""
        results = []
        n = len(cands)
        for i in range(n):
            ri_id, ri_si, ri_ep, ri_her, ri_cb, ri_esr = cands[i]
            for j in range(i + 1, n):
                rj_id, rj_si, rj_ep, rj_her, rj_cb, rj_esr = cands[j]
                for k in range(j + 1, n):
                    rk_id, rk_si, rk_ep, rk_her, rk_cb, rk_esr = cands[k]
                    counts = [0] * n_spec
                    for idx in ri_si:
                        counts[idx] += 1
                    for idx in rj_si:
                        counts[idx] += 1
                    for idx in rk_si:
                        counts[idx] += 1
                    score = self._fast_stacking_score(counts)
                    score += ri_cb + rj_cb + rk_cb
                    score -= ri_ep + rj_ep + rk_ep
                    her = ri_her or rj_her or rk_her
                    results.append((
                        score,
                        tuple(counts),
                        ri_cb + rj_cb + rk_cb,
                        ri_ep + rj_ep + rk_ep,
                        her,
                        (ri_id, rj_id, rk_id),
                        ri_esr + rj_esr + rk_esr))
        return results

    def _enum_all_diff(self, compact_cands, n_spec):
        """全スロット異色: 重複チェック不要"""
        results = []
        c0, c1, c2 = compact_cands[0], compact_cands[1], compact_cands[2]
        for ri_id, ri_si, ri_ep, ri_her, ri_cb, ri_esr in c0:
            for rj_id, rj_si, rj_ep, rj_her, rj_cb, rj_esr in c1:
                for rk_id, rk_si, rk_ep, rk_her, rk_cb, rk_esr in c2:
                    counts = [0] * n_spec
                    for idx in ri_si:
                        counts[idx] += 1
                    for idx in rj_si:
                        counts[idx] += 1
                    for idx in rk_si:
                        counts[idx] += 1
                    score = self._fast_stacking_score(counts)
                    score += ri_cb + rj_cb + rk_cb
                    score -= ri_ep + rj_ep + rk_ep
                    her = ri_her or rj_her or rk_her
                    results.append((
                        score,
                        tuple(counts),
                        ri_cb + rj_cb + rk_cb,
                        ri_ep + rj_ep + rk_ep,
                        her,
                        (ri_id, rj_id, rk_id),
                        ri_esr + rj_esr + rk_esr))
        return results

    def _enum_two_same(self, compact_cands, slot_colors, n_spec):
        """2同色+1異色: C(n,2)*m"""
        results = []
        # Identify which slots share the same color
        from collections import Counter
        color_counts = Counter(slot_colors)
        same_color = max(color_counts, key=color_counts.get)
        # Find which slot index has the different color
        same_idx = [i for i, c in enumerate(slot_colors) if c == same_color]
        diff_idx = [i for i, c in enumerate(slot_colors) if c != same_color][0]

        same_cands = compact_cands[same_idx[0]]
        diff_cands = compact_cands[diff_idx]
        n_same = len(same_cands)

        for i in range(n_same):
            ri_id, ri_si, ri_ep, ri_her, ri_cb, ri_esr = same_cands[i]
            for j in range(i + 1, n_same):
                rj_id, rj_si, rj_ep, rj_her, rj_cb, rj_esr = same_cands[j]
                for rk_id, rk_si, rk_ep, rk_her, rk_cb, rk_esr in diff_cands:
                    if rk_id == ri_id or rk_id == rj_id:
                        continue
                    counts = [0] * n_spec
                    for idx in ri_si:
                        counts[idx] += 1
                    for idx in rj_si:
                        counts[idx] += 1
                    for idx in rk_si:
                        counts[idx] += 1
                    score = self._fast_stacking_score(counts)
                    score += ri_cb + rj_cb + rk_cb
                    score -= ri_ep + rj_ep + rk_ep
                    her = ri_her or rj_her or rk_her
                    results.append((
                        score,
                        tuple(counts),
                        ri_cb + rj_cb + rk_cb,
                        ri_ep + rj_ep + rk_ep,
                        her,
                        (ri_id, rj_id, rk_id),
                        ri_esr + rj_esr + rk_esr))
        return results

    def _enum_general(self, compact_cands, n_spec):
        """汎用列挙: Any スロットやその他のパターン"""
        results = []
        seen = set()

        def recurse(slot_idx, chosen_ids, partial_si, partial_ep,
                     partial_her, partial_cb, partial_esr):
            if slot_idx == len(compact_cands):
                canon = tuple(sorted(chosen_ids))
                if canon in seen:
                    return
                seen.add(canon)
                counts = [0] * n_spec
                for si_list in partial_si:
                    for idx in si_list:
                        counts[idx] += 1
                score = self._fast_stacking_score(counts)
                score += partial_cb - partial_ep
                results.append((
                    score,
                    tuple(counts),
                    partial_cb, partial_ep, partial_her,
                    tuple(chosen_ids),
                    partial_esr))
                return

            for rid, si, ep, her, cb, esr in compact_cands[slot_idx]:
                if rid in chosen_ids:
                    continue
                recurse(
                    slot_idx + 1,
                    chosen_ids + (rid,),
                    partial_si + (si,),
                    partial_ep + ep,
                    partial_her or her,
                    partial_cb + cb,
                    partial_esr + esr)

        recurse(0, (), (), 0, False, 0, 0)
        return results

    def is_stackable(self, key: str) -> bool:
        """効果がスタック可能かどうか（重複装備で恩恵があるか）"""
        return self.stacking_data.get(key, False) is True

    def score_relic(self, relic: Dict) -> int:
        """個別遺物のスコア計算（キャッシュ付き）"""
        rid = relic['id']
        if rid in self._score_cache:
            return self._score_cache[rid]
        score = 0
        spec_keys = self._get_spec_keys(relic)
        for key in spec_keys:
            score += self.effect_lookup[key]['weight']
        # Concentration bonus: C(N, 2) pairs
        n = len(spec_keys)
        if n >= 2:
            score += CONCENTRATION_BONUS * n * (n - 1) // 2
        # Exclusion penalty
        for key in self._get_exclude_keys(relic):
            score -= self.exclude_lookup[key]['weight']
        self._score_cache[rid] = score
        return score

    def _stacking_aware_score(self, effect_counts: Dict[str, int]) -> int:
        """重複可否を考慮したスコア計算

        スタック可能な効果: weight × 遺物数（重複分の恩恵あり）
        スタック不可な効果: weight × 1（重複しても1回分のみ）
        条件付き (conditional): 同レベル重複不可、異レベルは加算
          - 同一キー(同レベル)が重複する場合、ペナルティを適用
          - PlusN なしキー: weight×1 + 重複ペナルティ
        """
        score = 0
        for key, count in effect_counts.items():
            if key not in self.effect_lookup:
                continue
            weight = self.effect_lookup[key]['weight']
            stacking = self.stacking_data.get(key, False)

            if stacking is True:
                score += weight * count
            elif stacking == 'conditional':
                # 同一キー = 同一レベル → 1回のみカウント
                score += weight
                # 重複している場合、余剰分にペナルティ（weight の 30%）
                if count > 1:
                    score -= int(weight * 0.3 * (count - 1))
            else:
                score += weight  # 非スタック: 1回のみカウント
                # 重複ペナルティ: 重複不可の効果が重複 → weight の 50% 減点
                if count > 1:
                    score -= int(weight * 0.5 * (count - 1))
        return score

    def score_combination(self, combo: Tuple[Dict, ...]):
        """組み合わせのスコア計算（重複可否・集中ボーナス・除外を考慮）

        スタック可能な効果は遺物ごとにカウントし、
        スタック不可な効果は1回のみカウントする。
        集中ボーナス: 1遺物に複数の指定効果がある場合に加算。
        除外ペナルティ: 除外対象の効果が含まれている場合に減算。
        """
        effect_counts: Dict[str, int] = {}
        concentration = 0
        exclude_penalty = 0
        has_exclude_required = False
        excluded_present: Set[str] = set()
        seen_ids = set()
        for relic in combo:
            rid = relic['id']
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            spec_keys = self._get_spec_keys(relic)
            for key in spec_keys:
                effect_counts[key] = effect_counts.get(key, 0) + 1
            # Concentration bonus
            n_sk = len(spec_keys)
            if n_sk >= 2:
                concentration += CONCENTRATION_BONUS * n_sk * (n_sk - 1) // 2
            # Exclusion penalty
            for key in self._get_exclude_keys(relic):
                exclude_penalty += self.exclude_lookup[key]['weight']
                excluded_present.add(key)
                if self.exclude_lookup[key]['priority'] == 'required':
                    has_exclude_required = True

        score = self._stacking_aware_score(effect_counts)
        score += concentration - exclude_penalty

        # Sub-priority tiebreaker
        sub_score = 0
        for key in effect_counts:
            idx = self._spec_key_to_idx.get(key)
            if idx is not None:
                sub_score += self._spec_sub_rank_values[idx]

        matched_keys = set(effect_counts.keys())
        required_keys = {
            k for k, v in self.effect_lookup.items()
            if v['priority'] == 'required'
        }
        missing_required = sorted(required_keys - matched_keys)
        required_met = len(missing_required) == 0 and not has_exclude_required

        return required_met, score, sub_score, matched_keys, missing_required, excluded_present

    def get_vessel_configs(self, character: str,
                           vessel_types: Optional[List[str]] = None,
                           deep: bool = False) -> List[Dict]:
        """キャラクターの献器設定を取得"""
        if not self.vessels_data:
            return []

        char_ja = resolve_character_name_ja(character)
        char_data = self.vessels_data.get('characters', {}).get(char_ja)
        if not char_data:
            print(f"Warning: No vessel data for character '{char_ja}'",
                  file=sys.stderr)
            return []

        slot_key = 'deepSlots' if deep else 'normalSlots'
        vessel_type_info = {
            vt['key']: vt for vt in self.vessels_data.get('vesselTypes', [])
        }

        configs = []
        for vkey, vdata in char_data.get('vessels', {}).items():
            if vessel_types and vkey not in vessel_types:
                continue
            slots = vdata.get(slot_key, [])
            vt_info = vessel_type_info.get(vkey, {})
            configs.append({
                'key': vkey,
                'nameJa': f"{char_ja}の{vt_info.get('nameJa', vkey)}",
                'nameEn': f"{char_data.get('nameEn', char_ja)}'s "
                          f"{vt_info.get('nameEn', vkey)}",
                'slots': slots,
                'normalSlots': vdata.get('normalSlots', []),
                'deepSlots': vdata.get('deepSlots', []),
            })

        # Universal vessels
        if not vessel_types:
            for uv in self.vessels_data.get('universalVessels', []):
                slots = uv.get(slot_key, [])
                configs.append({
                    'key': uv['key'],
                    'nameJa': uv['nameJa'],
                    'nameEn': uv['nameEn'],
                    'slots': slots,
                    'normalSlots': uv.get('normalSlots', []),
                    'deepSlots': uv.get('deepSlots', []),
                    'universal': True,
                })

        return configs

    def optimize_for_vessel(self, slot_colors: List[str],
                            types: Optional[List[str]] = None,
                            character: Optional[str] = None,
                            candidates_per_slot: int = 30,
                            top_n: int = 10) -> List[Dict]:
        """献器のスロット制約に基づく最適化"""
        base_filtered = self.filter_relics(types=types, character=character)

        # Group filtered relics by color
        by_color: Dict[str, List[Dict]] = {}
        for r in base_filtered:
            c = r.get('itemColor', '')
            by_color.setdefault(c, []).append(r)

        # For each slot, get scored candidate relics
        slot_candidates = []
        for slot_color in slot_colors:
            if slot_color == 'Any':
                candidates = base_filtered
            else:
                candidates = by_color.get(slot_color, [])

            scored = [(self.score_relic(r), r) for r in candidates]
            scored.sort(key=lambda x: x[0], reverse=True)
            top = [r for _, r in scored[:candidates_per_slot]]
            slot_candidates.append(top)

        if any(len(sc) == 0 for sc in slot_candidates):
            return []

        total = 1
        for sc in slot_candidates:
            total *= len(sc)
        print(f"  Candidates per slot: {[len(sc) for sc in slot_candidates]}, "
              f"product: {total}", file=sys.stderr)

        # Enumerate combinations (cartesian product, no duplicate relics)
        results = []
        seen = set()
        for combo in product(*slot_candidates):
            ids = tuple(r['id'] for r in combo)
            if len(set(ids)) != len(ids):
                continue
            canon = tuple(sorted(ids))
            if canon in seen:
                continue
            seen.add(canon)

            req_met, score, sub_score, matched, missing, excl_present = \
                self.score_combination(combo)
            results.append({
                'required_met': req_met,
                'score': score,
                'sub_score': sub_score,
                'matched_keys': matched,
                'missing_required': missing,
                'excluded_present': excl_present,
                'relics': combo,
            })

        results.sort(key=lambda x: (x['required_met'], x['score'],
                                    x['sub_score']), reverse=True)
        return results[:top_n]

    def _build_slot_candidates(self, slot_colors: List[str],
                               filtered: List[Dict],
                               candidates_per_slot: int
                               ) -> List[List[Dict]]:
        """スロットごとの候補遺物リストを構築

        指定効果を持つ遺物は必ず候補に含め、
        残りをスコア上位で埋める。
        """
        by_color: Dict[str, List[Dict]] = {}
        for r in filtered:
            c = r.get('itemColor', '')
            by_color.setdefault(c, []).append(r)

        # 指定効果を持つ遺物の ID セット
        wanted_ids: Set[int] = set()
        for r in filtered:
            if self._get_spec_keys(r):
                wanted_ids.add(r['id'])

        slot_candidates = []
        for slot_color in slot_colors:
            if slot_color == 'Any':
                candidates = filtered
            else:
                candidates = by_color.get(slot_color, [])

            # Ensure relics with wanted effects are always included
            must_include = [r for r in candidates
                           if r['id'] in wanted_ids]
            # Cap must_include to prevent unbounded candidate lists
            # (esp. for "Any" slots)
            if len(must_include) > candidates_per_slot:
                must_include.sort(
                    key=lambda r: self.score_relic(r), reverse=True)
                must_include = must_include[:candidates_per_slot]
            must_ids = {r['id'] for r in must_include}

            # Fill remaining slots with top-scored others
            others = [(self.score_relic(r), r) for r in candidates
                      if r['id'] not in must_ids]
            others.sort(key=lambda x: x[0], reverse=True)
            remaining = candidates_per_slot - len(must_include)
            if remaining > 0:
                top_others = [r for _, r in others[:remaining]]
            else:
                top_others = []

            combined = must_include + top_others
            # Sort by score descending for consistent ordering
            combined.sort(
                key=lambda r: self.score_relic(r), reverse=True)
            slot_candidates.append(combined)

        return slot_candidates

    def optimize_combined(self, normal_slot_colors: List[str],
                          deep_slot_colors: List[str],
                          normal_types: Optional[List[str]] = None,
                          deep_types: Optional[List[str]] = None,
                          character: Optional[str] = None,
                          candidates_per_slot: int = 15,
                          top_n: int = 10) -> List[Dict]:
        """通常遺物＋深層遺物の6スロット一括最適化

        全6スロット (通常3 + 深層3) の直積を列挙し、
        組み合わせ全体でスコアリングを行う。
        指定効果を持つ遺物は候補に必ず含まれる。
        """
        if normal_types is None:
            normal_types = ['Relic', 'UniqueRelic']
        if deep_types is None:
            deep_types = ['DeepRelic']

        normal_filtered = self.filter_relics(
            types=normal_types, character=character)
        deep_filtered = self.filter_relics(
            types=deep_types, character=character)

        # Build candidate lists for all 6 slots
        normal_cands = self._build_slot_candidates(
            normal_slot_colors, normal_filtered, candidates_per_slot)
        deep_cands = self._build_slot_candidates(
            deep_slot_colors, deep_filtered, candidates_per_slot)

        n_normal = len(normal_slot_colors)

        # Log candidate counts
        nc = [len(sc) for sc in normal_cands]
        dc = [len(sc) for sc in deep_cands]
        n_product = 1
        for sc in normal_cands:
            n_product *= len(sc)
        d_product = 1
        for sc in deep_cands:
            d_product *= len(sc)
        print(f"  Normal candidates: {nc} (product: {n_product})",
              file=sys.stderr)
        print(f"  Deep candidates:   {dc} (product: {d_product})",
              file=sys.stderr)

        # Phase 1: Enumerate normal combos using optimized enumeration
        # Compact format: (score, counts_tuple, conc, excl_pen,
        #                   has_excl_req, relic_ids, excl_sub_sum)
        n_cache_key = tuple(sorted(normal_slot_colors))
        if n_cache_key in self._phase_cache:
            normal_combos = self._phase_cache[n_cache_key]
        elif all(len(sc) > 0 for sc in normal_cands):
            compact_n = [[self._compact_relic(r) for r in sc]
                         for sc in normal_cands]
            normal_combos = self._enumerate_combos(
                compact_n, normal_slot_colors)
            self._phase_cache[n_cache_key] = normal_combos
        else:
            normal_combos = []

        # Phase 2: Enumerate deep combos
        d_cache_key = ('deep', tuple(sorted(deep_slot_colors)))
        if d_cache_key in self._phase_cache:
            deep_combos = self._phase_cache[d_cache_key]
        elif all(len(sc) > 0 for sc in deep_cands):
            compact_d = [[self._compact_relic(r) for r in sc]
                         for sc in deep_cands]
            deep_combos = self._enumerate_combos(
                compact_d, deep_slot_colors)
            self._phase_cache[d_cache_key] = deep_combos
        else:
            deep_combos = []

        print(f"  Normal combos: {len(normal_combos)}, "
              f"Deep combos: {len(deep_combos)}", file=sys.stderr)

        if not normal_combos and not deep_combos:
            return []

        # Sort each side by score descending
        normal_combos.sort(key=lambda x: x[0], reverse=True)
        deep_combos.sort(key=lambda x: x[0], reverse=True)

        n_spec = self._n_spec
        spec_weights = self._spec_weights
        spec_stacking_int = self._spec_stacking_int
        spec_penalty30 = self._spec_penalty30
        spec_penalty50 = self._spec_penalty50
        is_required = self._is_required
        required_idx_set = self._required_idx_set
        sub_rank_values = self._spec_sub_rank_values
        relic_by_id = self._relic_by_id
        spec_key_list = self._spec_key_list

        # Handle single-side cases
        if not normal_combos:
            return self._combos_to_results_compact(
                deep_combos[:top_n], is_deep_only=True)
        if not deep_combos:
            return self._combos_to_results_compact(
                normal_combos[:top_n], is_deep_only=False)

        # Phase 3: Cross-pair with heap-based top-N and pruning
        max_pairs = 500
        n_top = min(len(normal_combos), max_pairs)
        d_top = min(len(deep_combos), max_pairs)

        normal_top = normal_combos[:n_top]
        deep_top = deep_combos[:d_top]
        best_deep_score = deep_top[0][0] if deep_top else 0

        # Fix pruning: check if req_met=True is achievable
        req_met_bound = True
        if required_idx_set:
            possible_from_normal = set()
            for _, n_cts, _, _, _, _, _ in normal_top:
                for i in range(n_spec):
                    if n_cts[i] > 0:
                        possible_from_normal.add(i)
            possible_from_deep = set()
            for _, d_cts, _, _, _, _, _ in deep_top:
                for i in range(n_spec):
                    if d_cts[i] > 0:
                        possible_from_deep.add(i)
            possible_all = possible_from_normal | possible_from_deep
            if not required_idx_set.issubset(possible_all):
                req_met_bound = False
        if req_met_bound:
            has_n_no_excl = any(not h for _, _, _, _, h, _, _ in normal_top)
            has_d_no_excl = any(not h for _, _, _, _, h, _, _ in deep_top)
            if not (has_n_no_excl and has_d_no_excl):
                req_met_bound = False
        bound_req_int = -1 if req_met_bound else 0

        # Min-heap for top-N: heap_key = (-req_met_int, -score, counter)
        heap: list = []
        result_map: Dict[int, tuple] = {}
        counter = 0
        evaluated = 0

        for ns, n_cts, n_conc, n_ep, n_her, n_rids, n_esr in normal_top:
            # Outer pruning
            if len(heap) >= top_n:
                best_possible = (bound_req_int, -(ns + best_deep_score))
                if best_possible >= (heap[0][0], heap[0][1]):
                    break

            for ds, d_cts, d_conc, d_ep, d_her, d_rids, d_esr in deep_top:
                # Inner pruning
                if len(heap) >= top_n:
                    best_possible = (bound_req_int, -(ns + ds))
                    if best_possible >= (heap[0][0], heap[0][1]):
                        break

                # Inline merged scoring (integer stacking codes)
                score = 0
                has_all_required = True
                for i in range(n_spec):
                    c = n_cts[i] + d_cts[i]
                    if c == 0:
                        if is_required[i]:
                            has_all_required = False
                        continue
                    si = spec_stacking_int[i]
                    if si == 1:  # stackable
                        score += spec_weights[i] * c
                    elif si == 2:  # conditional
                        score += spec_weights[i]
                        if c > 1:
                            score -= spec_penalty30[i] * (c - 1)
                    else:  # non-stackable
                        score += spec_weights[i]
                        if c > 1:
                            score -= spec_penalty50[i] * (c - 1)

                score += n_conc + d_conc - n_ep - d_ep
                has_excl_req = n_her or d_her
                req_met = has_all_required and not has_excl_req

                # Sub-priority tiebreaker (include sub-rank minus exclude sub-rank)
                sub_score = 0
                for i in range(n_spec):
                    if n_cts[i] + d_cts[i] > 0:
                        sub_score += sub_rank_values[i]
                sub_score -= (n_esr + d_esr)

                evaluated += 1

                heap_key = (-int(req_met), -score, -sub_score, counter)
                # Check heap eligibility BEFORE building result
                if len(heap) < top_n:
                    heapq.heappush(heap, heap_key)
                    result_map[counter] = (
                        req_met, score, sub_score, n_cts, d_cts,
                        n_rids, d_rids)
                elif heap_key < heap[0]:
                    evicted = heapq.heapreplace(heap, heap_key)
                    del result_map[evicted[3]]
                    result_map[counter] = (
                        req_met, score, sub_score, n_cts, d_cts,
                        n_rids, d_rids)

                counter += 1

        print(f"  Pairing: {n_top} normal x {d_top} deep "
              f"(max {n_top * d_top}, evaluated {evaluated})",
              file=sys.stderr)

        # Build full results only for heap entries (lazy construction)
        results = []
        for hk in heap:
            data = result_map[hk[3]]
            req_met, score, sub_score, n_cts, d_cts, n_rids, d_rids = data
            # Reconstruct matched_keys from merged counts
            matched_keys = set()
            for i in range(n_spec):
                if n_cts[i] + d_cts[i] > 0:
                    matched_keys.add(spec_key_list[i])
            missing = sorted(
                spec_key_list[i] for i in required_idx_set
                if n_cts[i] + d_cts[i] == 0)
            # Reconstruct exclude info from relics
            excluded_present = set()
            all_rids = n_rids + d_rids
            for rid in all_rids:
                for k in self._get_exclude_keys(relic_by_id[rid]):
                    excluded_present.add(k)
            n_relics = tuple(relic_by_id[rid] for rid in n_rids)
            d_relics = tuple(relic_by_id[rid] for rid in d_rids)
            results.append({
                'required_met': req_met,
                'score': score,
                'sub_score': sub_score,
                'matched_keys': matched_keys,
                'missing_required': missing,
                'excluded_present': excluded_present,
                'relics': n_relics + d_relics,
                'normal_relics': n_relics,
                'deep_relics': d_relics,
            })
        results.sort(
            key=lambda x: (x['required_met'], x['score'],
                           x['sub_score']), reverse=True)

        print(f"  Best score: {results[0]['score']} "
              f"(required met: {results[0]['required_met']})"
              if results else "  No results", file=sys.stderr)

        return results

    def _combos_to_results_compact(self, combos, is_deep_only=False):
        """Compact combo list to result format (single-side)"""
        results = []
        spec_key_list = self._spec_key_list
        required_idx_set = self._required_idx_set
        n_spec = self._n_spec
        relic_by_id = self._relic_by_id
        for score, counts, conc, excl_pen, has_excl_req, rids, excl_sub_sum in combos:
            matched_keys = set()
            for i in range(n_spec):
                if counts[i] > 0:
                    matched_keys.add(spec_key_list[i])
            missing = sorted(
                spec_key_list[i] for i in required_idx_set
                if counts[i] == 0)
            sub_score = self._fast_sub_score(counts) - excl_sub_sum
            excluded_present = set()
            for rid in rids:
                for k in self._get_exclude_keys(relic_by_id[rid]):
                    excluded_present.add(k)
            relics = tuple(relic_by_id[rid] for rid in rids)
            if is_deep_only:
                entry = {
                    'required_met': len(missing) == 0
                        and not has_excl_req,
                    'score': score,
                    'sub_score': sub_score,
                    'matched_keys': matched_keys,
                    'missing_required': missing,
                    'excluded_present': excluded_present,
                    'relics': relics,
                    'normal_relics': (),
                    'deep_relics': relics,
                }
            else:
                entry = {
                    'required_met': len(missing) == 0
                        and not has_excl_req,
                    'score': score,
                    'sub_score': sub_score,
                    'matched_keys': matched_keys,
                    'missing_required': missing,
                    'excluded_present': excluded_present,
                    'relics': relics,
                    'normal_relics': relics,
                    'deep_relics': (),
                }
            results.append(entry)
        return results

    def optimize_legacy(self, color: Optional[str] = None,
                        types: Optional[List[str]] = None,
                        character: Optional[str] = None,
                        slots: int = 3,
                        candidates: int = 50,
                        top_n: int = 10) -> List[Dict]:
        """旧方式の最適化（色指定、献器なし）"""
        filtered = self.filter_relics(types=types, character=character,
                                      color=color)

        if len(filtered) == 0:
            return []

        scored = [(self.score_relic(r), r) for r in filtered]
        scored.sort(key=lambda x: x[0], reverse=True)
        candidate_relics = [r for _, r in scored[:candidates]]

        actual_slots = min(slots, len(candidate_relics))
        if actual_slots == 0:
            return []

        print(f"  Candidates: {len(candidate_relics)} relics, "
              f"combinations: C({len(candidate_relics)}, {actual_slots})",
              file=sys.stderr)

        results = []
        for combo in combinations(candidate_relics, actual_slots):
            req_met, score, sub_score, matched, missing, excl_present = \
                self.score_combination(combo)
            results.append({
                'required_met': req_met,
                'score': score,
                'sub_score': sub_score,
                'matched_keys': matched,
                'missing_required': missing,
                'excluded_present': excl_present,
                'relics': combo,
            })

        results.sort(key=lambda x: (x['required_met'], x['score'],
                                    x['sub_score']), reverse=True)
        return results[:top_n]

    def _format_relic(self, relic: Dict, matched_keys: Set[str],
                      excluded_keys: Optional[Set[str]] = None) -> Dict:
        """遺物1つの出力フォーマット"""
        effects_out = []
        excl_set = excluded_keys or set()
        for group in relic['effects']:
            main_eff = group[0]
            matched = main_eff['key'] in matched_keys
            excluded = main_eff['key'] in excl_set
            eff_entry = {
                'key': main_eff['key'],
                'name_ja': main_eff.get('name_ja', ''),
                'name_en': main_eff.get('name_en', ''),
                'matched': matched,
            }
            if matched and main_eff['key'] in self.effect_lookup:
                eff_entry['priority'] = \
                    self.effect_lookup[main_eff['key']]['priority']
            if excluded:
                eff_entry['excluded'] = True
                eff_entry['excludePriority'] = \
                    self.exclude_lookup[main_eff['key']]['priority']
            effects_out.append(eff_entry)
            for sub in group[1:]:
                sub_matched = sub['key'] in matched_keys
                sub_entry = {
                    'key': sub['key'],
                    'name_ja': sub.get('name_ja', ''),
                    'name_en': sub.get('name_en', ''),
                    'matched': sub_matched,
                    'isDebuff': True,
                }
                if sub_matched and sub['key'] in self.effect_lookup:
                    sub_entry['priority'] = \
                        self.effect_lookup[sub['key']]['priority']
                if sub['key'] in excl_set:
                    sub_entry['excluded'] = True
                    sub_entry['excludePriority'] = \
                        self.exclude_lookup[sub['key']]['priority']
                effects_out.append(sub_entry)

        return {
            'id': relic['id'],
            'itemKey': relic['itemKey'],
            'itemNameJa': relic.get('itemNameJa', ''),
            'itemNameEn': relic.get('itemNameEn', ''),
            'itemColor': relic.get('itemColor', ''),
            'itemType': relic.get('itemType', ''),
            'effects': effects_out,
        }

    def format_results(self, results: List[Dict],
                       vessel_info: Optional[Dict] = None,
                       **params) -> Dict:
        """出力 JSON フォーマット"""
        is_combined = params.get('combined', False)

        formatted_results = []
        for rank, res in enumerate(results, 1):
            matched_keys = res['matched_keys']
            excluded_keys = res.get('excluded_present', set())

            if is_combined and 'normal_relics' in res:
                normal_out = [self._format_relic(r, matched_keys,
                              excluded_keys)
                              for r in res['normal_relics']]
                deep_out = [self._format_relic(r, matched_keys,
                            excluded_keys)
                            for r in res['deep_relics']]
                entry = {
                    'rank': rank,
                    'score': res['score'],
                    'subScore': res.get('sub_score', 0),
                    'requiredMet': res['required_met'],
                    'normalRelics': normal_out,
                    'deepRelics': deep_out,
                    'matchedEffects': sorted(matched_keys),
                    'missingRequired': res['missing_required'],
                    'excludedPresent': sorted(excluded_keys),
                }
            else:
                relics_out = [self._format_relic(r, matched_keys,
                              excluded_keys)
                              for r in res['relics']]
                entry = {
                    'rank': rank,
                    'score': res['score'],
                    'subScore': res.get('sub_score', 0),
                    'requiredMet': res['required_met'],
                    'relics': relics_out,
                    'matchedEffects': sorted(matched_keys),
                    'missingRequired': res['missing_required'],
                    'excludedPresent': sorted(excluded_keys),
                }

            if vessel_info:
                entry['vessel'] = vessel_info
            formatted_results.append(entry)

        output = {
            'parameters': {
                'character': params.get('character'),
                'types': params.get('types', []),
                'candidates': params.get('candidates'),
                'effects': [
                    {'key': s.get('key', ''), 'name_ja': s.get('name_ja', ''),
                     'name_en': s.get('name_en', ''), 'priority': s['priority'],
                     'exclude': bool(s.get('exclude'))}
                    for s in self.effect_specs
                ],
            },
            'results': formatted_results,
        }

        if vessel_info:
            output['parameters']['vessel'] = vessel_info
            output['parameters']['deep'] = params.get('deep', False)
        elif params.get('color'):
            output['parameters']['color'] = params['color']

        return output


def _build_output(all_output: List[Dict], top_n: int = 50) -> Dict:
    """全献器の結果をマージし、グローバル上位 top_n 件に絞った出力を構築"""
    # 全献器の結果をフラットにマージ（各結果に献器情報を付与）
    flat = []
    for vessel_output in all_output:
        params = vessel_output.get('parameters', {})
        vessel_info = params.get('vessel')
        for res in vessel_output.get('results', []):
            entry = dict(res)
            if vessel_info and 'vessel' not in entry:
                entry['vessel'] = vessel_info
            elif not vessel_info and params.get('color'):
                entry['_color'] = params['color']
            flat.append(entry)

    # ソート: requiredMet 優先、次にスコア降順、次にサブスコア降順
    flat.sort(key=lambda r: (r.get('requiredMet', False), r.get('score', 0),
                              r.get('subScore', 0)),
              reverse=True)

    # グローバル top_n に絞る
    flat = flat[:top_n]

    # rank を振り直す
    for i, entry in enumerate(flat):
        entry['rank'] = i + 1

    output = {}

    if flat:
        output['bestResult'] = {
            'parameters': all_output[0].get('parameters', {}),
            'result': flat[0],
        }
        # bestResult の parameters に正しい献器情報を設定
        if flat[0].get('vessel'):
            output['bestResult']['parameters'] = dict(
                output['bestResult']['parameters'])
            output['bestResult']['parameters']['vessel'] = flat[0]['vessel']

    # allResults: フラット化した結果を献器ごとに再グループ化
    grouped = {}
    for entry in flat:
        vessel = entry.get('vessel')
        color = entry.get('_color')
        if vessel:
            group_key = vessel.get('key', '')
        elif color:
            group_key = color
        else:
            group_key = '_unknown'

        if group_key not in grouped:
            # 元の parameters を見つける
            src_params = {}
            for vo in all_output:
                p = vo.get('parameters', {})
                v = p.get('vessel')
                if vessel and v and v.get('key') == group_key:
                    src_params = p
                    break
                elif color and p.get('color') == color:
                    src_params = p
                    break
            grouped[group_key] = {
                'parameters': src_params,
                'results': [],
            }
        grouped[group_key]['results'].append(entry)

    output['allResults'] = list(grouped.values())

    return output


def main():
    parser = argparse.ArgumentParser(
        description='遺物組み合わせ最適化ツール - Relic Combination Optimizer')
    parser.add_argument('--input', required=True,
                        help='relic_parser 出力の JSON ファイル')
    parser.add_argument('-o', '--output', default='combinations.json',
                        help='出力 JSON ファイル (default: combinations.json)')
    parser.add_argument('--character', default=None,
                        help='キャラクター名 (例: 追跡者, Wylder)')
    parser.add_argument('--vessel', default=None,
                        help='献器タイプ, カンマ区切り '
                             '(例: urn,chalice,goblet,sootCoveredUrn,'
                             'sealedUrn,decrepitGoblet,forgottenGoblet)')
    parser.add_argument('--deep', action='store_true',
                        help='深層遺物スロットを使用')
    parser.add_argument('--combined', action='store_true',
                        help='通常遺物3つ＋深層遺物3つの組み合わせ最適化')
    parser.add_argument('--color', default=None,
                        help='遺物の色 - 献器未使用時 (Red, Blue, Yellow, Green)')
    parser.add_argument('--types', default='Relic',
                        help='許可する遺物タイプ, カンマ区切り (default: Relic)')
    parser.add_argument('--effects', default=None,
                        help='効果指定ファイル (JSON)')
    parser.add_argument('--vessels-data', default=None,
                        help='献器データファイル '
                             '(default: resources/vessels_data.json)')
    parser.add_argument('--top', type=int, default=10,
                        help='献器あたりの出力候補数 (default: 10)')
    parser.add_argument('--candidates', type=int, default=30,
                        help='スロットあたりの候補数 (default: 30)')

    args = parser.parse_args()

    # Load relic data
    print(f"Loading relic data from: {args.input}", file=sys.stderr)
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    relics = data.get('relics', [])
    print(f"Total relics: {len(relics)}", file=sys.stderr)

    # Load effects config
    effect_specs = []
    if args.effects:
        print(f"Loading effects config from: {args.effects}", file=sys.stderr)
        effect_specs = load_effects_config(args.effects)
        print(f"Effect specifications: {len(effect_specs)}", file=sys.stderr)

    # Load vessels data
    vessels_file = args.vessels_data
    if not vessels_file:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        vessels_file = os.path.join(script_dir, '..', 'resources',
                                    'vessels_data.json')

    vessels_data = None
    if os.path.exists(vessels_file):
        print(f"Loading vessels data from: {vessels_file}", file=sys.stderr)
        vessels_data = load_vessels_data(vessels_file)
    else:
        print(f"Warning: Vessels data not found at {vessels_file}",
              file=sys.stderr)

    # Parse types
    types = [t.strip() for t in args.types.split(',')]

    # Parse vessel types
    vessel_types = None
    if args.vessel:
        vessel_types = [v.strip() for v in args.vessel.split(',')]

    # Load stacking data
    stacking_data = None
    effects_data_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'resources', 'effects_data.json')
    if os.path.exists(effects_data_file):
        print(f"Loading stacking data from: {effects_data_file}",
              file=sys.stderr)
        stacking_data = load_stacking_data(effects_data_file)
        n_stackable = sum(1 for v in stacking_data.values() if v)
        print(f"  Effects with stacking info: {len(stacking_data)} "
              f"({n_stackable} stackable)", file=sys.stderr)

    # Create optimizer
    optimizer = RelicOptimizer(relics, effect_specs, vessels_data,
                               stacking_data)

    # Vessel-aware mode (character specified + vessels data available)
    if args.character and vessels_data:
        vessel_configs = optimizer.get_vessel_configs(
            args.character, vessel_types=vessel_types, deep=args.deep)

        if not vessel_configs:
            print(f"No vessel configs found for {args.character}",
                  file=sys.stderr)
            sys.exit(1)

        all_output = []
        total_vessels = len(vessel_configs)
        for vi, vc in enumerate(vessel_configs):
            print(f"PROGRESS:{vi}/{total_vessels}", file=sys.stderr, flush=True)
            print(f"\nOptimizing for vessel: {vc['nameJa']} "
                  f"({vc['nameEn']})", file=sys.stderr)

            vessel_info = {
                'key': vc['key'],
                'nameJa': vc['nameJa'],
                'nameEn': vc['nameEn'],
            }

            if args.combined:
                # Combined mode: normal 3 + deep 3
                normal_slots = vc['normalSlots']
                deep_slots = vc['deepSlots']
                print(f"  Normal slots: {normal_slots}", file=sys.stderr)
                print(f"  Deep slots:   {deep_slots}", file=sys.stderr)
                vessel_info['normalSlots'] = normal_slots
                vessel_info['deepSlots'] = deep_slots

                results = optimizer.optimize_combined(
                    normal_slot_colors=normal_slots,
                    deep_slot_colors=deep_slots,
                    character=args.character,
                    candidates_per_slot=args.candidates,
                    top_n=args.top,
                )

                formatted = optimizer.format_results(
                    results, vessel_info=vessel_info,
                    character=args.character, types=['Relic', 'DeepRelic'],
                    candidates=args.candidates, combined=True,
                )
            else:
                # Single mode (normal or deep)
                print(f"  Slots: {vc['slots']}", file=sys.stderr)
                vessel_info['slots'] = vc['slots']

                results = optimizer.optimize_for_vessel(
                    slot_colors=vc['slots'],
                    types=types,
                    character=args.character,
                    candidates_per_slot=args.candidates,
                    top_n=args.top,
                )

                formatted = optimizer.format_results(
                    results, vessel_info=vessel_info,
                    character=args.character, types=types,
                    candidates=args.candidates, deep=args.deep,
                )

            all_output.append(formatted)

            n = len(results)
            if n > 0:
                best = results[0]
                print(f"  Results: {n}, Top score: {best['score']} "
                      f"(required met: {best['required_met']})",
                      file=sys.stderr)
            else:
                print(f"  No combinations found", file=sys.stderr)

        print(f"PROGRESS:{total_vessels}/{total_vessels}", file=sys.stderr,
              flush=True)
        output_data = _build_output(all_output, top_n=args.top)

    else:
        # Legacy mode: color-based optimization (no vessel constraints)
        colors = [args.color] if args.color else \
            ['Red', 'Blue', 'Yellow', 'Green']
        all_output = []
        total_colors = len(colors)
        for ci, color in enumerate(colors):
            print(f"PROGRESS:{ci}/{total_colors}", file=sys.stderr, flush=True)
            print(f"\nOptimizing for color: {color}", file=sys.stderr)
            results = optimizer.optimize_legacy(
                color=color, types=types, character=args.character,
                slots=3, candidates=args.candidates, top_n=args.top,
            )
            formatted = optimizer.format_results(
                results, character=args.character, color=color,
                types=types, candidates=args.candidates,
            )
            all_output.append(formatted)
            n = len(results)
            if n > 0:
                best = results[0]
                print(f"  Top score: {best['score']} "
                      f"(required met: {best['required_met']})",
                      file=sys.stderr)
            else:
                print(f"  No combinations found", file=sys.stderr)

        print(f"PROGRESS:{total_colors}/{total_colors}", file=sys.stderr,
              flush=True)
        output_data = _build_output(all_output, top_n=args.top)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f"\nResults written to: {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
