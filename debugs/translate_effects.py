#!/usr/bin/env python3
"""
Translate effects_data.json: rename "name" -> "name_en", add "name_ja"
Uses official in-game Japanese names from Elden Ring: Nightreign
"""
import json
import re
import sys

# ============================================================
# Direct name -> Japanese mapping (exact match, case-insensitive)
# ============================================================
EXACT_MAP = {
    # === Stats ===
    "Increased Maximum Hp": "最大HP上昇",
    "Increased Maximum Fp": "最大FP上昇",
    "Increased Maximum Stamina": "最大スタミナ上昇",
    "Vigor Plus 1": "生命力+1",
    "Vigor Plus 2": "生命力+2",
    "Vigor Plus 3": "生命力+3",
    "Mind Plus 1": "精神力+1",
    "Mind Plus 2": "精神力+2",
    "Mind Plus 3": "精神力+3",
    "Endurance Plus 1": "持久力+1",
    "Endurance Plus 2": "持久力+2",
    "Endurance Plus 3": "持久力+3",
    "Strength Plus 1": "筋力+1",
    "Strength Plus 2": "筋力+2",
    "Strength Plus 3": "筋力+3",
    "Dexterity Plus 1": "技量+1",
    "Dexterity Plus 2": "技量+2",
    "Dexterity Plus 3": "技量+3",
    "Intelligence Plus 1": "知力+1",
    "Intelligence Plus 2": "知力+2",
    "Intelligence Plus 3": "知力+3",
    "Faith Plus 1": "信仰+1",
    "Faith Plus 2": "信仰+2",
    "Faith Plus 3": "信仰+3",
    "Arcane Plus 1": "神秘+1",
    "Arcane Plus 2": "神秘+2",
    "Arcane Plus 3": "神秘+3",
    "Poise Plus 1": "強靭度+1",
    "Poise Plus 2": "強靭度+2",
    "Poise Plus 3": "強靭度+3",
    "Poise Plus 4": "強靭度+4",
    "Poise Plus 5": "強靭度+5",

    # === Attack Power Up ===
    "Physical Attack Up": "物理攻撃力上昇",
    "Physical Attack Up Plus 1": "物理攻撃力上昇+1",
    "Physical Attack Up Plus 2": "物理攻撃力上昇+2",
    "Physical Attack Up Plus 3": "物理攻撃力上昇+3",
    "Physical Attack Up Plus 4": "物理攻撃力上昇+4",
    "Magic Attack Power Up": "魔力攻撃力上昇",
    "Magic Attack Power Up Plus 1": "魔力攻撃力上昇+1",
    "Magic Attack Power Up Plus 2": "魔力攻撃力上昇+2",
    "Magic Attack Power Up Plus 3": "魔力攻撃力上昇+3",
    "Magic Attack Power Up Plus 4": "魔力攻撃力上昇+4",
    "Fire Attack Power Up": "炎攻撃力上昇",
    "Fire Attack Power Up Plus 1": "炎攻撃力上昇+1",
    "Fire Attack Power Up Plus 2": "炎攻撃力上昇+2",
    "Fire Attack Power Up Plus 3": "炎攻撃力上昇+3",
    "Fire Attack Power Up Plus 4": "炎攻撃力上昇+4",
    "Lightning Attack Power Up": "雷攻撃力上昇",
    "Lightning Attack Power Up Plus 1": "雷攻撃力上昇+1",
    "Lightning Attack Power Up Plus 2": "雷攻撃力上昇+2",
    "Lightning Attack Power Up Plus 3": "雷攻撃力上昇+3",
    "Lightning Attack Power Up Plus 4": "雷攻撃力上昇+4",
    "Holy Attack Power Up": "聖攻撃力上昇",
    "Holy Attack Power Up Plus 1": "聖攻撃力上昇+1",
    "Holy Attack Power Up Plus 2": "聖攻撃力上昇+2",
    "Holy Attack Power Up Plus 3": "聖攻撃力上昇+3",
    "Holy Attack Power Up Plus 4": "聖攻撃力上昇+4",

    # === Improved Attack Power ===
    "Improved Physical Attack Power": "物理攻撃力強化",
    "Improved Magic Attack Power": "魔力攻撃力強化",
    "Improved Fire Attack Power": "炎攻撃力強化",
    "Improved Lightning Attack Power": "雷攻撃力強化",
    "Improved Holy Attack Power": "聖攻撃力強化",
    "Improved Non Physical Attack Power": "属性攻撃力強化",
    "Improved Affinity Attack Power": "属性攻撃力上昇",
    "Improved Affinity Attack Power Plus 1": "属性攻撃力上昇+1",
    "Improved Affinity Attack Power Plus 2": "属性攻撃力上昇+2",
    "Improved Melee Attack Power": "近接攻撃力上昇",
    "Improved Skill Attack Power": "戦技攻撃力上昇",
    "Improved Initial Standard Attack": "通常攻撃の1段目強化",
    "Improved Critical Hits": "致命の一撃強化",
    "Improved Critical Hits Plus 1": "致命の一撃強化+1",
    "Improved Guard Counters": "ガードカウンター強化",
    "Improved Guard Counters Plus 1": "ガードカウンター強化+1",
    "Improved Guard Counters Plus 2": "ガードカウンター強化+2",
    "Improved Roar And Breath Attacks": "咆哮とブレス強化",
    "Improved Roar And Breath Attacks Plus 1": "咆哮とブレス強化+1",
    "Improved Roar And Breath Attacks Plus 2": "咆哮とブレス強化+2",
    "Improved Throwing Pots": "投擲壺強化",
    "Improved Throwing Pot Damage": "投擲壺の攻撃力上昇",
    "Improved Throwing Pot Damage Plus 1": "投擲壺の攻撃力上昇+1",
    "Improved Throwing Pot Damage Plus 2": "投擲壺の攻撃力上昇+2",
    "Improved Throwing Knife Damage": "投擲ナイフの攻撃力上昇",
    "Improved Throwing Knife Damage Plus 1": "投擲ナイフの攻撃力上昇+1",
    "Improved Throwing Knife Damage Plus 2": "投擲ナイフの攻撃力上昇+2",
    "Improved Glintstone And Gravity Stone Damage": "輝石、重力石アイテムの攻撃力上昇",
    "Improved Glintstone And Gravity Stone Damage Plus 1": "輝石、重力石アイテムの攻撃力上昇+1",
    "Improved Glintstone And Gravity Stone Damage Plus 2": "輝石、重力石アイテムの攻撃力上昇+2",
    "Improved Perfuming Arts": "調香術強化",
    "Improved Perfuming Arts Plus 1": "調香術強化+1",
    "Improved Perfuming Arts Plus 2": "調香術強化+2",
    "Improved Ranged Weapon Attacks": "遠距離武器の攻撃力上昇",
    "Improved Charge Attacks": "タメ攻撃強化",
    "Improved Charged Spells And Skills": "タメ魔術/祈祷/戦技強化",
    "Improved Charged Sorceries": "タメ魔術強化",
    "Improved Charged Incantation": "タメ祈祷強化",
    "Improved Charged Skill Attack Power": "タメ戦技攻撃力上昇",
    "Improved Jump Attacks": "ジャンプ攻撃強化",
    "Improved Chain Attack Finishers": "連撃のフィニッシュ強化",
    "Improved Guard Breaking": "ガード崩し強化",
    "Improved Thrusting Counterattack": "刺突カウンター強化",
    "Improved Stance Breaking": "体勢を崩す力上昇",
    "Improved Stance Breaking When Two Handing": "両手持ちの、体勢を崩す力上昇",
    "Improved Stance Breaking When Wielding Two Armaments": "二刀持ちの、体勢を崩す力上昇",
    "Improved Stance Breaking With Head Shots": "ヘッドショットの、体勢を崩す力上昇",
    "Improved Dexterity": "技量強化",
    "Improved Attack Power When Two Handing": "両手持ち攻撃力上昇",
    "Attack Up When Wielding Two Armaments": "二刀持ち攻撃力上昇",
    "Boosts Attack Power Of Added Affinity Attacks": "属性攻撃力が付加された時、属性攻撃力上昇",
    "Attack Boost From Nearby Allies": "周囲の味方から攻撃力上昇",
    "Attack Power Increases After Using Grease Items": "脂アイテム使用時、追加で物理攻撃力上昇",
    "Physical Attack Power Increases After Using Grease Items Plus 1": "脂アイテム使用時、追加で攻撃力上昇+1",
    "Physical Attack Power Increases After Using Grease Items Plus 2": "脂アイテム使用時、追加で攻撃力上昇+2",
    "Attack Power Permanently Increased For Each Evergaol Prisoner Defeated": "封牢の囚を倒す度、攻撃力上昇",
    "Attack Power Up After Defeating Anight Invader": "夜の侵入者を倒す度、攻撃力上昇",
    "Improved Attack Power At Low Hp": "HP低下時、攻撃力上昇",
    "Improved Attack Power At Full Hp": "HP最大時、攻撃力上昇",
    "Successive Attacks Boost Attack Power": "攻撃連続時、攻撃力上昇",
    "Taking Attacks Improves Attack Power": "攻撃を受けると攻撃力上昇",
    "Switching Weapons Boosts Attack Power": "武器の持ち替え時、物理攻撃力上昇",
    "Switching Weapons Adds An Affinity Attack": "武器の持ち替え時、いずれかの属性攻撃力を付加",
    "Status Ailment Gauges Slowly Increase Attack Power": "状態異常ゲージがある時、徐々に攻撃力上昇",
    "Guard Counter Is Given Aboost Based On Current Hp": "ガードカウンターに、自身の現在HPの一部を加える",
    "Projectile Damage Drop Off Reduced": "遠距離攻撃力低下の軽減",
    "Projectile Damage Drop Off Reduced Plus 1": "遠距離攻撃力低下の軽減+1",
    "Critical Hits Boost Attack Power": "致命の一撃で攻撃力上昇",
    "Damage Boosted After Critical Hit": "致命の一撃後、攻撃力上昇",
    "Changed Strong Attacks": "強攻撃の変化",
    "Strong Attack Creates Wide Wave Of Heat": "強攻撃が広範囲の熱波を生む",
    "Strong Attacks Improve Poise": "強攻撃時、強靭度上昇",
    "Strong Jump Attacks Create Shockwave": "ジャンプ強攻撃で衝撃波発生",

    # === Sorcery & Incantation ===
    "Improved Sorceries": "魔術強化",
    "Improved Sorceries Plus 1": "魔術強化+1",
    "Improved Sorceries Plus 2": "魔術強化+2",
    "Improved Incantations": "祈祷強化",
    "Improved Incantations Plus 1": "祈祷強化+1",
    "Improved Incantations Plus 2": "祈祷強化+2",
    "Improved Sorceries And Incantations": "魔術/祈祷強化",
    "Improved Spell Casting Speed": "魔術/祈祷の詠唱速度上昇",
    "Extended Spell Duration": "魔術/祈祷、効果時間延長",
    "Increased Sorcery And Incantation Duration": "魔術/祈祷、効果時間延長",
    "Reduced Spell Fp Cost": "魔術/祈祷のFP消費軽減",
    "Reduced Skill Fp Cost": "戦技のFP消費軽減",
    "Raises Sorcery Incantation Potency": "魔術/祈祷の威力上昇",
    "Communion Grants Anti Dragon Effect": "竜餐により竜特効付与",
    "Improved Stonedigger Sorcery": "石掘りの魔術強化",
    "Improved Carian Sword Sorcery": "カーリアの剣の魔術強化",
    "Improved Glintblade Sorcery": "輝剣の魔術強化",
    "Improved Invisibility Sorcery": "不可視の魔術強化",
    "Improved Crystalian Sorcery": "結晶人の魔術強化",
    "Improved Gravity Sorcery": "重力の魔術強化",
    "Improved Thorn Sorcery": "茨の魔術強化",
    "Improved Night Sorcery": "夜の魔術強化",
    "Improved Fundamentalist Incantations": "黄金律原理主義の祈祷強化",
    "Improved Dragon Cult Incantations": "王都古竜信仰の祈祷強化",
    "Improved Giants Flame Incantations": "巨人の火の祈祷強化",
    "Improved Godslayer Incantations": "神狩りの祈祷強化",
    "Improved Bestial Incantations": "獣の祈祷強化",
    "Improved Frenzied Flame Incantations": "狂い火の祈祷強化",
    "Improved Dragon Communion Incantations": "竜餐の祈祷強化",

    # === Damage Negation ===
    "Improved Physical Damage Negation": "物理カット率上昇",
    "Improved Physical Damage Negation Plus 1": "物理カット率上昇+1",
    "Improved Physical Damage Negation Plus 2": "物理カット率上昇+2",
    "Improved Magic Damage Negation": "魔力カット率上昇",
    "Improved Magic Damage Negation Plus 1": "魔力カット率上昇+1",
    "Improved Magic Damage Negation Plus 2": "魔力カット率上昇+2",
    "Improved Fire Damage Negation": "炎カット率上昇",
    "Improved Fire Damage Negation Plus 1": "炎カット率上昇+1",
    "Improved Fire Damage Negation Plus 2": "炎カット率上昇+2",
    "Improved Lightning Damage Negation": "雷カット率上昇",
    "Improved Lightning Damage Negation Plus 1": "雷カット率上昇+1",
    "Improved Lightning Damage Negation Plus 2": "雷カット率上昇+2",
    "Improved Holy Damage Negation": "聖カット率上昇",
    "Improved Holy Damage Negation Plus 1": "聖カット率上昇+1",
    "Improved Holy Damage Negation Plus 2": "聖カット率上昇+2",
    "Improved Non Physical Damage Negation": "属性カット率上昇",
    "Improved Affinity Damage Negation": "属性カット率上昇",
    "Improved Affinity Damage Negation Plus 1": "属性カット率上昇+1",
    "Improved Affinity Damage Negation Plus 2": "属性カット率上昇+2",
    "Improved Damage Negation At Low Hp": "HP低下時、カット率上昇",
    "Improved Damage Negation At Full Hp": "HP最大時、カット率上昇",
    "Improved Dodging": "回避性能上昇",
    "Improved Guarding Ability": "ガード性能上昇",
    "Improved Guarding Ability Plus 1": "ガード性能上昇+1",
    "Improved Guarding Ability Plus 2": "ガード性能上昇+2",
    "Improved Poise": "強靭度上昇",
    "Improved Poise Near Totem Stela": "トーテム・ステラの周囲で、強靭度上昇",
    "Improved Poise Damage Negation When Knocked Back By Damage": "ダメージで吹き飛ばされた時、強靭度とカット率上昇",
    "Magic Damage Negation Up": "魔力カット率上昇",
    "Fire Damage Negation Up": "炎カット率上昇",
    "Lightning Damage Negation Up": "雷カット率上昇",
    "Holy Damage Negation Up": "聖カット率上昇",
    "Impartial Physical Damage Negation": "物理カット率低下",
    "Impaired Physical Damage Negation": "物理カット率低下",
    "Impaired Damage Negation": "カット率低下",
    "Impaired Affinity Damage Negation": "属性カット率低下",
    "Taking Damage Boosts Damage Negation": "被ダメージ時、カット率上昇",
    "Dmg Negation Up While Charging Attacks": "タメ攻撃中、カット率上昇",
    "Dmg Negation Up While Casting Spells": "魔術/祈祷の詠唱中、カット率上昇",
    "Shielding Improves Damage Negation": "シールド中、カット率上昇",
    "Raises Physical Damage Negation Plus 1": "物理カット率上昇+1",
    "Raises Non Physical Damage Negation Plus 1": "属性カット率上昇+1",
    "Raises Physical Attack Power Plus 1": "物理攻撃力上昇+1",

    # === Resistance ===
    "Improved Poison Resistance": "毒耐性上昇",
    "Improved Poison Resistance Plus 1": "毒耐性上昇+1",
    "Improved Poison Resistance Plus 2": "毒耐性上昇+2",
    "Improved Rot Resistance": "腐敗耐性上昇",
    "Improved Rot Resistance Plus 1": "腐敗耐性上昇+1",
    "Improved Rot Resistance Plus 2": "腐敗耐性上昇+2",
    "Improved Blood Loss Resistance": "出血耐性上昇",
    "Improved Blood Loss Resistance Plus 1": "出血耐性上昇+1",
    "Improved Blood Loss Resistance Plus 2": "出血耐性上昇+2",
    "Improved Frost Resistance": "冷気耐性上昇",
    "Improved Frost Resistance Plus 1": "冷気耐性上昇+1",
    "Improved Frost Resistance Plus 2": "冷気耐性上昇+2",
    "Improved Sleep Resistance": "睡眠耐性上昇",
    "Improved Sleep Resistance Plus 1": "睡眠耐性上昇+1",
    "Improved Sleep Resistance Plus 2": "睡眠耐性上昇+2",
    "Improved Madness Resistance": "発狂耐性上昇",
    "Improved Madness Resistance Plus 1": "発狂耐性上昇+1",
    "Improved Madness Resistance Plus 2": "発狂耐性上昇+2",
    "Improved Death Blight Resistance": "抗死耐性上昇",
    "Improved Death Blight Resistance Plus 1": "抗死耐性上昇+1",
    "Improved Death Blight Resistance Plus 2": "抗死耐性上昇+2",
    "Improved Poison Rot Resistance": "毒/腐敗耐性上昇",
    "Improved Blood Loss And Frost Resistance": "出血/冷気耐性上昇",
    "Improved Sleep Madness Resistance": "睡眠/発狂耐性上昇",
    "All Resistances Up": "すべての状態異常耐性上昇",
    "All Resistance Up": "すべての状態異常耐性上昇",
    "Raises Resistance To All Ailments": "すべての状態異常耐性上昇",
    "All Resistances Down": "すべての状態異常耐性低下",

    # === Recovery ===
    "Continuous Hp Recovery": "HP持続回復",
    "Continuous Fp Recovery": "FP持続回復",
    "Continuous Hploss": "HP持続減少",
    "Fp Restoration Upon Successive Attacks": "攻撃連続時、FP回復",
    "Hp Restoration Upon Successive Attacks": "攻撃連続時、HP回復",
    "Successive Attack Hp Restoration": "攻撃連続時、HP回復",
    "Hp Recovery From Successful Guarding": "ガード成功時、HP回復",
    "Hp Recovery From Successful Guarding Plus": "ガード成功時、HP回復+",
    "Fp Recovery From Successful Guarding": "ガード成功時、FP回復",
    "Defeating Enemies Restores Hp": "敵を倒した時、HP回復",
    "Defeating Enemies Restores Fp": "敵を倒した時、FP回復",
    "Defeating Enemies Restores Hpfor Allies But Not For Self": "敵を倒した時、自身を除く周囲の味方のHP回復",
    "Critical Hit Hprestoration": "致命の一撃でHP回復",
    "Critical Hit Fprestoration": "致命の一撃でFP回復",
    "Partial Hp Restoration Upon Post Damage Attacks": "ダメージを受けた直後、攻撃によりHPの一部を回復",
    "Partial Hprestoration Upon Post Damage Attacks Plus 1": "ダメージを受けた直後、攻撃によりHPの一部を回復+1",
    "Partial Hprestoration Upon Post Damage Attacks Plus 2": "ダメージを受けた直後、攻撃によりHPの一部を回復+2",
    "Hp Restoration Upon Thrusting Counterattack": "刺突カウンター発生時、HP回復",
    "Hp Restoration Upon Thrusting Counterattack Plus 1": "刺突カウンター発生時、HP回復+1",
    "Hp Restoration Upon Thrusting Counterattack Plus 2": "刺突カウンター発生時、HP回復+2",
    "Hp Restored When Using Medicinal Boluses Etc": "苔薬などのアイテム使用でHP回復",
    "Hp Restored When Using Medicinal Boluses Etc Plus 1": "苔薬などのアイテム使用でHP回復+1",
    "Hp Restored When Using Medicinal Boluses Etc Plus 2": "苔薬などのアイテム使用でHP回復+2",
    "Hp Restoration With Head Shots": "ヘッドショットでHP回復",
    "Hp Restoration Upon Attacks": "攻撃命中時、HP回復",
    "Fp Restoration Upon Attacks": "攻撃命中時、FP回復",
    "Slowly Restore Hp For Self And Nearby Allies When Hp Is Low": "HP低下時、周囲の味方を含めHPをゆっくりと回復",
    "Improved Flask Hprestoration": "聖杯瓶の回復量上昇",
    "Improved Stamina Recovery": "スタミナ回復速度上昇",
    "Improved Stamina Recovery Plus 1": "スタミナ回復速度上昇+1",
    "Stamina Recovery Upon Landing Attacks": "攻撃命中時、スタミナ回復",
    "Stamina Recovery Upon Landing Attacks Plus 1": "攻撃命中時、スタミナ回復+1",
    "Taking Damage Restores Fp": "被ダメージ時、FP回復",
    "Gradual Restoration By Flask": "聖杯瓶による徐々に回復",
    "Flask Also Heals Allies": "聖杯瓶の回復を、周囲の味方に分配",
    "Flask Healing Also Restores Fp": "聖杯瓶使用時、FPも回復",
    "Rot In Vicinity Causes Continuous Hp Recovery": "周囲で腐敗状態の発生時、HP持続回復",
    "Madness Continually Recovers Fp": "発狂状態になると、FP持続回復",
    "Defeating Enemies Near Totem Stela Restores Hp": "トーテム・ステラの周囲で敵を倒した時、HP回復",
    "Low Hp Crit Hit Fully Restores Hp": "HP低下時、致命の一撃でHPを全回復",
    "Successive Attacks Negate Damage": "攻撃連続時、カット率上昇",
    "Performing Consecutive Successful Guards Improves Guard Ability And Deflects Big Attacks": "ガード連続成功時、ガード性能上昇＆大攻撃を弾く",

    # === Skills / Arts ===
    "Character Skill Cooldown Reduction": "スキルクールタイム軽減",
    "Character Skill Cooldown Reduction Plus 1": "スキルクールタイム軽減+1",
    "Character Skill Cooldown Reduction Plus 2": "スキルクールタイム軽減+2",
    "Character Skill Cooldown Reduction Plus 3": "スキルクールタイム軽減+3",
    "Character Skill Cooldown Reduction Plus 4": "スキルクールタイム軽減+4",
    "Character Skill Cooldown Reduction Plus 5": "スキルクールタイム軽減+5",
    "Ultimate Art Auto Charge Plus 1": "アーツゲージ自然蓄積+1",
    "Ultimate Art Auto Charge Plus 2": "アーツゲージ自然蓄積+2",
    "Ultimate Art Auto Charge Plus 3": "アーツゲージ自然蓄積+3",
    "Ultimate Art Auto Charge Plus 4": "アーツゲージ自然蓄積+4",
    "Ultimate Art Auto Charge Plus 5": "アーツゲージ自然蓄積+5",
    "Ultimate Art Gauge Charge Speed Up": "アーツゲージ蓄積増加",
    "Defeating Enemies Fills More Of The Art Gauge": "敵を倒した時、アーツゲージ増加",
    "Defeating Enemies Fills More Of The Art Gauge Plus 1": "敵を倒した時、アーツゲージ増加+1",
    "Defeating Enemies Fills More Of The Art Gauge Plus 2": "敵を倒した時、アーツゲージ増加+2",
    "Art Gauge Charged From Successful Guarding": "ガード成功時、アーツゲージを蓄積",
    "Art Gauge Charged From Successful Guarding Plus 1": "ガード成功時、アーツゲージを蓄積+1",
    "Art Gauge Charged From Successful Guarding Plus 2": "ガード成功時、アーツゲージを蓄積+2",
    "Art Gauge Fills Moderately Upon Critical Hit": "致命の一撃で、アーツゲージ増加",
    "Art Gauge Fills Moderately Upon Critical Hit Plus 1": "致命の一撃で、アーツゲージ増加+1",
    "Art Gauge Fills Moderately Upon Critical Hit Plus 2": "致命の一撃で、アーツゲージ増加+2",
    "Skill Activation Improves Poise": "戦技発動時、強靭度上昇",

    # === Status Ailments ===
    "Attacks Inflict Poison": "攻撃に毒の状態異常を付加",
    "Attacks Inflict Poison Plus 1": "攻撃に毒の状態異常を付加+1",
    "Attacks Inflict Poison Plus 2": "攻撃に毒の状態異常を付加+2",
    "Attacks Inflict Blood Loss": "攻撃に出血の状態異常を付加",
    "Attacks Inflict Blood Loss Plus 1": "攻撃に出血の状態異常を付加+1",
    "Attacks Inflict Blood Loss Plus 2": "攻撃に出血の状態異常を付加+2",
    "Attacks Inflict Sleep": "攻撃に睡眠の状態異常を付加",
    "Attacks Inflict Sleep Plus 1": "攻撃に睡眠の状態異常を付加+1",
    "Attacks Inflict Sleep Plus 2": "攻撃に睡眠の状態異常を付加+2",
    "Attacks Inflict Sleep Plus 3": "攻撃に睡眠の状態異常を付加+3",
    "Attacks Inflict Death Blight": "攻撃に死の状態異常を付加",
    "Attacks Inflict Scarlet Rot": "攻撃に腐敗の状態異常を付加",
    "Attacks Inflict Scarlet Rot Plus 1": "攻撃に腐敗の状態異常を付加+1",
    "Attacks Inflict Scarlet Rot Plus 2": "攻撃に腐敗の状態異常を付加+2",
    "Attacks Inflict Frost": "攻撃に冷気の状態異常を付加",
    "Attacks Inflict Frost Plus 1": "攻撃に冷気の状態異常を付加+1",
    "Attacks Inflict Frost Plus 2": "攻撃に冷気の状態異常を付加+2",
    "Attacks Inflict Frost Plus 3": "攻撃に冷気の状態異常を付加+3",
    "Attacks Inflict Madness": "攻撃に発狂の状態異常を付加",
    "Attacks Inflict Rot": "攻撃に腐敗の状態異常を付加",
    "Attacks Inflict Rot When Damage Is Taken": "被ダメージ時、腐敗の状態異常を付加",
    "Add Fire To Weapon": "武器に炎攻撃力を付加",
    "Add Magic To Weapon": "武器に魔力攻撃力を付加",
    "Add Lightning To Weapon": "武器に雷攻撃力を付加",
    "Add Holy To Weapon": "武器に聖攻撃力を付加",
    "Ailments Cause Increased Damage": "状態異常時、被ダメージ増加",
    "Blood Loss In Vicinity Increases Attack Power": "周囲で出血状態の発生時、攻撃力上昇",
    "Blood Loss Increases Attack Power": "出血状態になると、攻撃力上昇",
    "Poison And Rot Improves Attack Power": "毒/腐敗状態で攻撃力上昇",
    "Poison And Rot In Vicinity Increases Attack Power": "周囲で毒/腐敗状態の発生時、攻撃力上昇",
    "Poison Increases Attack Power": "毒状態になると、攻撃力上昇",
    "Frostbite Increases Attack Power": "凍傷状態になると、攻撃力上昇",
    "Sleep Increases Attack Power": "睡眠状態になると、攻撃力上昇",
    "Madness Increases Attack Power": "発狂状態になると、攻撃力上昇",
    "Sleep In Vicinity Improves Attack Power": "周囲で睡眠状態の発生時、攻撃力上昇",
    "Sleep In Vicinity Improves Attack Power Plus 1": "周囲で睡眠状態の発生時、攻撃力上昇+1",
    "Sleep In Vicinity Improves Attack Power Plus 2": "周囲で睡眠状態の発生時、攻撃力上昇+2",
    "Madness In Vicinity Improves Attack Power": "周囲で発狂状態の発生時、攻撃力上昇",
    "Madness In Vicinity Improves Attack Power Plus 1": "周囲で発狂状態の発生時、攻撃力上昇+1",
    "Madness In Vicinity Improves Attack Power Plus 2": "周囲で発狂状態の発生時、攻撃力上昇+2",
    "Nearby Frostbite Conceals Self": "周囲で凍傷状態の発生時、自身の姿を隠す",
    "Attack Power Up When Facing Poison Afflicted Enemy": "毒状態の敵に対する攻撃を強化",
    "Attack Power Up When Facing Poison Afflicted Enemy Plus 1": "毒状態の敵に対する攻撃を強化+1",
    "Attack Power Up When Facing Poison Afflicted Enemy Plus 2": "毒状態の敵に対する攻撃を強化+2",
    "Attack Power Up When Facing Scarlet Rot Afflicted Enemy": "腐敗状態の敵に対する攻撃を強化",
    "Attack Power Up When Facing Scarlet Rot Afflicted Enemy Plus 1": "腐敗状態の敵に対する攻撃を強化+1",
    "Attack Power Up When Facing Scarlet Rot Afflicted Enemy Plus 2": "腐敗状態の敵に対する攻撃を強化+2",
    "Attack Power Up When Facing Frostbite Afflicted Enemy": "凍傷状態の敵に対する攻撃を強化",
    "Attack Power Up When Facing Frostbite Afflicted Enemy Plus 1": "凍傷状態の敵に対する攻撃を強化+1",
    "Attack Power Up When Facing Frostbite Afflicted Enemy Plus 2": "凍傷状態の敵に対する攻撃を強化+2",
    "Attack Power Up When Facing Sleep Afflicted Enemy": "睡眠状態の敵に対する攻撃を強化",
    "Attacks Create Magic Bursts Versus Sleeping Enemies": "睡眠状態の敵への攻撃で魔力爆発",
    "Critical Hits Deal Huge Damage On Poisoned Enemies": "毒状態の敵への致命の一撃が大ダメージ",
    "Critical Hits Inflict Blood Loss": "HP低下時、致命の一撃に出血を付加",

    # === Taking Damage Buildup ===
    "Taking Damage Causes Poison Buildup": "被ダメージ時、毒を蓄積",
    "Taking Damage Causes Rot Buildup": "被ダメージ時、腐敗を蓄積",
    "Taking Damage Causes Frost Buildup": "被ダメージ時、冷気を蓄積",
    "Taking Damage Causes Blood Loss Buildup": "被ダメージ時、出血を蓄積",
    "Taking Damage Causes Madness Buildup": "被ダメージ時、発狂を蓄積",
    "Taking Damage Causes Sleep Buildup": "被ダメージ時、睡眠を蓄積",
    "Taking Damage Causes Death Buildup": "被ダメージ時、死を蓄積",

    # === Status produces mist ===
    "Poison Produces Amist Of Poison": "毒状態になると、毒霧を発生",
    "Madness Produces Aflame Of Frenzy": "発狂状態になると、狂い火を発生",
    "Rot Produces Amist Of Scarlet Rot": "腐敗状態になると、腐敗霧を発生",
    "Frostbite Produces Amist Of Frost": "凍傷状態になると、冷気霧を発生",
    "Sleep Produces Amist Of Sleep": "睡眠状態になると、睡眠霧を発生",

    # === Critical Hit special ===
    "Critical Hit Boosts Stamina Recovery Speed": "致命の一撃で、スタミナ回復速度上昇",
    "Critical Hit Boosts Stamina Recovery Speed Plus 1": "致命の一撃で、スタミナ回復速度上昇+1",
    "Critical Hit Adds Lightning Effect": "致命の一撃に雷効果を付加",
    "Critical Hit Creates Sleep Mist": "致命の一撃で睡眠霧を発生",
    "Critical Hits Earn Runes": "致命の一撃で、ルーンを取得",
    "Fire Critical Hit Grants Max Stamina Boost": "炎の致命の一撃で最大スタミナ上昇",
    "Sacred Order Upon Holy Critical Hit": "聖の致命の一撃で聖律を発動",
    "Magma Upon Fire Critical Hit": "炎の致命の一撃でマグマ発生",
    "Lightning Critical Hit Imbues Armament": "雷の致命の一撃で武器に雷付与",
    "Crystal Shards Upon Magic Critical Hit": "魔力の致命の一撃で結晶弾発生",
    "Poison Mist Upon Poison Critical Hit": "毒の致命の一撃で毒霧発生",
    "Blood Loss Crit Thorns Of Punishment": "出血の致命の一撃で罰の茨発動",
    "Rot Critical Hit Fires Pest Threads": "腐敗の致命の一撃で害虫の糸発射",
    "Ice Storm Upon Critical Hit With Frost": "冷気の致命の一撃で氷嵐発生",
    "Madness Crit Hit Fires Frenzied Flame": "発狂の致命の一撃で狂い火発射",
    "Death Crit Hit Calls Death Lightning": "死の致命の一撃で死の雷発動",

    # === Guard effects ===
    "Consecutive Guards Harden Skin": "ガード連続成功時、肌を硬化",
    "Guard Counters Activate Holy Attacks": "ガードカウンターで聖攻撃を発動",
    "Guard Counters Cast Light Pillar": "ガードカウンターで光の柱を発生",
    "Guard Counters Launch Summoning Attack": "ガードカウンターで召喚攻撃を発動",
    "Shockwave Produced From Successful Guarding": "ガード成功時、衝撃波を発生",
    "Parries Activate Golden Retaliation": "パリィ成功時、黄金の報復を発動",
    "Successful Guarding Ups Poise": "ガード成功時、強靭度上昇",
    "Successful Guarding Ups Dmg Negation": "ガード成功時、カット率上昇",
    "Guarding Ups Attack And Casting Speeds": "ガード中、攻撃速度と詠唱速度上昇",
    "Draw Enemy Attention While Guarding": "ガード中、敵に狙われやすくなる",
    "Shielding Invokes Indomitable Vow": "シールド中、不屈の誓いを発動",
    "Shielding Creates Holy Ground": "シールド中、聖地を生成",
    "Broken Stance Activates Endure": "体勢が崩れた時、我慢を発動",

    # === Charged attack effects ===
    "Ice Storm Upon Charged Slash": "タメ斬り攻撃時、氷嵐を発生",
    "Ring Of Light Upon Charged Slash": "タメ斬り攻撃時、光輪を発生",
    "Black Flames Upon Charged Slash": "タメ斬り攻撃時、黒炎を発生",
    "Phantom Attack Upon Charged Slash": "タメ斬り攻撃時、幻影攻撃を発生",
    "Roaring Flames Upon Charged Slash": "タメ斬り攻撃時、咆哮炎を発生",
    "Holy Shockwave Upon Charged Strike": "タメ打ち攻撃時、聖衝撃波を発生",
    "Projectiles Upon Charged Strike": "タメ打ち攻撃時、飛び道具を発生",
    "Luring Enemies Upon Charged Strike": "タメ打ち攻撃時、敵を誘引",
    "Shockwave Upon Charged Strike": "タメ打ち攻撃時、衝撃波を発生",
    "Phantom Attack Upon Charged Strike": "タメ打ち攻撃時、幻影攻撃を発生",
    "Magma Upon Charged Strike": "タメ打ち攻撃時、マグマを発生",
    "Magic Bubbles Upon Charged Strike": "タメ打ち攻撃時、魔力泡を発生",
    "Phantom Attack Upon Charged Thrust": "タメ突き攻撃時、幻影攻撃を発生",
    "Lightning Upon Charged Thrust": "タメ突き攻撃時、雷を発生",
    "Acid Mist Upon Charged Thrust": "タメ突き攻撃時、酸霧を発生",
    "Pest Threads Upon Charged Thrust": "タメ突き攻撃時、害虫の糸を発生",
    "Poison Mist Upon Charged Thrust": "タメ突き攻撃時、毒霧を発生",
    "Charged Thrust Invokes Sleep Mist": "タメ突き攻撃時、睡眠霧を発生",
    "Colosssal Armaments Coated In Rock When Performing Charged Attacks": "特大武器タメ攻撃時、岩を纏う",
    "Colossal Armaments Coated In Rock When Performing Charged Attacks": "特大武器タメ攻撃時、岩を纏う",
    "Projectiles Launched Upon Attacks": "攻撃時、飛び道具を発射",

    # === Precision Aiming ===
    "Lightning Upon Precision Aiming": "精密射撃時、雷を発生",
    "Poison Mist Upon Precision Aiming": "精密射撃時、毒霧を発生",
    "Rot Mist Upon Precision Aiming": "精密射撃時、腐敗霧を発生",
    "Bloodflies Upon Precision Aiming": "精密射撃時、血蝿を発生",

    # === Charge attack follow-up ===
    "Magic Attack Follows Charge Attacks": "タメ攻撃に追加の魔力攻撃",
    "Fire Attack Follows Charge Attacks": "タメ攻撃に追加の炎攻撃",
    "Lightning Follows Charge Attacks": "タメ攻撃に追加の雷攻撃",
    "Holy Attack Follows Charge Attacks": "タメ攻撃に追加の聖攻撃",

    # === Walking effects ===
    "Darkness Conceals Caster While Walking": "歩行中、闇が術者を隠す",
    "Savage Flames Roar While Walking": "歩行中、蛮火の咆哮を発生",
    "Flame Of Frenzy While Walking": "歩行中、狂い火を発生",
    "Wraiths While Walking": "歩行中、怨霊を発生",
    "Vicious Star Rain Pours While Walking": "歩行中、凶星の雨を降らせる",
    "Storm Of Red Lightning While Walking": "歩行中、赤雷の嵐を発生",

    # === Surge Sprint ===
    "Surge Sprint Landings Split Earth": "波動ダッシュ着地時、地面を割る",
    "Magma Surge Sprint": "波動ダッシュ中、マグマを発生",
    "Ice Storm Surge Sprint": "波動ダッシュ中、氷嵐を発生",

    # === Dodge ===
    "Lightning Upon Dodging": "回避時、雷を発生",

    # === Misc ===
    "Jumping Conjures Magic Projectiles": "ジャンプ時、魔力弾を発生",
    "Gesture Crossed Legs Builds Up Madness": "ジェスチャー「あぐら」により、発狂が蓄積",
    "Sudden Enemy Death Upon Attacks": "攻撃時、稀に敵が即死",
    "Occasionally Nullify Attacks When Damage Negations Is Lowered": "カット率低下時、稀に敵から受ける攻撃を無効化",
    "Creates Holy Ground At Low Hp": "HP低下時、聖地を生成",
    "Less Likely To Be Targeted": "敵に狙われにくくなる",
    "Multiple Periodical Glintblades": "定期的に輝剣を複数生成",
    "Many Periodical Glintblades": "定期的に輝剣を多数生成",
    "Periodical Giant Glintblades": "定期的に巨大輝剣を生成",

    # === Item Discovery / Runes ===
    "Improved Item Discovery": "アイテム発見力上昇",
    "More Runes From Defeated Enemies": "獲得ルーン増加",
    "Increased Rune Acquisition For Self And Allies": "自身と味方の取得ルーン増加",
    "No Rune Loss Or Level Down Upon Death": "死亡時ルーン喪失なし/レベルダウンなし",
    "Rune Discount For Shop Purchases While On Expedition": "出撃中、ショップでの購入に必要なルーンが割引",
    "Huge Rune Discount For Shop Purchases While On Expedition": "出撃中、ショップでの購入に必要なルーンが大割引",
    "Rune Of The Strong": "強者のルーン",
    "Runes 60K At Start 30K On Death": "出撃時ルーン60K、死亡時30K失う",
    "Treasure Marked Upon Map": "埋もれ宝の位置を地図に表示",

    # === Team ===
    "Raised Stamina Recovery For Nearby Allies But Not For Self": "自身を除く、周囲の味方のスタミナ回復速度上昇",
    "Items Confer Effect To All Nearby Allies": "アイテムの効果が周囲の味方にも発動",

    # === Reduced / Debuff ===
    "Reduced Vigor": "生命力低下",
    "Reduced Endurance": "持久力低下",
    "Reduced Vigor And Arcane": "生命力と神秘が低下",
    "Reduced Strength And Intelligence": "筋力と知力が低下",
    "Reduced Dexterity And Faith": "技量と信仰が低下",
    "Reduced Intelligence And Dexterity": "知力と技量が低下",
    "Reduced Faith And Strength": "信仰と筋力が低下",
    "Reduced Maximum Hp": "最大HP低下",
    "Reduced Maximum Fp": "最大FP低下",
    "Reduced Maximum Stamina": "最大スタミナ低下",
    "Reduced Flask Hprestoration": "聖杯瓶の回復量低下",
    "Reduced Rune Acquisition": "取得ルーン減少",
    "Reduced Fpconsumption": "FP消費軽減",
    "Reduced Fpconsumption Plus 1": "FP消費軽減+1",
    "Reduced Fpconsumption Plus 2": "FP消費軽減+2",
    "Reduced Stamina Consumption": "スタミナ消費軽減",
    "Maximum Hp Down": "最大HP低下",
    "Ultimate Art Charging Impaired": "アーツゲージ蓄積鈍化",
    "Lower Attack When Below Max Hp": "HP最大未満時、攻撃力低下",
    "Poison Buildup When Below Max Hp": "HP最大未満時、毒が蓄積",
    "Rot Buildup When Below Max Hp": "HP最大未満時、腐敗が蓄積",
    "Max Hpreduces Attack Power": "最大HP時、攻撃力低下",
    "Near Death Spills Flask": "瀕死時、聖杯瓶を失う",
    "Near Death Reduces Max Hp": "瀕死時、最大HP低下",
    "Near Death Reduces Art Gauge": "瀕死時、アーツゲージ低下",
    "Reduced Damage Negation For Flask Usages": "聖杯瓶使用時、カット率低下",
    "Sleep Buildup For Flask Usages": "聖杯瓶使用時、睡眠を蓄積",
    "Madness Buildup For Flask Usages": "聖杯瓶使用時、発狂を蓄積",
    "More Damage Taken After Evasion": "回避直後の被ダメージ増加",
    "Repeated Evasions Lower Damage Negation": "回避連続時、カット率低下",
    "Surge Sprinting Drains More Stamina": "波動ダッシュのスタミナ消費増加",
    "Increased Drain On Stamina For Evasion": "回避のスタミナ消費増加",
    "Lower Stamina Impairs Dmg Negation": "スタミナ低下時、カット率低下",
    "Attacks Impaired On Occasion": "稀に攻撃力が低下",
    "Slower Art Gauge When Below Max Hp": "HP最大未満時、アーツゲージ蓄積鈍化",
    "Nights Tide Damage Increased": "夜の潮の被ダメージ増加",
    "Damage Increased By Nights Encroachment": "夜の侵食によるダメージ増加",
    "Failing To Cast Sorcery Restores Fp": "魔術の詠唱失敗時、FP回復",

    # === Defeating Group Effects ===
    "Defeating Group Summons Wraiths": "集団撃破時、怨霊を召喚",
    "Defeating Group Releases Mist Of Charm": "集団撃破時、魅了の霧を放出",
    "Defeating Group Calls Vengeful Spirits": "集団撃破時、復讐の霊を召喚",
    "Magma Upon Defeating Multiple Enemies": "集団撃破時、マグマを発生",
    "Defeating Group Releases Mist Of Frost": "集団撃破時、冷気の霧を放出",
    "Defeating Group Unleashes Lightning": "集団撃破時、雷を放出",
    "Defeating Group Fires Golden Shockwave": "集団撃破時、黄金衝撃波を発射",

    # === Deep Layer specific ===
    "Max Hpincreased For Each Great Enemy Defeated At Agreat Church": "大教会の強敵を倒す度、最大HP上昇",
    "Runes And Item Discovery Increased For Each Great Enemy Defeated At Afort": "小砦の強敵を倒す度、取得ルーン増加、発見力上昇",
    "Arcane Increased For Each Great Enemy Defeated At Aruin": "遺跡の強敵を倒す度、神秘上昇",
    "Max Stamina Increased For Each Great Enemy Defeated At Agreat Encampment": "大野営地の強敵を倒す度、最大スタミナ上昇",
    "Max Fp Permanently Increased After Releasing Sorcerers Rise Mechanism": "魔術師塔の仕掛けが解除される度、最大FP上昇",
    "Raises Maximum Fp Plus 1": "最大FP上昇+1",

    # === Starting Armament ===
    "Starting Armament Deals Magic Damage": "出撃時の武器に魔力攻撃力を付加",
    "Starting Armament Deals Fire Damage": "出撃時の武器に炎攻撃力を付加",
    "Armament Deals Fire Damage Plus 1At Start Of Expedition": "出撃時の武器に炎攻撃力を付加+1",
    "Starting Armament Deals Lightning Damage": "出撃時の武器に雷攻撃力を付加",
    "Starting Armament Deals Holy Damage": "出撃時の武器に聖攻撃力を付加",
    "Starting Armament Inflicts Frost": "出撃時の武器に冷気の状態異常を付加",
    "Starting Armament Inflicts Poison": "出撃時の武器に毒の状態異常を付加",
    "Starting Armament Inflicts Blood Loss": "出撃時の武器に出血の状態異常を付加",
    "Starting Armament Inflicts Scarlet Rot": "出撃時の武器に腐敗の状態異常を付加",

    # === Starting Items ===
    "Stonesword Key In Possession At Start Of Expedition": "出撃時に「石剣の鍵」を持つ",
    "Small Pouch In Possession At Start Of Expedition": "出撃時に「小さなポーチ」を持つ",
    "Fire Pots In Possession At Start Of Expedition": "出撃時に「火炎壺」を持つ",
    "Magic Pots In Possession At Start Of Expedition": "出撃時に「魔力壺」を持つ",
    "Lightning Pots In Possession At Start Of Expedition": "出撃時に「雷壺」を持つ",
    "Holy Water Pots In Possession At Start Of Expedition": "出撃時に「聖水壺」を持つ",
    "Poisonbone Darts In Possession At Start Of Expedition": "出撃時に「骨の毒投げ矢」を持つ",
    "Crystal Darts In Possession At Start Of Expedition": "出撃時に「結晶投げ矢」を持つ",
    "Throwing Daggers In Possession At Start Of Expedition": "出撃時に「スローイングダガー」を持つ",
    "Glintstone Scraps In Possession At Start Of Expedition": "出撃時に「屑輝石」を持つ",
    "Gravity Stone Chunks In Possession At Start Of Expedition": "出撃時に「塊の重力石」を持つ",
    "Bewitching Branches In Possession At Start Of Expedition": "出撃時に「誘惑の枝」を持つ",
    "Wraith Calling Bell In Possession At Start Of Expedition": "出撃時に「呪霊喚びの鈴」を持つ",
    "Fire Grease In Possession At Start Of Expedition": "出撃時に「火脂」を持つ",
    "Magic Grease In Possession At Start Of Expedition": "出撃時に「魔力脂」を持つ",
    "Lightning Grease In Possession At Start Of Expedition": "出撃時に「雷脂」を持つ",
    "Holy Grease In Possession At Start Of Expedition": "出撃時に「聖脂」を持つ",
    "Shield Grease In Possession At Start Of Expedition": "出撃時に「盾脂」を持つ",
    "Starlight Shards In Possession At Start Of Expedition": "出撃時に「星光の欠片」を持つ",
    "Uplifting Aromatic In Possession At Start Of Expedition": "出撃時に「奮起の芳香」を持つ",
    "Spark Aromatic In Possession At Start Of Expedition": "出撃時に「火花の芳香」を持つ",
    "Ironjar Aromatic In Possession At Start Of Expedition": "出撃時に「鋼壺の芳香」を持つ",
    "Bloodboil Aromatic In Possession At Start Of Expedition": "出撃時に「沸血の芳香」を持つ",
    "Poison Spraymist In Possession At Start Of Expedition": "出撃時に「毒の噴霧」を持つ",
    "Acid Spraymist In Possession At Start Of Expedition": "出撃時に「酸の噴霧」を持つ",

    # === Crystal Tears ===
    "Crimsonspill Crystal Tear In Possession At Start Of Expedition": "出撃時に「赤色の秘雫」を持つ",
    "Crimson Crystal Tear In Possession At Start Of Expedition": "出撃時に「赤雫の結晶雫」を持つ",
    "Cerulean Crystal Tear In Possession At Start Of Expedition": "出撃時に「青雫の結晶雫」を持つ",
    "Speckled Hardtear In Possession At Start Of Expedition": "出撃時に「斑の硬雫」を持つ",
    "Crimson Bubbletear In Possession At Start Of Expedition": "出撃時に「赤泡の結晶雫」を持つ",
    "Opaline Bubbletear In Possession At Start Of Expedition": "出撃時に「虹泡の結晶雫」を持つ",
    "Crimsonburst Crystal Tear In Possession At Start Of Expedition": "出撃時に「赤花の結晶雫」を持つ",
    "Greenburst Crystal Tear In Possession At Start Of Expedition": "出撃時に「緑花の結晶雫」を持つ",
    "Opaline Hardtear In Possession At Start Of Expedition": "出撃時に「虹の硬雫」を持つ",
    "Thorny Cracked Tear In Possession At Start Of Expedition": "出撃時に「棘のヒビ雫」を持つ",
    "Spiked Cracked Tear In Possession At Start Of Expedition": "出撃時に「尖ったヒビ雫」を持つ",
    "Windy Crystal Tear In Possession At Start Of Expedition": "出撃時に「風の結晶雫」を持つ",
    "Ruptured Crystal Tear In Possession At Start Of Expedition": "出撃時に「裂けた結晶雫」を持つ",
    "Leaden Hardtear In Possession At Start Of Expedition": "出撃時に「鉛の硬雫」を持つ",
    "Twiggy Cracked Tear In Possession At Start Of Expedition": "出撃時に「枝のヒビ雫」を持つ",
    "Crimsonwhorl Bubbletear In Possession At Start Of Expedition": "出撃時に「赤渦の結晶雫」を持つ",
    "Cerulean Hidden Tear In Possession At Start Of Expedition": "出撃時に「青色の秘雫」を持つ",
    "Stonebarb Cracked Tear In Possession At Start Of Expedition": "出撃時に「岩のヒビ雫」を持つ",
    "Flame Shrouding Cracked Tear In Possession At Start Of Expedition": "出撃時に「炎のヒビ雫」を持つ",
    "Magic Shrouding Cracked Tear In Possession At Start Of Expedition": "出撃時に「魔力のヒビ雫」を持つ",
    "Lightning Shrouding Cracked Tear In Possession At Start Of Expedition": "出撃時に「雷のヒビ雫」を持つ",
    "Holy Shrouding Cracked Tear In Possession At Start Of Expedition": "出撃時に「聖のヒビ雫」を持つ",
    "Greenspill Crystal Tear In Possession At Start Of Expedition": "出撃時に「緑色の秘雫」を持つ",

    # === Skill changes ===
    "Changes Compatible Armaments Skill To Glintblade Phalanx At Start Of Expedition": "出撃時の武器の戦技を「輝剣の円陣」にする",
    "Changes Compatible Armaments Skill To Gravitas At Start Of Expedition": "出撃時の武器の戦技を「グラビタス」にする",
    "Changes Compatible Armaments Skill To Flaming Strike At Start Of Expedition": "出撃時の武器の戦技を「炎撃」にする",
    "Changes Compatible Armaments Skill To Eruption At Start Of Expedition": "出撃時の武器の戦技を「溶岩噴火」にする",
    "Changes Compatible Armaments Skill To Thunderbolt At Start Of Expedition": "出撃時の武器の戦技を「落雷」にする",
    "Changes Compatible Armaments Skill To Lightning Slash At Start Of Expedition": "出撃時の武器の戦技を「雷撃斬」にする",
    "Changes Compatible Armaments Skill To Sacred Blade At Start Of Expedition": "出撃時の武器の戦技を「聖なる刃」にする",
    "Changes Compatible Armaments Skill To Prayerful Strike At Start Of Expedition": "出撃時の武器の戦技を「祈りの一撃」にする",
    "Changes Compatible Armaments Skill To Poisonous Mist At Start Of Expedition": "出撃時の武器の戦技を「毒の霧」にする",
    "Changes Compatible Armaments Skill To Poison Moth Flight At Start Of Expedition": "出撃時の武器の戦技を「毒蛾は二度舞う」にする",
    "Changes Compatible Armaments Skill To Blood Blade At Start Of Expedition": "出撃時の武器の戦技を「血の刃」にする",
    "Changes Compatible Armaments Skill To Seppuku At Start Of Expedition": "出撃時の武器の戦技を「切腹」にする",
    "Changes Compatible Armaments Skill To Chilling Mist At Start Of Expedition": "出撃時の武器の戦技を「冷気の霧」にする",
    "Changes Compatible Armaments Skill To Hoarfrost Stomp At Start Of Expedition": "出撃時の武器の戦技を「霜踏み」にする",
    "Changes Compatible Armaments Skill To White Shadows Lure At Start Of Expedition": "出撃時の武器の戦技を「白い影の誘い」にする",
    "Changes Compatible Armaments Skill To Endure At Start Of Expedition": "出撃時の武器の戦技を「我慢」にする",
    "Changes Compatible Armaments Skill To Quickstep At Start Of Expedition": "出撃時の武器の戦技を「クイックステップ」にする",
    "Changes Compatible Armaments Skill To Storm Stomp At Start Of Expedition": "出撃時の武器の戦技を「嵐脚」にする",
    "Changes Compatible Armaments Skill To Determination At Start Of Expedition": "出撃時の武器の戦技を「デターミネーション」にする",
    "Changes Compatible Armaments Skill To Rain Of Arrows At Start Of Expedition": "出撃時の武器の戦技を「アローレイン」にする",

    # === Sorcery changes ===
    "Changes Compatible Armaments Sorcery To Magic Glintblade At Start Of Expedition": "出撃時の武器の魔術を「魔術の輝剣」にする",
    "Changes Compatible Armaments Sorcery To Carian Greatsword At Start Of Expedition": "出撃時の武器の魔術を「カーリアの大剣」にする",
    "Changes Compatible Armaments Sorcery To Night Shard At Start Of Expedition": "出撃時の武器の魔術を「夜のつぶて」にする",
    "Changes Compatible Armaments Sorcery To Magma Shot At Start Of Expedition": "出撃時の武器の魔術を「溶岩弾」にする",
    "Changes Compatible Armaments Sorcery To Briars Of Punishment At Start Of Expedition": "出撃時の武器の魔術を「罰の茨」にする",

    # === Incantation changes ===
    "Changes Compatible Armaments Incantation To Wrath Of Gold At Start Of Expedition": "出撃時の武器の祈祷を「黄金の怒り」にする",
    "Changes Compatible Armaments Incantation To Lightning Spear At Start Of Expedition": "出撃時の武器の祈祷を「雷の槍」にする",
    "Changes Compatible Armaments Incantation To Oflame At Start Of Expedition": "出撃時の武器の祈祷を「火よ！」にする",
    "Changes Compatible Armaments Incantation To Beast Claw At Start Of Expedition": "出撃時の武器の祈祷を「獣爪」にする",
    "Changes Compatible Armaments Incantation To Dragonfire At Start Of Expedition": "出撃時の武器の祈祷を「竜炎」にする",

    # === Powers ===
    "Power Of Dark Moon": "暗月の力",
    "Power Of Despair": "絶望の力",
    "Power Of Destined Death": "宿命の死の力",
    "Power Of Destruction": "破壊の力",
    "Power Of Full Moon": "満月の力",
    "Power Of House Marais": "マリスの力",
    "Power Of Night And Flame": "夜と炎の力",
    "Power Of The Ancestral Spirit": "祖霊の力",
    "Power Of The Blasphemous": "冒涜の力",
    "Power Of The Blood Lord": "血の君主の力",
    "Power Of The Dragonlord": "竜王の力",
    "Power Of The First Lord": "初代王の力",
    "Power Of The Flying Dragon": "飛竜の力",
    "Power Of The General": "将軍の力",
    "Power Of The Giant": "巨人の力",
    "Power Of The Golden Lineage": "黄金の血統の力",
    "Power Of The Golden Order": "黄金律の力",
    "Power Of The Great Ancient Dragon": "古竜の力",
    "Power Of The Greater Will": "大いなる意志の力",
    "Power Of The Lightless Void": "光なき虚ろの力",
    "Power Of The Omen King": "忌み王の力",
    "Power Of The Queen": "女王の力",
    "Power Of The Starscourge": "星砕きの力",
    "Power Of The Undefeated": "不敗の力",
    "Power Of Vengeance": "復讐の力",

    # === Grief ===
    "The Wylders Grief": "追跡者の悲嘆",
    "The Guardians Grief": "守護者の悲嘆",
    "The Ironeyes Grief": "鉄の目の悲嘆",
    "The Duchess Grief": "レディの悲嘆",
    "The Raiders Grief": "無頼漢の悲嘆",
    "The Revenants Grief": "復讐者の悲嘆",
    "The Recluses Grief": "隠者の悲嘆",
    "The Executors Grief": "執行者の悲嘆",
    "The Scholars Grief": "学者の悲嘆",
    "The Undertakers Grief": "葬儀屋の悲嘆",

    # === Attack Boost (talisman-like) ===
    "Attack Boost Lifeforms Born Of Falling Stars": "星の末裔への攻撃力上昇",
    "Attack Boost Those Who Live In Death": "死に生きる者への攻撃力上昇",
    "Attack Boost Dragons": "竜への攻撃力上昇",

    # === Character-specific (Wylder / 追跡者) ===
    "Wylder Additional Character Skill Use": "【追跡者】スキルの使用回数+1",
    "Wylder Art Gauge Greatly Filled When Ability Activated": "【追跡者】アビリティ発動時、アーツゲージ増加",
    "Wylder Character Skill Inflicts Blood Loss": "【追跡者】スキルに、出血の状態異常を付加",
    "Wylder Improved Mind Reduced Vigor": "【追跡者】精神力上昇、生命力低下",
    "Wylder Improved Intelligence And Faith Reduced Strength And Dexterity": "【追跡者】知力/信仰上昇、筋力/技量低下",
    "Wylder Art Activation Spreads Fire In Area": "【追跡者】アーツ発動時、周囲を延焼",
    "Wylder Standard Attacks Enhanced With Fiery Follow Ups When Using Character Skill": "【追跡者】スキル使用時、通常攻撃で炎を纏った追撃を行う",
    "Wylder Improved Attack Power When Ability Activated": "【追跡者】アビリティ発動時、攻撃力上昇",
    "Wylder Improved Attack Power When Character Skill Activated": "【追跡者】スキル発動時、攻撃力上昇",
    "Wylder Impaired Damage Negation Improved Attack Power Stamina After Art Activation": "【追跡者】アーツ発動後、カット率低下＆攻撃力/スタミナ上昇",
    "Wylder Reduced Cooldown Time For Character Skill": "【追跡者】スキルクールタイム軽減",

    # === Guardian / 守護者 ===
    "Guardian Slowly Restores Nearby Allies Hp": "【守護者】アーツ発動時、周囲の味方HPを徐々に回復",
    "Guardian Character Skill Boosts Damage Negation Of Nearby Allies": "【守護者】スキル使用時、周囲の味方のカット率上昇",
    "Guardian Improved Strength And Dexterity Reduced Vigor": "【守護者】筋力/技量上昇、生命力低下",
    "Guardian Improved Mind And Faith Reduced Vigor": "【守護者】精神力/信仰上昇、生命力低下",
    "Guardian Improved Character Skill Range": "【守護者】スキルの効果範囲拡大",
    "Guardian Increased Duration For Character Skill": "【守護者】スキルの持続時間延長",
    "Guardian Damage Negation For Allies Improved": "【守護者】味方のカット率上昇効果を強化",
    "Guardian Creates Whirlwind When Charging Halberd": "【守護者】斧槍タメ攻撃時、つむじ風が発生",
    "Guardian Restores Allies Hpwhen Character Skill Used": "【守護者】スキル使用時、味方のHP回復",
    "Guardian Character Skill Inflicts Holy Damage": "【守護者】スキルに聖ダメージを付加",
    "Guardian Become Target Of Enemy Aggression": "【守護者】敵に狙われやすくなる",
    "Guardian Successful Guards Send Out Shockwaves": "【守護者】ガード成功時、衝撃波が発生",

    # === Ironeye / 鉄の目 ===
    "Ironeye Additional Character Skill Use": "【鉄の目】スキルの使用回数+1",
    "Ironeye Character Skill Inflicts Heavy Poison Damage On Poisoned Enemies": "【鉄の目】スキルに毒を付加し、毒状態の敵に大ダメージ",
    "Ironeye Art Charge Activation Adds Poison Effect": "【鉄の目】アーツのタメ発動時、毒の状態異常を付加",
    "Ironeye Boosts Thrusting Counterattacks After Art": "【鉄の目】アーツ発動後、刺突カウンター強化",
    "Ironeye Extends Duration Of Weak Point": "【鉄の目】弱点の持続時間を延長",
    "Ironeye Improved Arcane Reduced Dexterity": "【鉄の目】神秘上昇、技量低下",
    "Ironeye Improved Vigor And Strength Reduced Dexterity": "【鉄の目】生命力/筋力上昇、技量低下",

    # === Duchess / レディ ===
    "Duchess Improved Character Skill Attack Power": "【レディ】スキルのダメージ上昇",
    "Duchess Use Character Skill For Brief Invulnerability": "【レディ】スキル使用時、僅かに無敵",
    "Duchess Defeating Enemies While Art Active Ups Attack": "【レディ】アーツ発動中、敵撃破で攻撃力上昇",
    "Duchess Dagger Chain Attack Reprises": "【レディ】短剣による攻撃連続時、周囲の敵に直近の出来事を再演",
    "Duchess Become Stealthy After Crit From Behind": "【レディ】背後からの致命の一撃後、自身の姿を隠す",
    "Duchess Duration Of Ultimate Art Extended": "【レディ】アーツの効果時間延長",
    "Duchess Character Skill Inflicts Sleep": "【レディ】スキルに睡眠の状態異常を付加",
    "Duchess Improved Vigor And Strength Reduced Mind": "【レディ】生命力/筋力上昇、精神力低下",
    "Duchess Improved Mind And Faith Reduced Intelligence": "【レディ】精神力/信仰上昇、知力低下",

    # === Raider / 無頼漢 ===
    "Raider Character Skill Damage Up": "【無頼漢】スキル中に攻撃を受けると攻撃力と最大スタミナ上昇",
    "Raider Hit With Character Skill To Reduce Enemy Attack Power": "【無頼漢】スキル命中時、敵の攻撃力低下",
    "Raider Damage Taken While Using Character Skill Improves Attack": "【無頼漢】スキル中に被ダメージで攻撃力上昇",
    "Raider Duration Of Ultimate Art Extended": "【無頼漢】アーツの効果時間延長",
    "Raider Permanently Increase Attack Power": "【無頼漢】攻撃力が恒久的に上昇",
    "Raider Improved Mind And Intelligence Reduced Vigor And Endurance": "【無頼漢】精神力/知力上昇、生命力/持久力低下",
    "Raider Improved Arcane Reduced Vigor": "【無頼漢】神秘上昇、生命力低下",

    # === Revenant / 復讐者 ===
    "Revenant Expend Own Hpto Fully Heal Nearby Allies": "【復讐者】自身のHPと引き換えに周囲の味方のHPを全回復",
    "Revenant Increased Max Fpupon Ability Activation": "【復讐者】アビリティ発動時、最大FP上昇",
    "Revenant Trigger Ghostflame Explosion During Ultimate Art Activation": "【復讐者】アーツ発動時、霊炎の爆発を発生",
    "Revenant Strengthens Family And Allies When Ultimate Art Activated": "【復讐者】アーツ発動時、ファミリーと味方を強化",
    "Revenant Power Up While Fighting Alongside Family": "【復讐者】ファミリーと共闘中、自身を強化",
    "Revenant Ability Activation Chance Increased": "【復讐者】アビリティ発動確率上昇",
    "Revenant Improved Vigor And Endurance Reduced Mind": "【復讐者】生命力/持久力上昇、精神力低下",
    "Revenant Improved Strength Reduced Faith": "【復讐者】筋力上昇、信仰低下",

    # === Recluse / 隠者 ===
    "Recluse Suffer Blood Loss And Increase Attack Power": "【隠者】自身が出血状態になり、攻撃力上昇",
    "Recluse Collect Affinity Residues To Negate Affinity": "【隠者】属性痕を集めた時、対応する属性カット率上昇",
    "Recluse Collecting 4Affinity Residues Improves Affinity Attack Power": "【隠者】属性痕を4つ集めた時、属性攻撃力上昇",
    "Recluse Collecting Affinity Residue Activates Terra Magica": "【隠者】属性痕を集めた時、「魔術の地」が発動",
    "Recluse Activating Ultimate Art Raises Max Hp": "【隠者】アーツ発動時、最大HP上昇",
    "Recluse Extends Duration Of Blood Sigils": "【隠者】血の印の持続時間延長",
    "Recluse Improved Vigor Endurance And Dexterity Reduced Intelligence And Faith": "【隠者】生命力/持久力/技量上昇、知力/信仰低下",
    "Recluse Improved Intelligence And Faith Reduced Mind": "【隠者】知力/信仰上昇、精神力低下",

    # === Executor / 執行者 ===
    "Executor Unlocking Cursed Sword Restores Hp": "【執行者】スキル中、妖刀が解放状態になるとHP回復",
    "Executor Roaring Restores Hpwhile Art Active": "【執行者】アーツ発動中、咆哮でHP回復",
    "Executor Slowly Restore Hpupon Ability Activation": "【執行者】アビリティ発動時、HPをゆっくりと回復",
    "Executor Attack Power Up While Ultimate Art Active": "【執行者】アーツ発動中、攻撃力上昇",
    "Executor Improves Effect But Lowers Resistance": "【執行者】効果を強化するが耐性が低下",
    "Executor Character Skill Boosts Attack But Drains Hp": "【執行者】スキル使用で攻撃力上昇、HP減少",
    "Executor Improved Vigor And Endurance Reduced Arcane": "【執行者】生命力/持久力上昇、神秘低下",
    "Executor Improved Dexterity And Arcane Reduced Vigor": "【執行者】技量/神秘上昇、生命力低下",

    # === Scholar / 学者 ===
    "Scholar Allies Targeted By Character Skill Gain Boosted Attack": "【学者】スキル使用時、対象に含まれた味方の攻撃力上昇",
    "Scholar Reduced Fp Consumption When Using Character Skill On Self": "【学者】スキルを自身に使用時、FP消費軽減",
    "Scholar Prevent Slowing Of Character Skill Progress": "【学者】スキルの進捗率の低下を抑制",
    "Scholar Earn Runes For Each Additional Specimen Acquired With Character Skill": "【学者】スキルによる標本が増える度、ルーンを取得",
    "Scholar Continuous Damage Inflicted On Targets Threaded By Ultimate Art": "【学者】アーツでリンクした敵対象に、継続ダメージ",
    "Scholar Improved Mind Reduced Vigor": "【学者】精神力上昇、生命力低下",
    "Scholar Improved Endurance And Dexterity Reduced Intelligence And Arcane": "【学者】持久力/技量上昇、知力/神秘低下",

    # === Undertaker / 葬儀屋 ===
    "Undertaker Executing Art Readies Character Skill": "【葬儀屋】アーツ発動後、スキル再使用可能",
    "Undertaker Activating Ultimate Art Increases Attack Power": "【葬儀屋】アーツ発動時、攻撃力上昇",
    "Undertaker Attack Power Increased By Landing The Final Blow Of Achain Attack": "【葬儀屋】連撃の最終攻撃命中時、攻撃力上昇",
    "Undertaker Physical Attacks Boosted While Assist Effect From Incantation Is Active For Self": "【葬儀屋】祈祷による補助効果発生時、物理攻撃力上昇",
    "Undertaker Contact With Allies Restores Their Hp While Ultimate Art Is Activated": "【葬儀屋】アーツ発動時、触れた味方のHP回復",
    "Undertaker Improved Dexterity Reduced Vigor And Faith": "【葬儀屋】技量上昇、生命力/信仰低下",
    "Undertaker Improved Mind And Faith Reduced Strength": "【葬儀屋】精神力/信仰上昇、筋力低下",

    # === Equipped weapons bonuses ===
    "Max Fp Up With 3Plus Staves Equipped": "杖を3つ以上装備していると最大FP上昇",
    "Max Fp Up With 3Plus Sacred Seals Equipped": "聖印を3つ以上装備していると最大FP上昇",
    "Max Hp Up With 3Plus Small Shields Equipped": "小盾を3つ以上装備していると最大HP上昇",
    "Max Hp Up With 3Plus Medium Shields Equipped": "中盾を3つ以上装備していると最大HP上昇",
    "Max Hp Up With 3Plus Greatshields Equipped": "大盾を3つ以上装備していると最大HP上昇",
}

# ============================================================
# Weapon type mappings for pattern-based translation
# ============================================================
WEAPON_MAP = {
    "Dagger": "短剣", "Daggers": "短剣",
    "Straight Sword": "直剣", "Straight Swords": "直剣",
    "Greatsword": "大剣", "Greatswords": "大剣",
    "Colossal Sword": "特大剣", "Colossal Swords": "特大剣",
    "Curved Sword": "曲剣", "Curved Swords": "曲剣",
    "Curved Greatsword": "大曲剣", "Curved Greatswords": "大曲剣",
    "Katana": "刀",
    "Twinblade": "両刃剣", "Twinblades": "両刃剣",
    "Thrusting Sword": "刺剣", "Thrusting Swords": "刺剣",
    "Heavy Thrusting Sword": "重刺剣", "Heavy Thrusting Swords": "重刺剣",
    "Axe": "斧", "Axes": "斧",
    "Greataxe": "大斧", "Greataxes": "大斧",
    "Hammer": "槌", "Hammers": "槌",
    "Great Hammer": "大槌", "Great Hammers": "大槌",
    "Flail": "フレイル", "Flails": "フレイル",
    "Spear": "槍", "Spears": "槍",
    "Pike": "パイク", "Pikes": "パイク",
    "Great Spear": "大槍", "Great Spears": "大槍",
    "Halberd": "斧槍", "Halberds": "斧槍",
    "Reaper": "鎌", "Reapers": "鎌",
    "Fist": "拳", "Fists": "拳",
    "Claw": "爪", "Claws": "爪",
    "Whip": "鞭", "Whips": "鞭",
    "Colossal Weapon": "特大武器", "Colossal Weapons": "特大武器",
    "Bow": "弓", "Bows": "弓",
    "Greatbow": "大弓", "Greatbows": "大弓",
    "Crossbow": "ボウガン", "Crossbows": "ボウガン",
    "Ballista": "バリスタ", "Ballistas": "バリスタ",
    "Small Shield": "小盾", "Small Shields": "小盾",
    "Medium Shield": "中盾", "Medium Shields": "中盾",
    "Greatshield": "大盾", "Greatshields": "大盾",
    "Stave": "杖", "Staves": "杖",
    "Sacred Seal": "聖印", "Sacred Seals": "聖印",
    "Torch": "松明", "Torches": "松明",
}

# Sort by length descending to match longest first
WEAPON_KEYS_SORTED = sorted(WEAPON_MAP.keys(), key=len, reverse=True)


def translate_weapon_pattern(name):
    """Handle weapon-type based patterns"""
    # HP Restoration Upon [Weapon] Attacks
    for wk in WEAPON_KEYS_SORTED:
        if name == f"Hp Restoration Upon {wk} Attacks":
            return f"{WEAPON_MAP[wk]}の攻撃でHP回復"
        if name == f"Fp Restoration Upon {wk} Attacks":
            return f"{WEAPON_MAP[wk]}の攻撃でFP回復"
        if name == f"Improved {wk} Attack Power":
            return f"{WEAPON_MAP[wk]}の攻撃力上昇"
        pat = f"Improved Attack Power With 3Plus {wk} Equipped"
        if name == pat:
            return f"{WEAPON_MAP[wk]}を3つ以上装備していると攻撃力上昇"
        pat2 = f"Dormant Power Helps Discover {wk}"
        if name == pat2:
            return f"潜在する力から、{WEAPON_MAP[wk]}を見つけやすくなる"
    return None


def translate_name(name):
    """Translate an English effect name to Japanese"""
    # 1. Try exact match (case-insensitive title case)
    # Normalize: the data has Title Case names
    if name in EXACT_MAP:
        return EXACT_MAP[name]

    # 2. Try weapon-based patterns
    result = translate_weapon_pattern(name)
    if result:
        return result

    # 3. If nothing matched, return None
    return None


def main():
    input_file = "/c/Users/owner/Desktop/Apps/DockerSandboxWs/ERN_RelicForge/resources/effects_data.json"

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    effects = data.get('effects', {})
    translated = 0
    missing = []

    for eid, edata in effects.items():
        en_name = edata.get('name', '')
        ja_name = translate_name(en_name)

        # Rename name -> name_en, add name_ja
        edata['name_en'] = en_name
        if ja_name:
            edata['name_ja'] = ja_name
            translated += 1
        else:
            edata['name_ja'] = en_name  # fallback to English
            missing.append(f"{eid}: {en_name}")

        # Remove old 'name' key
        if 'name' in edata:
            del edata['name']

    # Write output
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Total effects: {len(effects)}")
    print(f"Translated: {translated}")
    print(f"Missing (fallback to English): {len(missing)}")
    if missing:
        print("\n--- Missing translations ---")
        for m in missing:
            print(f"  {m}")


if __name__ == '__main__':
    main()
