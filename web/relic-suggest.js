/**
 * Build suggestion (experimental) — turn what the player wants (character, weapons, playstyles,
 * a 火力↔生存 slider, optionally a known build) into build-search conditions.
 *
 * The search itself is the regular build search (relic-optimizer.js); this file only decides which
 * effects to ask for and how strongly. Rules (agreed with the owner, see resources/build_suggest.json):
 *   type tiers   core → preferred, good / opt → nice_to_have, avoid → exclude
 *   known build  must → required (effects that define it), rec → preferred, opt → nice_to_have, avoid → exclude
 *   staples      character-wide staples: rec → preferred, opt → nice_to_have, avoid → exclude
 *   weapons      「○○の攻撃力上昇」 → preferred; 3つ以上装備 → nice_to_have.
 *                Weapon-type effects that come with a type or the staples are used only for the
 *                weapon types the player picked (a type lists several weapons; the rest is noise)
 *   find         「潜在する力から、○○を見つけやすくなる」 replaces the type the character finds more
 *                often (favoredWeapons): for the first picked type that is not favoured → preferred, other
 *                picked types → nice_to_have (only one works: the leftmost relic's). For a favoured type it
 *                does nothing and is not used, except to narrow a character with several favoured types
 *   slider       火力 side: generic offense → preferred; 生存 side: generic survival → preferred
 *   mode         封牢バフ vs 侵入バフ (modePreference): the one that suits the mode (通常のみ = 通常モード,
 *                通常+深層 = 深き夜) gets the better of the two levels, the other one a level lower
 *   demerits     deep demerits the wiki says to avoid → exclude (normal + deep mode only)
 *   character    per-character evaluations (characters[name]): demerits this character should avoid →
 *                exclude (wiki body text: preferred weight, agreeing comments: nice_to_have); effects that
 *                do not work for this character (useless) are not used at all
 * An effect wanted by one choice and avoided by another is kept (wanted wins) and reported as a conflict.
 * Unreleased effects are never used (spoilers); deep-only effects are dropped in normal-only mode;
 * effects for another character (「【キャラ名】…」) are dropped because they do nothing for the chosen one.
 */

const SUGGEST_LEVELS = ['required', 'preferred', 'nice_to_have'];

/**
 * @param {object} data   resources/build_suggest.json
 * @param {object} input  { character, mode: 'combined'|'normal', weapons: [], types: [], focus: -2..2, buildId }
 * @param {object} effectInfo  effect key -> { unreleased, deepOnly, character } (see suggestEffectInfo)
 * @returns {{effects: Array, conflicts: Array, notOnRelics: Array, notes: Array, unknown: Array}}
 *   effects: [{ key, priority, exclude, reasons: [label] }] in rank order (most important first)
 *   notes: [{ kind: 'findFavored' | 'findReplaces' | 'findOnlyOne' | 'mode' | 'character', ... }] for the screen to explain
 */
function suggestConditions(data, input, effectInfo) {
  const wanted = new Map();    // key -> { level (index in SUGGEST_LEVELS), order, reasons }
  const avoided = new Map();   // key -> { order, reasons }
  const unknown = [];
  let order = 0;
  const charRules = (data.characters || {})[input.character] || { avoid: [], useless: [] };
  const useless = new Set(charRules.useless.map((x) => x.key));
  const favored = new Set(((data.favoredWeapons || {})[input.character]) || []);
  const findOf = new Map();   // 「見つけやすくなる」 key -> weapon type
  for (const w of data.weapons || []) for (const k of w.find) findOf.set(k, w.id);
  const usable = (key) => {
    const info = effectInfo[key];
    if (!info || info.unreleased) return false;
    if (info.character && info.character !== input.character) return false;
    if (useless.has(key)) return false;
    // a favoured type is found more often already; the effect only helps to narrow several down to one
    if (findOf.has(key) && favored.has(findOf.get(key)) && favored.size < 2) return false;
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
  const avoid = (keys, reason, level = 'nice_to_have') => {
    for (const key of keys || []) {
      if (!usable(key)) continue;
      const lv = SUGGEST_LEVELS.indexOf(level);
      const cur = avoided.get(key);
      if (!cur) avoided.set(key, { level: lv, order: order++, reasons: [reason] });
      else {
        if (lv < cur.level) cur.level = lv;
        if (!cur.reasons.includes(reason)) cur.reasons.push(reason);
      }
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
  const others = weapons.filter((w) => !favored.has(w.id));   // picked types the character does not find often
  const notes = [];

  // Add in importance order so that the rank inside each priority follows it
  if (build) want(build.must, 'required', build.name);
  if (build) want(build.rec, 'preferred', build.name);
  if (staples) want(onlyPickedWeapons(staples.rec), 'preferred', `${input.character}の定番`);
  for (const t of types) want(onlyPickedWeapons(t.core), 'preferred', t.id);
  for (const w of weapons) want(w.attack, 'preferred', w.id);
  if (others.length) want(others[0].find, 'preferred', `${others[0].id}を出やすく`);
  if (focus < 0) want(generic.offense, 'preferred', '火力重視');
  if (focus > 0) want(generic.survival, 'preferred', '生存重視');
  if (build) want(build.opt, 'nice_to_have', build.name);
  for (const t of types) want(onlyPickedWeapons(t.good), 'nice_to_have', t.id);
  for (const w of weapons) want(w === others[0] ? w.three : [...w.three, ...w.find], 'nice_to_have', w.id);
  if (staples) want(onlyPickedWeapons(staples.opt), 'nice_to_have', `${input.character}の定番`);
  for (const t of types) want(onlyPickedWeapons(t.opt), 'nice_to_have', t.id);
  if (focus === 0) {
    want(generic.offense, 'nice_to_have', '火力');
    want(generic.survival, 'nice_to_have', '生存');
  } else if (Math.abs(focus) === 1) {
    want(focus < 0 ? generic.survival : generic.offense, 'nice_to_have', focus < 0 ? '生存' : '火力');
  }

  // Only one 「見つけやすくなる」 works: keep one above nice_to_have (the first one in rank order)
  const finds = [...wanted].filter(([k, w]) => findOf.has(k) && w.level === 1).sort((x, y) => x[1].order - y[1].order);
  for (const [, w] of finds.slice(1)) w.level = 2;
  const favoredPicked = weapons.filter((w) => favored.has(w.id)).map((w) => w.id);
  if (favoredPicked.length && favored.size < 2) notes.push({ kind: 'findFavored', weapons: favoredPicked });
  if (others.length && favoredPicked.length && others[0].find.some((k) => wanted.has(k))) {
    notes.push({ kind: 'findReplaces', weapon: others[0].id, favored: [...favored] });
  }
  if (others.length > 1) notes.push({ kind: 'findOnlyOne', first: others[0].id, rest: others.slice(1).map((w) => w.id) });

  // 封牢バフ vs 侵入バフ by mode: the one that suits the mode goes first, the other one a level lower
  const pref = (data.modePreference || {})[input.mode === 'normal' ? 'normal' : 'combined'];
  if (pref) {
    const first = pref.first.filter(usable);
    const second = pref.second.filter(usable);
    const touched = [...first, ...second].filter((k) => wanted.has(k));
    if (first.length && touched.length) {
      const top = Math.max(1, Math.min(...touched.map((k) => wanted.get(k).level)));   // never makes one required
      const ord = Math.min(...touched.map((k) => wanted.get(k).order));
      want(first, SUGGEST_LEVELS[top], `${pref.label}で優先`);
      for (const k of first) {
        const w = wanted.get(k);
        if (w.level === top) w.order = ord - 0.5;
      }
      for (const k of second) {
        const w = wanted.get(k);
        if (!w || w.level === 0) continue;
        w.level = Math.min(2, Math.max(w.level, top + 1));
        w.reasons.push(`${pref.label}では控えめ`);
      }
      notes.push({ kind: 'mode', mode: pref.label, first, second });
    }
  }

  if (build) avoid(build.avoid, build.name);
  if (staples) avoid(staples.avoid, `${input.character}の定番`);
  for (const t of types) avoid(t.avoid, t.id);
  if (input.mode !== 'normal') {
    avoid((data.demerits || {}).avoid, '避けたい深層デメリット');
    for (const x of charRules.avoid) avoid([x.key], `${input.character}: ${x.why}`, x.priority);
  }

  const effects = [];
  const conflicts = [];
  for (const [key, w] of wanted) {
    const a = avoided.get(key);
    if (a) conflicts.push({ key, wantedBy: w.reasons, avoidedBy: a.reasons });
    effects.push({ key, priority: SUGGEST_LEVELS[w.level], exclude: false, reasons: w.reasons, _l: w.level, _o: w.order });
  }
  for (const [key, a] of avoided) {
    if (!wanted.has(key)) {
      effects.push({ key, priority: SUGGEST_LEVELS[a.level], exclude: true, reasons: a.reasons, _l: 3 + a.level, _o: a.order });
    }
  }
  effects.sort((x, y) => x._l - y._l || x._o - y._o);
  // per-character exclusions that made it into the conditions (the screen explains them briefly); none in
  // normal mode, where they are not applied (a key avoided there came from another rule)
  const charAvoided = input.mode === 'normal' ? [] : charRules.avoid.filter((x) => avoided.has(x.key) && !wanted.has(x.key));
  if (charAvoided.length) notes.push({ kind: 'character', character: input.character, items: charAvoided.map((x) => ({ key: x.key, why: x.why, tier: x.tier })) });
  for (const e of effects) { delete e._l; delete e._o; }

  const notOnRelics = [];
  for (const t of types) {
    for (const name of t.notOnRelics || []) {
      if (!notOnRelics.some((n) => n.name === name)) notOnRelics.push({ name, type: t.id });
    }
  }
  return { effects, conflicts, notOnRelics, notes, unknown };
}

/**
 * effect key -> { unreleased, deepOnly, character }
 *   unreleased: every relic id of the key is marked; deepOnly: every released relic id is marked (same rule as the
 *   app's lists: a kind with a normal version, e.g. a relic's fixed effect, is usable in normal-only mode);
 *   character: the character in 「【キャラ名】…」 for character-specific effects
 */
function suggestEffectInfo(effectsData) {
  const info = {};
  for (const [id, e] of Object.entries((effectsData && effectsData.effects) || {})) {
    const n = Number(id);
    if (!(n < 200000 || (n >= 6000000 && n < 7400000))) continue;   // relic effects only
    const cur = info[e.key];
    const m = /^【(.+?)】/.exec(e.name_ja || '');
    if (!cur) {
      info[e.key] = { unreleased: !!e.unreleased, deepOnly: !e.unreleased && !!e.deepOnly, character: m ? m[1] : '', _released: !e.unreleased };
    } else {
      cur.unreleased = cur.unreleased && !!e.unreleased;
      if (!e.unreleased) {
        cur.deepOnly = (cur._released ? cur.deepOnly : true) && !!e.deepOnly;
        cur._released = true;
      }
    }
  }
  for (const v of Object.values(info)) delete v._released;
  return info;
}
