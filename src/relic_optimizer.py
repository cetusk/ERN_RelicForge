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
from itertools import combinations, product
from typing import List, Dict, Set, Tuple, Optional


# === Priority weights ===
PRIORITY_WEIGHTS = {
    'required': 100,
    'preferred': 10,
    'nice_to_have': 1,
}

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


def load_stacking_data(effects_data_file: str) -> Dict[str, bool]:
    """効果の重複可否データを読み込み

    effects_data.json から各効果キーの stackable 値を取得。
    同じキーが複数のエフェクト ID に存在する場合、
    いずれかが True なら True とする。
    """
    with open(effects_data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    key_stackable: Dict[str, bool] = {}
    for eid, entry in data.get('effects', {}).items():
        key = entry['key']
        stackable = entry.get('stackable', False)
        if key not in key_stackable:
            key_stackable[key] = (stackable is True)
        elif stackable is True:
            key_stackable[key] = True
    return key_stackable


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
                 stacking_data: Optional[Dict[str, bool]] = None):
        self.all_relics = relics
        self.effect_specs = effect_specs
        self.vessels_data = vessels_data
        self.stacking_data: Dict[str, bool] = stacking_data or {}

        # Build effect lookup: key -> { priority, weight }
        self.effect_lookup: Dict[str, Dict] = {}
        for spec in effect_specs:
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
                self._resolve_name_matches(name_ja, name_en, spec, weight)

    def _resolve_name_matches(self, name_ja: Optional[str], name_en: Optional[str],
                               spec: Dict, weight: int):
        """Resolve name_ja/name_en partial matches to effect keys from relic data"""
        for relic in self.all_relics:
            for group in relic['effects']:
                for eff in group:
                    matched = False
                    if name_ja and name_ja in eff.get('name_ja', ''):
                        matched = True
                    if name_en and name_en.lower() in eff.get('name_en', '').lower():
                        matched = True
                    if matched and eff['key'] not in self.effect_lookup:
                        self.effect_lookup[eff['key']] = {
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

        if character:
            char_ja = resolve_character_name_ja(character)

            def has_other_char_effect(relic):
                for group in relic['effects']:
                    main_eff = group[0]
                    name = main_eff.get('name_ja', '')
                    m = re.match(r'【(.+?)】', name)
                    if m and m.group(1) != char_ja:
                        return True
                return False

            filtered = [r for r in filtered if not has_other_char_effect(r)]

        return filtered

    def get_relic_effect_keys(self, relic: Dict) -> Set[str]:
        """遺物のメイン効果キーを取得（デバフ副効果は除外）"""
        keys = set()
        for group in relic['effects']:
            if group:
                keys.add(group[0]['key'])
        return keys

    def is_stackable(self, key: str) -> bool:
        """効果がスタック可能かどうか（重複装備で恩恵があるか）"""
        return self.stacking_data.get(key, False)

    def score_relic(self, relic: Dict) -> int:
        """個別遺物のスコア計算"""
        score = 0
        for key in self.get_relic_effect_keys(relic):
            if key in self.effect_lookup:
                score += self.effect_lookup[key]['weight']
        return score

    def _stacking_aware_score(self, effect_counts: Dict[str, int]) -> int:
        """重複可否を考慮したスコア計算

        スタック可能な効果: weight × 遺物数（重複分の恩恵あり）
        スタック不可な効果: weight × 1（重複しても1回分のみ）
        """
        score = 0
        for key, count in effect_counts.items():
            if key not in self.effect_lookup:
                continue
            weight = self.effect_lookup[key]['weight']
            if self.is_stackable(key):
                score += weight * count
            else:
                score += weight  # 1回のみカウント
        return score

    def score_combination(self, combo: Tuple[Dict, ...]) -> Tuple[bool, int, Set[str], List[str]]:
        """組み合わせのスコア計算（重複可否を考慮）

        スタック可能な効果は遺物ごとにカウントし、
        スタック不可な効果は1回のみカウントする。
        """
        effect_counts: Dict[str, int] = {}
        seen_ids = set()
        for relic in combo:
            rid = relic['id']
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            for key in self.get_relic_effect_keys(relic):
                if key in self.effect_lookup:
                    effect_counts[key] = effect_counts.get(key, 0) + 1

        score = self._stacking_aware_score(effect_counts)

        matched_keys = set(effect_counts.keys())
        required_keys = {
            k for k, v in self.effect_lookup.items()
            if v['priority'] == 'required'
        }
        missing_required = sorted(required_keys - matched_keys)
        required_met = len(missing_required) == 0

        return required_met, score, matched_keys, missing_required

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

            req_met, score, matched, missing = self.score_combination(combo)
            results.append({
                'required_met': req_met,
                'score': score,
                'matched_keys': matched,
                'missing_required': missing,
                'relics': combo,
            })

        results.sort(key=lambda x: (x['required_met'], x['score']), reverse=True)
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
            for key in self.get_relic_effect_keys(r):
                if key in self.effect_lookup:
                    wanted_ids.add(r['id'])
                    break

        slot_candidates = []
        for slot_color in slot_colors:
            if slot_color == 'Any':
                candidates = filtered
            else:
                candidates = by_color.get(slot_color, [])

            # Ensure relics with wanted effects are always included
            must_include = [r for r in candidates
                           if r['id'] in wanted_ids]
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

        # Phase 1: Enumerate normal combos (3 slots)
        normal_combos = []
        seen_n = set()
        if all(len(sc) > 0 for sc in normal_cands):
            for combo in product(*normal_cands):
                ids = tuple(r['id'] for r in combo)
                if len(set(ids)) != n_normal:
                    continue
                canon = tuple(sorted(ids))
                if canon in seen_n:
                    continue
                seen_n.add(canon)
                effect_counts: Dict[str, int] = {}
                for r in combo:
                    for k in self.get_relic_effect_keys(r):
                        if k in self.effect_lookup:
                            effect_counts[k] = \
                                effect_counts.get(k, 0) + 1
                score = self._stacking_aware_score(effect_counts)
                keys = set(effect_counts.keys())
                normal_combos.append((score, keys, combo))

        # Phase 2: Enumerate deep combos (3 slots)
        deep_combos = []
        seen_d = set()
        n_deep = len(deep_slot_colors)
        if all(len(sc) > 0 for sc in deep_cands):
            for combo in product(*deep_cands):
                ids = tuple(r['id'] for r in combo)
                if len(set(ids)) != n_deep:
                    continue
                canon = tuple(sorted(ids))
                if canon in seen_d:
                    continue
                seen_d.add(canon)
                effect_counts: Dict[str, int] = {}
                for r in combo:
                    for k in self.get_relic_effect_keys(r):
                        if k in self.effect_lookup:
                            effect_counts[k] = \
                                effect_counts.get(k, 0) + 1
                score = self._stacking_aware_score(effect_counts)
                keys = set(effect_counts.keys())
                deep_combos.append((score, keys, combo))

        print(f"  Normal combos: {len(normal_combos)}, "
              f"Deep combos: {len(deep_combos)}", file=sys.stderr)

        if not normal_combos and not deep_combos:
            return []

        # Sort each side by score descending
        normal_combos.sort(key=lambda x: x[0], reverse=True)
        deep_combos.sort(key=lambda x: x[0], reverse=True)

        # Handle single-side cases
        if not normal_combos:
            return self._combos_to_results(
                [(s, k, (), c) for s, k, c in deep_combos[:top_n]])
        if not deep_combos:
            return self._combos_to_results(
                [(s, k, c, ()) for s, k, c in normal_combos[:top_n]])

        # Phase 3: Cross-pair with pruning
        # Take generous top from each side for pairing
        max_pairs = 500
        n_top = min(len(normal_combos), max_pairs)
        d_top = min(len(deep_combos), max_pairs)
        print(f"  Pairing: {n_top} normal x {d_top} deep = "
              f"{n_top * d_top} pairs", file=sys.stderr)

        required_keys = {
            k for k, v in self.effect_lookup.items()
            if v['priority'] == 'required'
        }

        results = []
        for ns, nkeys, ncombo in normal_combos[:n_top]:
            for ds, dkeys, dcombo in deep_combos[:d_top]:
                # 全6遺物から効果カウントを再計算
                effect_counts: Dict[str, int] = {}
                for r in list(ncombo) + list(dcombo):
                    for k in self.get_relic_effect_keys(r):
                        if k in self.effect_lookup:
                            effect_counts[k] = \
                                effect_counts.get(k, 0) + 1
                score = self._stacking_aware_score(effect_counts)
                matched = set(effect_counts.keys())
                missing = sorted(required_keys - matched)
                req_met = len(missing) == 0

                results.append({
                    'required_met': req_met,
                    'score': score,
                    'matched_keys': matched,
                    'missing_required': missing,
                    'relics': tuple(ncombo) + tuple(dcombo),
                    'normal_relics': ncombo,
                    'deep_relics': dcombo,
                })

        results.sort(
            key=lambda x: (x['required_met'], x['score']), reverse=True)

        print(f"  Best score: {results[0]['score']} "
              f"(required met: {results[0]['required_met']})"
              if results else "  No results", file=sys.stderr)

        return results[:top_n]

    def _combos_to_results(self, items):
        """Single-side combo list to result format"""
        results = []
        for score, keys, ncombo, dcombo in items:
            matched = {k for k in keys if k in self.effect_lookup}
            required_keys = {
                k for k, v in self.effect_lookup.items()
                if v['priority'] == 'required'
            }
            missing = sorted(required_keys - matched)
            results.append({
                'required_met': len(missing) == 0,
                'score': score,
                'matched_keys': matched,
                'missing_required': missing,
                'relics': tuple(ncombo) + tuple(dcombo),
                'normal_relics': ncombo,
                'deep_relics': dcombo,
            })
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
            req_met, score, matched, missing = self.score_combination(combo)
            results.append({
                'required_met': req_met,
                'score': score,
                'matched_keys': matched,
                'missing_required': missing,
                'relics': combo,
            })

        results.sort(key=lambda x: (x['required_met'], x['score']), reverse=True)
        return results[:top_n]

    def _format_relic(self, relic: Dict, matched_keys: Set[str]) -> Dict:
        """遺物1つの出力フォーマット"""
        effects_out = []
        for group in relic['effects']:
            main_eff = group[0]
            matched = main_eff['key'] in matched_keys
            eff_entry = {
                'key': main_eff['key'],
                'name_ja': main_eff.get('name_ja', ''),
                'name_en': main_eff.get('name_en', ''),
                'matched': matched,
            }
            if matched and main_eff['key'] in self.effect_lookup:
                eff_entry['priority'] = \
                    self.effect_lookup[main_eff['key']]['priority']
            effects_out.append(eff_entry)
            for sub in group[1:]:
                effects_out.append({
                    'key': sub['key'],
                    'name_ja': sub.get('name_ja', ''),
                    'name_en': sub.get('name_en', ''),
                    'matched': False,
                    'isDebuff': True,
                })

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

            if is_combined and 'normal_relics' in res:
                normal_out = [self._format_relic(r, matched_keys)
                              for r in res['normal_relics']]
                deep_out = [self._format_relic(r, matched_keys)
                            for r in res['deep_relics']]
                entry = {
                    'rank': rank,
                    'score': res['score'],
                    'requiredMet': res['required_met'],
                    'normalRelics': normal_out,
                    'deepRelics': deep_out,
                    'matchedEffects': sorted(matched_keys),
                    'missingRequired': res['missing_required'],
                }
            else:
                relics_out = [self._format_relic(r, matched_keys)
                              for r in res['relics']]
                entry = {
                    'rank': rank,
                    'score': res['score'],
                    'requiredMet': res['required_met'],
                    'relics': relics_out,
                    'matchedEffects': sorted(matched_keys),
                    'missingRequired': res['missing_required'],
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
                     'name_en': s.get('name_en', ''), 'priority': s['priority']}
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


def _build_output(all_output: List[Dict]) -> Dict:
    """bestResult（最高スコア）と allResults（全結果）に分離した出力を構築"""
    # 全献器/色の結果から最高スコアの結果を選出
    best_result = None
    best_score = -1
    best_required_met = False

    for vessel_output in all_output:
        results = vessel_output.get('results', [])
        if not results:
            continue
        top = results[0]
        top_req = top.get('requiredMet', False)
        top_score = top.get('score', 0)
        # required 充足 > スコア の優先順
        if ((top_req and not best_required_met) or
            (top_req == best_required_met and top_score > best_score)):
            best_required_met = top_req
            best_score = top_score
            best_result = vessel_output

    output = {}

    if best_result:
        # bestResult: 最高スコアの献器/色の先頭結果のみ
        best_entry = {
            'parameters': best_result['parameters'],
            'result': best_result['results'][0],
        }
        output['bestResult'] = best_entry

    # allResults: 全献器/色の全結果
    output['allResults'] = all_output

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
        for vc in vessel_configs:
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

        output_data = _build_output(all_output)

    else:
        # Legacy mode: color-based optimization (no vessel constraints)
        colors = [args.color] if args.color else \
            ['Red', 'Blue', 'Yellow', 'Green']
        all_output = []
        for color in colors:
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

        output_data = _build_output(all_output)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f"\nResults written to: {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
