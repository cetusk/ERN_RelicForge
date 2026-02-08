#!/usr/bin/env python3
"""
Add stacking information to effects_data.json based on kamikouryaku.net rules.

For each effect entry, adds:
  - stackable: true, false, or "conditional"
  - stackNotes: string with Japanese notes (empty string if none)
"""

import json
import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
EFFECTS_FILE = os.path.join(PROJECT_DIR, "resources", "effects_data.json")

# Character name prefixes for character-specific effects
CHARACTER_PREFIXES = (
    "wylder", "guardian", "ironeye", "duchess", "raider",
    "revenant", "recluse", "executor", "scholar", "undertaker",
)

# ============================================================
# ID-specific overrides (highest priority)
# ============================================================
ID_OVERRIDES = {
    # Standard increasedMaximumHP -> NOT stackable
    "310000": (False, "深層版は重複可"),
    "310400": (False, "深層版は重複可"),
    # Deep relic increasedMaximumHP -> stackable
    "6610400": (True, ""),
    # 7000090 is also increasedMaximumHP but from stat bonuses context (vigor sub-effect)
    # treat similarly to standard
    "7000090": (False, "深層版は重複可"),
    # 8000000, 8000001 are also increasedMaximumHP from armor/talisman context
    "8000000": (False, "深層版は重複可"),
    "8000001": (False, "深層版は重複可"),
}


def get_stacking_info(effect_id: str, key: str) -> tuple:
    """
    Determine stacking info for an effect.
    Returns (stackable, stackNotes) tuple.
    stackable is True, False, or "conditional".
    """

    # ---- ID-specific overrides ----
    if effect_id in ID_OVERRIDES:
        return ID_OVERRIDES[effect_id]

    # ---- KEY-based rules (order matters) ----

    # == Grief effects (character-specific grief) ==
    if key.endswith("Grief"):
        return (False, "キャラクター固有効果")

    # == Character-specific effects ==
    # Check character prefix patterns
    for prefix in CHARACTER_PREFIXES:
        if key.startswith(prefix) or key.startswith("the" + prefix.capitalize()):
            return (False, "キャラクター固有効果")
    # Also match "theWylders", "theGuardians", etc. (possessive forms)
    if re.match(r'^the(Wylder|Guardian|Ironeye|Duchess|Raider|Revenant|Recluse|Executor|Scholar|Undertaker)', key):
        return (False, "キャラクター固有効果")

    # == Power of effects (boss remembrance powers) ==
    if key.startswith("powerOf"):
        return (False, "")

    # == Stat bonuses (+N variants) ==
    stat_bonus_prefixes = (
        "vigorPlus", "mindPlus", "endurancePlus", "strengthPlus",
        "dexterityPlus", "intelligencePlus", "faithPlus", "arcanePlus",
        "poisePlus",
    )
    for prefix in stat_bonus_prefixes:
        if key.startswith(prefix):
            return (True, "")

    # == Improved Poise ==
    if key == "improvedPoise":
        return (True, "")

    # == Improved Dexterity ==
    if key == "improvedDexterity":
        return (True, "")

    # == Max FP / Max Stamina (always stackable) ==
    if key.startswith("increasedMaximumFP") or key == "raisesMaximumFpPlus1":
        return (True, "")
    if key.startswith("increasedMaximumStamina"):
        return (True, "")

    # == increasedMaximumHP without ID override -> default false ==
    if key == "increasedMaximumHP":
        return (False, "深層版は重複可")

    # == Attack power up (multiplicative, all stackable) ==
    attack_up_patterns = [
        "physicalAttackUp", "magicAttackPowerUp", "fireAttackPowerUp",
        "lightningAttackPowerUp", "holyAttackPowerUp",
        "raisesPhysicalAttackPowerPlus",
    ]
    for pat in attack_up_patterns:
        if key.startswith(pat):
            return (True, "")

    # == Improved attack power types ==
    improved_attack_stackable = [
        "improvedMeleeAttackPower",
        "improvedSkillAttackPower",
        "improvedPhysicalAttackPower",
        "improvedMagicAttackPower",
        "improvedFireAttackPower",
        "improvedLightningAttackPower",
        "improvedHolyAttackPower",
        "improvedNonPhysicalAttackPower",
        "improvedInitialStandardAttack",
        "improvedRoarAndBreathAttacks",
        "improvedStanceBreakingWhenTwoHanding",
        "improvedStanceBreakingWhenWieldingTwoArmaments",
        "boostsAttackPowerOfAddedAffinityAttacks",
        "improvedAffinityAttackPower",
        "improvedGuardCounters",
        "improvedGuardBreaking",
        "improvedChargeAttacks",
        "improvedChargedSpellsAndSkills",
        "improvedJumpAttacks",
        "improvedChainAttackFinishers",
        "improvedRangedWeaponAttacks",
        "projectileDamageDropOffReduced",
        "improvedThrowingPots",
        "improvedThrowingPotDamage",
        "improvedThrowingKnifeDamage",
        "improvedGlintstoneAndGravityStoneDamage",
        "improvedPerfumingArts",
        "attackUpWhenWieldingTwoArmaments",
        "improvedAttackPowerWhenTwoHanding",
        "improvedChargedSkillAttackPower",
        "improvedStanceBreaking",
    ]
    for pat in improved_attack_stackable:
        if key.startswith(pat):
            return (True, "")

    # == Improved critical hits ==
    if key == "improvedCriticalHits":
        return (True, "")
    if key.startswith("improvedCriticalHitsPlus"):
        return (False, "約1.24倍")

    # == Weapon-type attack power (improved*AttackPower for specific weapons) ==
    weapon_attack_pattern = re.compile(
        r'^improved(Dagger|StraightSword|Greatsword|ColossalSword|CurvedSword|'
        r'CurvedGreatsword|Katana|Twinblade|ThrustingSword|HeavyThrustingSword|'
        r'Axe|Greataxe|Hammer|GreatHammer|Flail|Spear|Pike|GreatSpear|'
        r'Halberd|Reaper|Fist|Claw|Whip|ColossalWeapon|Bow|Greatbow|'
        r'Crossbow|Ballista)AttackPower$'
    )
    if weapon_attack_pattern.match(key):
        return (True, "")

    # == Improved attack power at low/full HP ==
    if key == "improvedAttackPowerAtLowHP":
        return (True, "")
    if key == "improvedAttackPowerAtFullHP":
        return (True, "")

    # == Magic/Incantation improvements ==
    sorcery_incantation_stackable = [
        "improvedSorceries",
        "improvedIncantations",
        "improvedChargedSorceries",
        "improvedChargedIncantation",
        "improvedSorceriesAndIncantations",
        "raisesSorceryIncantationPotency",
        "increasedSorceryAndIncantationDuration",
    ]
    for pat in sorcery_incantation_stackable:
        if key.startswith(pat):
            return (True, "")

    # Specific sorcery types
    specific_sorceries = [
        "improvedStonediggerSorcery", "improvedCarianSwordSorcery",
        "improvedGlintbladeSorcery", "improvedInvisibilitySorcery",
        "improvedCrystalianSorcery", "improvedGravitySorcery",
        "improvedThornSorcery", "improvedNightSorcery",
    ]
    for pat in specific_sorceries:
        if key == pat:
            return (True, "")

    # Specific incantation types
    specific_incantations = [
        "improvedFundamentalistIncantations", "improvedDragonCultIncantations",
        "improvedGiantsFlameIncantations", "improvedGodslayerIncantations",
        "improvedBestialIncantations", "improvedFrenziedFlameIncantations",
        "improvedDragonCommunionIncantations",
    ]
    for pat in specific_incantations:
        if key == pat:
            return (True, "")

    # == Cut rates / Damage negation ==
    negation_stackable = [
        "improvedMagicDamageNegation",
        "improvedFireDamageNegation",
        "improvedLightningDamageNegation",
        "improvedHolyDamageNegation",
        "improvedAffinityDamageNegation",
        "improvedNonPhysicalDamageNegation",
        "raisesNonPhysicalDamageNegationPlus",
        "raisesPhysicalDamageNegationPlus",
        "magicDamageNegationUp",
        "fireDamageNegationUp",
        "lightningDamageNegationUp",
        "holyDamageNegationUp",
    ]
    for pat in negation_stackable:
        if key.startswith(pat):
            return (True, "")

    # improvedPhysicalDamageNegation base -> conditional, Plus variants -> true
    if key.startswith("improvedPhysicalDamageNegationPlus"):
        return (True, "")
    if key == "improvedPhysicalDamageNegation":
        return ("conditional", "約8%")

    # improvedDamageNegationAtLowHP / AtFullHP
    if key == "improvedDamageNegationAtLowHP":
        return (True, "")
    if key == "improvedDamageNegationAtFullHP":
        return (True, "")

    # Improved guarding ability
    if key.startswith("improvedGuardingAbility"):
        return (True, "")

    # == Resistances ==
    resistance_stackable = [
        "improvedBloodLossResistance", "improvedFrostResistance",
        "improvedPoisonResistance", "improvedRotResistance",
        "improvedSleepResistance", "improvedMadnessResistance",
        "improvedDeathBlightResistance",
        "improvedPoisonRotResistance", "improvedBloodLossAndFrostResistance",
        "improvedSleepMadnessResistance",
        "allResistanceUp", "allResistancesUp",
        "raisesResistanceToAllAilments",
    ]
    for pat in resistance_stackable:
        if key.startswith(pat):
            return (True, "")

    # == Recovery effects ==
    if key == "continuousHpRecovery":
        return (True, "2HP/秒")
    if key == "fpRestorationUponSuccessiveAttacks":
        return (True, "")
    if key == "madnessContinuallyRecoversFP":
        return (True, "2/秒、25秒間")
    if key == "improvedFlaskHPRestoration":
        return (True, "")
    if key == "defeatingEnemiesRestoresHP":
        return (True, "")
    if key == "defeatingEnemiesRestoresFP":
        return (True, "")
    if key == "successiveAttackHpRestoration":
        return (True, "")
    if key == "criticalHitHPRestoration":
        return (True, "")
    if key == "criticalHitFPRestoration":
        return (True, "")

    # == Skill / Arts ==
    if key.startswith("characterSkillCooldownReduction"):
        return (True, "")
    if key.startswith("ultimateArtAutoCharge"):
        return (True, "")

    # == Starting items ==
    if "InPossessionAtStartOfExpedition" in key:
        if key == "stoneswordKeyInPossessionAtStartOfExpedition" or key == "stoneSwordKeyInPossessionAtStartOfExpedition":
            return (False, "")
        return (True, "")

    # == War arts/skills changes ==
    if key.startswith("changesCompatibleArmamentsSkillTo"):
        return (True, "複数あっても1つのみ有効（左優先）")
    if key.startswith("changesCompatibleArmamentsSorceryTo"):
        return (True, "複数あっても1つのみ有効（左優先）")
    if key.startswith("changesCompatibleArmamentsIncantationTo"):
        return (True, "複数あっても1つのみ有効（左優先）")

    # == Team / Allies ==
    if key == "increasedRuneAcquisitionForSelfAndAllies":
        return (True, "1人あたり3.5%、最大10.5%")

    # == Consumption reduction ==
    if key.startswith("reducedFPConsumption"):
        return (True, "")
    if key == "reducedSpellFpCost":
        return (True, "")
    if key == "reducedSkillFpCost":
        return (True, "")

    # == Stamina recovery ==
    if key.startswith("improvedStaminaRecovery"):
        return (True, "")

    # == Item discovery / Runes ==
    if key == "improvedItemDiscovery":
        return (True, "")
    if key == "moreRunesFromDefeatedEnemies":
        return (True, "")

    # == Gesture ==
    if key == "gestureCrossedLegsBuildsUpMadness":
        return (True, "")

    # == Improved Spell Casting Speed ==
    if key == "improvedSpellCastingSpeed":
        return (True, "")

    # ================================================================
    # DEMERIT EFFECTS (all stackable)
    # ================================================================
    demerit_stackable = [
        "reducedVigor", "reducedEndurance", "reducedStrengthAndIntelligence",
        "reducedDexterityAndFaith", "reducedIntelligenceAndDexterity",
        "reducedFaithAndStrength", "reducedVigorAndArcane",
        "reducedRuneAcquisition", "reducedFlaskHPRestoration",
        "reducedStaminaConsumption", "reducedMaximumHP",
        "reducedMaximumFP", "reducedMaximumStamina",
        "continuousHPLoss",
        "allResistancesDown",
        "moreDamageTakenAfterEvasion",
        "ailmentsCauseIncreasedDamage",
        "attacksImpairedOnOccasion",
        "damageIncreasedByNightsEncroachment",
        "nightsTideDamageIncreased",
        "maximumHpDown",
        "impairedPhysicalDamageNegation",
        "impairedDamageNegation",
        "impairedAffinityDamageNegation",
        "takingDamageCausesPoisonBuildup",
        "takingDamageCausesRotBuildup",
        "takingDamageCausesFrostBuildup",
        "takingDamageCausesBloodLossBuildup",
        "takingDamageCausesMadnessBuildup",
        "takingDamageCausesSleepBuildup",
        "takingDamageCausesDeathBuildup",
        "ultimateArtChargingImpaired",
        "surgeSprintingDrainsMoreStamina",
        "increasedDrainOnStaminaForEvasion",
        "repeatedEvasionsLowerDamageNegation",
        "reducedDamageNegationForFlaskUsages",
        "sleepBuildupForFlaskUsages",
        "madnessBuildupForFlaskUsages",
        "lowerAttackWhenBelowMaxHP",
        "poisonBuildupWhenBelowMaxHP",
        "rotBuildupWhenBelowMaxHP",
        "maxHPReducesAttackPower",
        "nearDeathSpillsFlask",
        "nearDeathReducesMaxHP",
        "nearDeathReducesArtGauge",
        "lowerStaminaImpairsDmgNegation",
        "slowerArtGaugeWhenBelowMaxHP",
    ]
    for pat in demerit_stackable:
        if key == pat:
            return (True, "")
    # Broader pattern for "reduced*" demerits
    if key.startswith("reduced") and key not in ("reducedSpellFpCost", "reducedSkillFpCost"):
        # Already handled FP cost above; other reduced* are demerits
        return (True, "")

    # ================================================================
    # CONDITIONAL effects
    # ================================================================
    if key == "successiveAttacksBoostAttackPower":
        return ("conditional", "最大10スタックまで内部加算")
    if key == "statusAilmentGaugesSlowlyIncreaseAttackPower":
        return ("conditional", "最大10スタック、1スタックあたり約1.038倍")
    if key == "continuousFpRecovery":
        return ("conditional", "5秒に1回復")
    if key == "rotInVicinityCausesContinuousHpRecovery":
        return ("conditional", "最大HPの0.15%+15/秒")
    if key == "switchingWeaponsAddsAnAffinityAttack":
        return ("conditional", "10秒間属性+10")
    if key == "extendedSpellDuration":
        return ("conditional", "+50%")
    if key == "drawEnemyAttentionWhileGuarding":
        return ("conditional", "ガード中のみ有効")
    if key == "nearbyFrostbiteConcealsSelf":
        return ("conditional", "")
    if key == "occasionallyNullifyAttacksWhenDamageNegationsIsLowered":
        return ("conditional", "")
    if key == "improvedDodging":
        return ("conditional", "iフレーム延長")

    # attackPowerUpWhenFacing*AfflictedEnemy base -> false, Plus -> conditional
    if re.match(r'^attackPowerUpWhenFacing\w+AfflictedEnemyPlus\d+$', key):
        return ("conditional", "")
    if re.match(r'^attackPowerUpWhenFacing\w+AfflictedEnemy$', key):
        return (False, "")

    # sleepInVicinityImprovesAttackPower / Plus variants
    if key.startswith("sleepInVicinityImprovesAttackPower"):
        return ("conditional", "")
    # madnessInVicinityImprovesAttackPower / Plus variants
    if key.startswith("madnessInVicinityImprovesAttackPower"):
        return ("conditional", "")

    # bloodLossInVicinityIncreasesAttackPower
    if key == "bloodLossInVicinityIncreasesAttackPower":
        return ("conditional", "20秒間")
    # poisonAndRotInVicinityIncreasesAttackPower
    if key == "poisonAndRotInVicinityIncreasesAttackPower":
        return ("conditional", "")
    # poisonAndRotImprovesAttackPower (slight variant name)
    if key == "poisonAndRotImprovesAttackPower":
        return ("conditional", "")

    # defeatingEnemiesFillsMoreOfTheArtGaugePlus1/2
    if re.match(r'^defeatingEnemiesFillsMoreOfTheArtGaugePlus\d+$', key):
        return ("conditional", "通常版と深層版の異なるレベル同士は重複可")
    # artGaugeFillsModeratelyUponCriticalHitPlus1/2
    if re.match(r'^artGaugeFillsModeratelyUponCriticalHitPlus\d+$', key):
        return ("conditional", "")
    # artGaugeChargedFromSuccessfulGuardingPlus1/2
    if re.match(r'^artGaugeChargedFromSuccessfulGuardingPlus\d+$', key):
        return ("conditional", "")
    # hpRestorationUponThrustingCounterattackPlus1/2
    if re.match(r'^hpRestorationUponThrustingCounterattackPlus\d+$', key):
        return ("conditional", "")
    # partialHPRestorationUponPostDamageAttacksPlus1/2
    if re.match(r'^partialHPRestorationUponPostDamageAttacksPlus\d+$', key):
        return ("conditional", "")
    # hpRestoredWhenUsingMedicinalBolusesEtcPlus1/2
    if re.match(r'^hpRestoredWhenUsingMedicinalBolusesEtcPlus\d+$', key):
        return ("conditional", "")
    # physicalAttackPowerIncreasesAfterUsingGreaseItemsPlus1/2
    if re.match(r'^physicalAttackPowerIncreasesAfterUsingGreaseItemsPlus\d+$', key):
        return ("conditional", "")

    # improved*AttackPowerWith3Plus*Equipped -> conditional
    if re.match(r'^improved\w+With3Plus\w+Equipped$', key):
        return ("conditional", "異なる武器種同士は重複可")
    # max*With3Plus*Equipped -> conditional
    if re.match(r'^max\w+With3Plus\w+Equipped$', key):
        return ("conditional", "異なる武器種同士は重複可")

    # ================================================================
    # NOT STACKABLE (false)
    # ================================================================
    not_stackable_exact = {
        "switchingWeaponsBoostsAttackPower": "10秒間1.1倍",
        "takingAttacksImprovesAttackPower": "10秒間1.15倍",
        "attackPowerPermanentlyIncreasedForEachEvergaolPrisonerDefeated": "",
        "attackPowerUpAfterDefeatingANightInvader": "1体あたり約1.07倍",
        "guardCounterIsGivenABoostBasedOnCurrentHP": "",
        "staminaRecoveryUponLandingAttacks": "1ヒット+2",
        "staminaRecoveryUponLandingAttacksPlus1": "1ヒット+3",
        "criticalHitBoostsStaminaRecoverySpeed": "15秒間約15%",
        "criticalHitBoostsStaminaRecoverySpeedPlus1": "15秒間約25%",
        "criticalHitsEarnRunes": "600ルーン",
        "flaskAlsoHealsAllies": "自分-10%、味方30%",
        "itemsConferEffectToAllNearbyAllies": "",
        "raisedStaminaRecoveryForNearbyAlliesButNotForSelf": "",
        "defeatingEnemiesRestoresHPForAlliesButNotForSelf": "",
        "defeatingEnemiesRestoresNearbyAlliesHP": "",
        "showBuriedTreasureOnMap": "",
        "treasureMarkedUponMap": "",
        "hugeRuneDiscountForShopPurchasesWhileOnExpedition": "20%割引",
        "runeDiscountForShopPurchasesWhileOnExpedition": "10%割引",
        "noRuneLossOrLevelDownUponDeath": "",
        "slowlyRestoreHpForSelfAndNearbyAlliesWhenHpIsLow": "",
        "hpRecoveryFromSuccessfulGuarding": "固定+15",
        "hpRestorationUponThrustingCounterattack": "最大HPの2.5%",
        "partialHpRestorationUponPostDamageAttacks": "",
        "partialHPRestorationUponPostDamageAttacks": "",
        "hpRestoredWhenUsingMedicinalBolusesEtc": "+50回復",
        "improvedPoiseDamageNegationWhenKnockedBackByDamage": "20秒間約20%",
        "attackPowerIncreasesAfterUsingGreaseItems": "約30秒間1.1倍",
        "defeatingEnemiesFillsMoreOfTheArtGauge": "約5%",
        "artGaugeFillsModeratelyUponCriticalHit": "約5%",
        "artGaugeChargedFromSuccessfulGuarding": "約1%",
        "hpRestorationUponAttacks": "",
        "fpRestorationUponAttacks": "",
        "defeatingEnemiesNearTotemStelaRestoresHP": "",
        "criticalHitsBoostAttackPower": "",
        "damageBoostedAfterCriticalHit": "",
        "criticalHitsInflictBloodLoss": "",
        "criticalHitAddsLightningEffect": "",
        "fireCriticalHitGrantsMaxStaminaBoost": "",
        "crystalShardsUponMagicCriticalHit": "",
        "attacksCreateMagicBurstsVersusSleepingEnemies": "",
        "colossalArmamentsCoatedInRockWhenPerformingChargedAttacks": "",
        "gradualRestorationByFlask": "",
        "communionGrantsAntiDragonEffect": "",
        "bloodfliesUponPrecisionAiming": "",
        "flaskHealingAlsoRestoresFP": "",
        "fpRecoveryFromSuccessfulGuarding": "",
        "hpRestorationWithHeadShots": "",
        "failingToCastSorceryRestoresFP": "",
        "guardingUpsAttackAndCastingSpeeds": "",
        "brokenStanceActivatesEndure": "",
        "consecutiveGuardsHardenSkin": "",
        "dmgNegationUpWhileCastingSpells": "",
        "dmgNegationUpWhileChargingAttacks": "",
        "guardCountersActivateHolyAttacks": "",
        "guardCountersCastLightPillar": "",
        "guardCountersLaunchSummoningAttack": "",
        "bloodLossIncreasesAttackPower": "",
        "frostbiteIncreasesAttackPower": "",
        "poisonIncreasesAttackPower": "",
        "sleepIncreasesAttackPower": "",
        "madnessIncreasesAttackPower": "",
        "attackBoostFromNearbyAllies": "",
        "maxHPIncreasedForEachGreatEnemyDefeatedAtAGreatChurch": "",
        "runesAndItemDiscoveryIncreasedForEachGreatEnemyDefeatedAtAFort": "",
        "maxStaminaIncreasedForEachGreatEnemyDefeatedAtAGreatEncampment": "",
        "arcaneIncreasedForEachGreatEnemyDefeatedAtARuin": "",
        "maxFpPermanentlyIncreasedAfterReleasingSorcerersRiseMechanism": "",
        "improvedPoiseNearTotemStela": "",
        "improvedThrustingCounterattack": "",
        "createsHolyGroundAtLowHP": "",
        "criticalHitCreatesSleepMist": "",
    }
    if key in not_stackable_exact:
        return (False, not_stackable_exact[key])

    # Weapon-type HP/FP recovery (per weapon) -> false
    weapon_hp_fp_pattern = re.compile(
        r'^(hp|fp)RestorationUpon(Dagger|StraightSword|Greatsword|ColossalSword|'
        r'CurvedSword|CurvedGreatsword|Katana|Twinblade|ThrustingSword|'
        r'HeavyThrustingSword|Axe|Greataxe|Hammer|GreatHammer|Flail|'
        r'Spear|Pike|GreatSpear|Halberd|Reaper|Fist|Claw|Whip|'
        r'ColossalWeapon|Bow|Greatbow|Crossbow|Ballista)Attacks$'
    )
    if weapon_hp_fp_pattern.match(key):
        return (False, "クールタイムあり")

    # Starting weapon enchantments
    if key.startswith("startingArmamentInflicts") or key.startswith("startingArmamentDeals"):
        return (False, "左優先、1つのみ有効")
    if key.startswith("armamentDeals"):
        return (False, "左優先、1つのみ有効")
    if key in ("addFireToWeapon", "addMagicToWeapon", "addLightningToWeapon", "addHolyToWeapon"):
        return (False, "左優先、1つのみ有効")

    # Dormant power effects
    if key.startswith("dormantPowerHelpsDiscover"):
        return (False, "左優先")

    # All "changedStrongAttacks" variants
    if key.startswith("changedStrongAttacks"):
        return (False, "")

    # On-critical-hit action effects
    crit_action_keys = [
        "bloodLossCritThornsOfPunishment", "rotCriticalHitFiresPestThreads",
        "poisonMistUponPoisonCriticalHit", "iceStormUponCriticalHitWithFrost",
        "madnessCritHitFiresFrenziedFlame", "deathCritHitCallsDeathLightning",
        "sacredOrderUponHolyCriticalHit", "magmaUponFireCriticalHit",
        "lightningCriticalHitImbuesArmament", "lowHpCritHitFullyRestoresHP",
        "criticalHitsDealHugeDamageOnPoisonedEnemies",
    ]
    if key in crit_action_keys:
        return (False, "")

    # Upon charged thrust/slash effects
    if re.match(r'.*Upon(Charged)?(Thrust|Slash|Strike)$', key) and key not in improved_attack_stackable:
        return (False, "")

    # Defeating group effects
    if key.startswith("defeatingGroup"):
        return (False, "")

    # Walking/triggered effects
    walking_triggered = [
        "darknessConcealsCasterWhileWalking",
        "flameOfFrenzyWhileWalking",
        "savageFlamesRoarWhileWalking",
        "wraithsWhileWalking",
        "viciousStarRainPoursWhileWalking",
        "stormOfRedLightningWhileWalking",
        "magmaSurgeSprint", "iceStormSurgeSprint",
        "surgeSprintLandingsSplitEarth",
    ]
    if key in walking_triggered:
        return (False, "")

    # Attack boost vs specific enemy types
    if key.startswith("attackBoost"):
        return (False, "")

    # Attacks inflict ailments (base -> false, Plus -> conditional)
    if re.match(r'^attacksInflict\w+Plus\d+$', key):
        return ("conditional", "")
    if re.match(r'^attacksInflict\w+$', key):
        return (False, "")
    if key == "attacksInflictRotWhenDamageIsTaken":
        return (False, "")

    # ================================================================
    # Remaining miscellaneous effects
    # ================================================================
    misc_false = [
        "strongAttackCreatesWideWaveOfHeat",
        "jumpingConjuresMagicProjectiles",
        "performingConsecutiveSuccessfulGuardsImprovesGuardAbilityAndDeflectsBigAttacks",
        "shockwaveProducedFromSuccessfulGuarding",
        "parriesActivateGoldenRetaliation",
        "lightningUponDodging",
        "lightningUponPrecisionAiming",
        "poisonMistUponPrecisionAiming",
        "rotMistUponPrecisionAiming",
        "projectilesLaunchedUponAttacks",
        "shieldingImprovesDamageNegation",
        "shieldingInvokesIndomitableVow",
        "shieldingCreatesHolyGround",
        "poisonProducesAMistOfPoison",
        "madnessProducesAFlameOfFrenzy",
        "rotProducesAMistOfScarletRot",
        "frostbiteProducesAMistOfFrost",
        "sleepProducesAMistOfSleep",
        "magicAttackFollowsChargeAttacks",
        "fireAttackFollowsChargeAttacks",
        "lightningFollowsChargeAttacks",
        "holyAttackFollowsChargeAttacks",
        "multiplePeriodicalGlintblades",
        "manyPeriodicalGlintblades",
        "periodicalGiantGlintblades",
        "successiveAttacksNegateDamage",
        "takingDamageRestoresFp",
        "takingDamageBoostsDamageNegation",
        "hpRestorationUponSuccessiveAttacks",
        "strongAttacksImprovePoise",
        "skillActivationImprovesPoise",
        "successfulGuardingUpsPoise",
        "successfulGuardingUpsDmgNegation",
        "hpRecoveryFromSuccessfulGuardingPlus",
        "suddenEnemyDeathUponAttacks",
        "lessLikelyToBeTargeted",
        "runeOfTheStrong",
        "runes60kAtStart30kOnDeath",
        "ultimateArtGaugeChargeSpeedUp",
        "improvedStanceBreakingWithHeadShots",
        "strongJumpAttacksCreateShockwave",
    ]
    if key in misc_false:
        return (False, "")

    # ================================================================
    # FALLBACK LOGIC
    # ================================================================

    # 1. Character name prefix
    for prefix in CHARACTER_PREFIXES:
        lower_key = key[0].lower() + key[1:] if key else key
        if lower_key.startswith(prefix):
            return (False, "キャラクター固有効果")

    # 2. InPossessionAtStartOfExpedition
    if "InPossessionAtStartOfExpedition" in key or "inPossessionAtStartOfExpedition" in key:
        return (True, "")

    # 3. Plus variants of stackable base
    plus_match = re.match(r'^(.+?)Plus(\d+)$', key)
    if plus_match:
        base_key = plus_match.group(1)
        # Try to determine base stacking
        # If we can't determine, default to false
        pass

    # 4. Attacks + ailment pattern
    if re.match(r'^attacksInflict', key):
        return (False, "")

    # 5. Default: false with empty note (conservative)
    return (False, "")


def main():
    with open(EFFECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    effects = data["effects"]

    count_true = 0
    count_false = 0
    count_conditional = 0

    for effect_id, entry in effects.items():
        key = entry["key"]
        stackable, notes = get_stacking_info(effect_id, key)
        entry["stackable"] = stackable
        entry["stackNotes"] = notes

        if stackable is True:
            count_true += 1
        elif stackable is False:
            count_false += 1
        elif stackable == "conditional":
            count_conditional += 1

    with open(EFFECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = len(effects)
    print(f"Stacking info added to {total} effects.")
    print(f"  Stackable (true):       {count_true}")
    print(f"  Not stackable (false):  {count_false}")
    print(f"  Conditional:            {count_conditional}")
    print()

    # Print some sample entries for verification
    sample_ids = [
        "10000", "310000", "6610400", "312501", "340000",
        "7001400", "11000", "6621000", "7120900", "330600",
        "7122700", "321600", "7040201", "350200", "7260710",
    ]
    print("=== Sample entries ===")
    for sid in sample_ids:
        if sid in effects:
            e = effects[sid]
            print(f"  ID {sid}: key={e['key']}, stackable={e['stackable']}, stackNotes={e['stackNotes']!r}")
        else:
            print(f"  ID {sid}: NOT FOUND")


if __name__ == "__main__":
    main()
