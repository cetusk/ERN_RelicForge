/**
 * Build suggestion (experimental) — turn what the player wants (character, weapons, playstyles,
 * a 火力↔生存 slider, optionally a known build) into build-search conditions.
 *
 * The search itself is the regular build search (relic-optimizer.js); this file only decides which
 * effects to ask for and how strongly. Rules (agreed with the owner, see resources/build_suggest.json):
 *   type tiers   core → preferred, good / opt → nice_to_have, avoid → exclude
 *   known build  must → required (effects that define it), rec → preferred, opt → nice_to_have, avoid → exclude
 *   staples      character-wide staples: rec → preferred, opt → nice_to_have, avoid → exclude
 *   weapons      「○○の攻撃力上昇」 → preferred; 3つ以上装備 / 潜在する力 → nice_to_have.
 *                Weapon-type effects that come with a type or the staples are used only for the
 *                weapon types the player picked (a type lists several weapons; the rest is noise)
 *   slider       火力 side: generic offense → preferred; 生存 side: generic survival → preferred
 *   demerits     deep demerits the wiki says to avoid → exclude (normal + deep mode only)
 * An effect wanted by one choice and avoided by another is kept (wanted wins) and reported as a conflict.
 * Unreleased effects are never used (spoilers); deep-only effects are dropped in normal-only mode;
 * effects for another character (「【キャラ名】…」) are dropped because they do nothing for the chosen one.
 */

const SUGGEST_LEVELS = ['required', 'preferred', 'nice_to_have'];

/**
 * @param {object} data   resources/build_suggest.json
 * @param {object} input  { character, mode: 'combined'|'normal', weapons: [], types: [], focus: -2..2, buildId }
 * @param {object} effectInfo  effect key -> { unreleased, deepOnly, character } (see suggestEffectInfo)
 * @returns {{effects: Array, conflicts: Array, notOnRelics: Array, unknown: Array}}
 *   effects: [{ key, priority, exclude, reasons: [label] }] in rank order (most important first)
 */
function suggestConditions(data, input, effectInfo) {
  const wanted = new Map();    // key -> { level (index in SUGGEST_LEVELS), order, reasons }
  const avoided = new Map();   // key -> { order, reasons }
  const unknown = [];
  let order = 0;
  const usable = (key) => {
    const info = effectInfo[key];
    if (!info || info.unreleased) return false;
    if (info.character && info.character !== input.character) return false;
    return !(input.mode === 'normal' && info.deepOnly);
  };
  const want = (keys, level, reason) => {
    for (const key of keys || []) {
      if (!usable(key)) continue;
      const lv = SUGGEST_LEVELS.indexOf(level);
      const cur = wanted.get(key);
      if (!cur) {
        wanted.set(key, { level: lv, order: order++, reasons: [reason] });
      } else {
        if (lv < cur.level) { cur.level = lv; cur.order = order++; }
        if (!cur.reasons.includes(reason)) cur.reasons.push(reason);
      }
    }
  };
  const avoid = (keys, reason) => {
    for (const key of keys || []) {
      if (!usable(key)) continue;
      const cur = avoided.get(key);
      if (!cur) avoided.set(key, { order: order++, reasons: [reason] });
      else if (!cur.reasons.includes(reason)) cur.reasons.push(reason);
    }
  };

  const typeById = new Map((data.types || []).map((t) => [t.id, t]));
  const types = [];
  for (const id of input.types || []) {
    const t = typeById.get(id);
    if (t) types.push(t);
    else unknown.push(id);
  }
  const weaponById = new Map((data.weapons || []).map((w) => [w.id, w]));
  const weapons = (input.weapons || []).map((id) => weaponById.get(id) || (unknown.push(id), null)).filter(Boolean);
  const weaponOf = new Map();
  for (const w of data.weapons || []) for (const k of [...w.attack, ...w.three, ...w.find]) weaponOf.set(k, w.id);
  const picked = new Set(weapons.map((w) => w.id));
  const onlyPickedWeapons = (keys) => (keys || []).filter((k) => !weaponOf.has(k) || picked.has(weaponOf.get(k)));
  const build = input.buildId ? (data.builds || []).find((b) => b.id === input.buildId) : null;
  if (input.buildId && !build) unknown.push(input.buildId);
  const staples = (data.staples || {})[input.character];
  const focus = Math.max(-2, Math.min(2, Number(input.focus) || 0));
  const generic = data.generic || {};

  // Add in importance order so that the rank inside each priority follows it
  if (build) want(build.must, 'required', build.name);
  if (build) want(build.rec, 'preferred', build.name);
  if (staples) want(onlyPickedWeapons(staples.rec), 'preferred', `${input.character}の定番`);
  for (const t of types) want(onlyPickedWeapons(t.core), 'preferred', t.id);
  for (const w of weapons) want(w.attack, 'preferred', w.id);
  if (focus < 0) want(generic.offense, 'preferred', '火力重視');
  if (focus > 0) want(generic.survival, 'preferred', '生存重視');
  if (build) want(build.opt, 'nice_to_have', build.name);
  for (const t of types) want(onlyPickedWeapons(t.good), 'nice_to_have', t.id);
  for (const w of weapons) want([...w.three, ...w.find], 'nice_to_have', w.id);
  if (staples) want(onlyPickedWeapons(staples.opt), 'nice_to_have', `${input.character}の定番`);
  for (const t of types) want(onlyPickedWeapons(t.opt), 'nice_to_have', t.id);
  if (focus === 0) {
    want(generic.offense, 'nice_to_have', '火力');
    want(generic.survival, 'nice_to_have', '生存');
  } else if (Math.abs(focus) === 1) {
    want(focus < 0 ? generic.survival : generic.offense, 'nice_to_have', focus < 0 ? '生存' : '火力');
  }

  if (build) avoid(build.avoid, build.name);
  if (staples) avoid(staples.avoid, `${input.character}の定番`);
  for (const t of types) avoid(t.avoid, t.id);
  if (input.mode !== 'normal') avoid((data.demerits || {}).avoid, '避けたい深層デメリット');

  const effects = [];
  const conflicts = [];
  for (const [key, w] of wanted) {
    const a = avoided.get(key);
    if (a) conflicts.push({ key, wantedBy: w.reasons, avoidedBy: a.reasons });
    effects.push({ key, priority: SUGGEST_LEVELS[w.level], exclude: false, reasons: w.reasons, _l: w.level, _o: w.order });
  }
  for (const [key, a] of avoided) {
    if (!wanted.has(key)) {
      effects.push({ key, priority: 'nice_to_have', exclude: true, reasons: a.reasons, _l: 3, _o: a.order });
    }
  }
  effects.sort((x, y) => x._l - y._l || x._o - y._o);
  for (const e of effects) { delete e._l; delete e._o; }

  const notOnRelics = [];
  for (const t of types) {
    for (const name of t.notOnRelics || []) {
      if (!notOnRelics.some((n) => n.name === name)) notOnRelics.push({ name, type: t.id });
    }
  }
  return { effects, conflicts, notOnRelics, unknown };
}

/**
 * effect key -> { unreleased, deepOnly, character }
 *   unreleased: every relic id of the key is marked; deepOnly: any id is marked (same rule as the app's lists);
 *   character: the character in 「【キャラ名】…」 for character-specific effects
 */
function suggestEffectInfo(effectsData) {
  const info = {};
  for (const [id, e] of Object.entries((effectsData && effectsData.effects) || {})) {
    const n = Number(id);
    if (!(n < 200000 || (n >= 6000000 && n < 7400000))) continue;   // relic effects only
    const cur = info[e.key];
    const m = /^【(.+?)】/.exec(e.name_ja || '');
    if (!cur) info[e.key] = { unreleased: !!e.unreleased, deepOnly: !!e.deepOnly, character: m ? m[1] : '' };
    else {
      cur.unreleased = cur.unreleased && !!e.unreleased;
      cur.deepOnly = cur.deepOnly || !!e.deepOnly;   // the app treats a kind as deep-only if any id is marked
    }
  }
  return info;
}
