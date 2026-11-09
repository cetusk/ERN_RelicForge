/**
 * Effect categories and the list of released relic effects — shared by the app (web / gui) and the public
 * guide page (web/guide.html).
 *
 * The public page shows effects without a save file, so it must never show an unreleased effect (spoilers):
 * releasedRelicEffects() keeps relic effects only (unique relic ids < 200000, normal / deep 6000000–7399999)
 * and drops every id marked "unreleased" in effects_data.json (tools/wiki_effects keeps those marks).
 */

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

function isRelicEffectId(id) {
  const n = Number(id);
  return n < 200000 || (n >= 6000000 && n < 7400000);
}

/**
 * Effect kinds (keys) that only appear on deep relics: every released relic id of the kind is marked deepOnly.
 * A kind with a normal version (e.g. 属性カット率上昇: deep 6611100 and the fixed effect 7006300 of a relic) is not.
 * @param {object} effects  id -> { key, deepOnly, unreleased } (effects_data.json "effects", or the app's lookup)
 */
function deepOnlyKeys(effects) {
  const deep = new Map();   // key -> every released relic id so far is deep-only
  for (const [id, e] of Object.entries(effects || {})) {
    if (!e.key || !isRelicEffectId(id) || e.unreleased) continue;
    deep.set(e.key, (deep.has(e.key) ? deep.get(e.key) : true) && !!e.deepOnly);
  }
  return new Set([...deep].filter(([, d]) => d).map(([k]) => k));
}

/**
 * The notes of a kind's normal and deep versions when they differ (e.g. 最大HP上昇: 通常 +100 / 深層 +10%):
 * key -> [{ deep, stackNotes, stackNotesFull }], only for kinds whose released relic ids have different notes.
 */
function effectVariants(effects) {
  const byKey = new Map();
  const ids = Object.keys(effects || {}).sort((a, b) => Number(a) - Number(b));
  for (const id of ids) {
    const e = effects[id];
    if (!e.key || !isRelicEffectId(id) || e.unreleased) continue;
    const list = byKey.get(e.key) || [];
    const v = { deep: !!e.deepOnly, stackNotes: e.stackNotes || '', stackNotesFull: e.stackNotesFull || '' };
    if (!list.some((x) => x.deep === v.deep && x.stackNotes === v.stackNotes)) list.push(v);
    byKey.set(e.key, list);
  }
  const out = new Map();
  for (const [k, list] of byKey) {
    if (new Set(list.map((x) => x.stackNotes)).size > 1 && list.some((x) => x.deep) && list.some((x) => !x.deep)) {
      out.set(k, list.sort((a, b) => a.deep - b.deep));
    }
  }
  return out;
}

/**
 * One entry per effect kind (key) that has at least one released relic id:
 * [{ key, name_ja, name_en, category, deepOnly, stackable, stackNotes, stackNotesFull, variants }], sorted by name.
 * Names and notes come from a released id; deepOnly when every released id is deep-only; variants when the normal
 * and deep versions have different notes (see effectVariants).
 */
function releasedRelicEffects(effectsData) {
  const effects = (effectsData && effectsData.effects) || {};
  const deepKeys = deepOnlyKeys(effects);
  const variants = effectVariants(effects);
  const byKey = new Map();
  const ids = Object.keys(effects).sort((a, b) => Number(a) - Number(b));
  for (const id of ids) {
    const e = effects[id];
    if (!e.key || !isRelicEffectId(id) || e.unreleased || byKey.has(e.key)) continue;
    byKey.set(e.key, {
      key: e.key,
      name_ja: e.name_ja || e.name_en || e.key,
      name_en: e.name_en || e.key,
      category: classifyEffect(e.name_ja, e.name_en, e.key),
      deepOnly: deepKeys.has(e.key),
      stackable: e.stackable,
      stackNotes: e.stackNotes || '',
      stackNotesFull: e.stackNotesFull || '',
      variants: variants.get(e.key) || null,
    });
  }
  return [...byKey.values()].sort((a, b) => a.name_ja.localeCompare(b.name_ja, 'ja'));
}
