# -*- coding: utf-8 -*-
# Archetype content (第2版). Executed inside gen.py (has add(), key families, wt_keys...).
# 出典は神攻略wiki（kamikouryaku.net/nightreign_eldenring）と公式パッチノートのみ。
import urllib.parse as _u

KW = "https://kamikouryaku.net/nightreign_eldenring/"
def W(page, date, label=None):
    return f"- 神攻略wiki {label or page} {KW}?{_u.quote(page)} （最終更新 {date}）"
def B(title, date):
    return f"- 神攻略wiki ビルド投稿「{title}」 {KW}?{_u.quote('ビルド投稿/' + title)} （最終更新 {date}）"

S_GLOSS = W("用語集", "2026-10-26")
S_EFF = W("遺物効果", "2026-10-21")
S_RELIC = W("遺物", "2026-06-25")
S_STATUS = W("状態変化", "2026-05-06")
S_BUILDS = W("ビルド投稿", "2026-09-30", "ビルド投稿一覧")
S_SORC = W("魔術", "2026-08-04")
S_INC = W("祈祷", "2026-01-19")
S_RESCUE = W("救助", "2026-09-13")
S_GAREKI = W("遺物/瓦礫の夜", "2026-02-09")
S_HAL = W("遺物/安寧の遺志", "2026-10-24")
C = {  # キャラページ
    "追跡者": W("追跡者", "2026-10-18"), "守護者": W("守護者", "2026-10-22"), "鉄の目": W("鉄の目", "2026-10-25"),
    "レディ": W("レディ", "2026-10-20"), "無頼漢": W("無頼漢", "2026-10-08"), "復讐者": W("復讐者", "2026-06-28"),
    "隠者": W("隠者", "2026-10-23"), "執行者": W("執行者", "2026-09-13"), "学者": W("学者", "2026-10-16"),
    "葬儀屋": W("葬儀屋", "2026-10-27"),
}
S_OFF1032 = "- 公式 アップデート情報 App Ver.1.03.2 / Regulation Ver.1.03.4 https://nightreign.eldenring.jp/article/260115_1.html （2026-01-15、日付・バージョン確認用）"
S_OFF103 = "- 公式 アップデート情報 App Ver.1.03 / Regulation Ver.1.03.1 https://nightreign.eldenring.jp/article/251203_1.html （2025-12-03、日付・バージョン確認用）"
def S(*xs):
    return "\n".join(xs)

DEEP_SCHOOL = "深層の遺物にも「○○の魔術/祈祷を強化」が付く（遺物効果ページ FAQ: 深層枠でも系統強化＋対応属性攻撃力の組み合わせが可能）。"

# ============================================================ 攻撃パターン系
add(cat="攻撃パターン系", name="バッタ", conf="高",
    aliases="バッタ戦法、二刀バッタ、ジャンプ二刀、両手持ちバッタ、クイステ二刀バッタ（守護者）、（※「バッター無頼漢」は1段目連打の比喩なので別物）",
    desc="""
ジャンプ攻撃を繰り返す戦法。両手に同じ武器種を持ち **ジャンプ二刀攻撃** を繰り返すものを「二刀バッタ」と呼び、単に「バッタ」と言う場合はこれを指すことが多い（用語集）。
- ダメージと体勢崩しの両立が高水準。ジャンプで偶発的に敵の攻撃を避けられることもある（用語集）。
- 二刀バッタの体勢崩しが優秀なのは大剣・特大武器などの重量系。斧槍・刀などの軽量系は **両手持ちバッタ**（両手持ちジャンプ強攻撃）の方が強靭削りが高い（用語集）。
- 二刀のジャンプ二刀攻撃・ダッシュ二刀攻撃は武器種によって最大4ヒットの連撃になり、フルヒットで「攻撃連続時」系の効果が発動する（守護者ページ）。
""",
    chars="追跡者（大剣）、無頼漢（特大武器）、葬儀屋（斧槍二刀バッタ投稿）、守護者（斧槍のクイステ二刀バッタ。斧槍のジャンプ二刀攻撃はアーツゲージ蓄積が高く救助性能も高い）、執行者（両刃剣二刀バッタ）。",
    core=["improvedStanceBreakingWhenWieldingTwoArmaments", "improvedStanceBreakingWhenTwoHanding"] + STAMREC + END,
    good=["successiveAttacksBoostAttackPower"] + CRIT + PHYS
         + wt_many(["大剣", "特大武器", "斧槍", "特大剣", "大槌", "両刃剣"], ("3plus", "find")),
    opt=["fpRestorationUponSuccessiveAttacks", "changesCompatibleArmamentsSkillToQuickstepAtStartOfExpedition"] + POISE + REGAIN + UNIV + STR
        + wt_many(["大剣", "特大武器", "斧槍", "特大剣", "大槌", "両刃剣"], ("atk",)),
    avoid=[],
    nonrelic=["improvedJumpAttacks", "successiveAttacksNegateDamage", "attackUpWhenWieldingTwoArmaments", "improvedStaminaRecovery", "improvedStaminaRecoveryPlus1", "reducedStaminaConsumption", "strongJumpAttacksCreateShockwave"],
    missing_note="""
- 「ジャンプ攻撃強化」「攻撃連続時、カット率上昇」は **付帯効果のみ**（遺物に無し）。
- 「スタミナ回復速度上昇」も付帯効果側。遺物では「攻撃命中時、スタミナ回復」で代替（執行者ページ: 両刃剣二刀バッタを連発するなら必須、4ヒットするので回復量が多い）。
""",
    notes="""
- 「攻撃連続時、攻撃力上昇」は二刀ジャンプ攻撃の多段ヒットで発動する（守護者ページの記述＋オーナー確認）。1.03.2 で効果量は下方修正されたが、多段ヒットで発動する仕組みは変わっていない → 相性良。
- 二刀は「同じ武器種」が条件（一部例外あり。用語集「二刀流」）。武器種3本・発見系遺物は2本目確保の補助として間接的に効く（葬儀屋の斧槍バッタ投稿は「斧槍を見つけやすくなる（必須）」）。
- 「二刀持ちの、体勢を崩す力上昇」は射撃・魔術・祈祷には無効。「両手持ちの〜」は両手持ちで二刀になる武器（爪・拳）には無効（遺物効果ページ）。
- スタミナを使い切る戦法だが、スタミナ系のデメリットは現行の深層の遺物に無いため「避けたい」は空。
""",
    sources=S(S_GLOSS, S_EFF, C["守護者"], C["執行者"], B("技量ステ変斧槍二刀バッタ葬儀屋", "2026-07-30"), S_OFF1032))

add(cat="攻撃パターン系", name="通常攻撃1段目", conf="高",
    aliases="1段目、一段目、1段目特化、1段目強化型、初段、R1型、弱攻撃1段目、1段目二刀、タニムラッシュ（左右交互に1段目を出す技術）、ガーキャン（ガードキャンセルで1段目に戻す）、「バッター」（1段目を振り続ける比喩）",
    desc="""
遺物「通常攻撃の1段目強化」（15%・重ね掛け可）を複数積み、**通常攻撃の初段だけを繰り返す**型。
- 対象: 通常攻撃・**二刀攻撃の1段目**・**弓の通常攻撃**。強攻撃/タメ攻撃/ガード攻撃/大弓/クロスボウ/バリスタは対象外（遺物効果ページ）。
- 左右交互に攻撃すると常に「通常攻撃の1段目」となり DPS が上がる（タニムラッシュ）。二刀流でも「右手通常攻撃→二刀攻撃→…」で連続発動できる（用語集）。
- 投稿例では「1段目強化」を最大6枠ぶん積む。
""",
    chars="守護者（大槍二刀・クイステ）、無頼漢、執行者（妖刀一段目）、追跡者（直剣二刀）、レディ（直剣一段目＋回避）、隠者（近接隠者）。武器ガチャに左右されにくいのが利点。",
    core=["improvedInitialStandardAttack"],
    good=STAMREC + PHYS + REGAIN + UNIV + VIG,
    opt=["takingAttacksImprovesAttackPower", "slowlyRestoreHpForSelfAndNearbyAlliesWhenHpIsLow", "upliftingAromaticInPossessionAtStartOfExpedition", "changesCompatibleArmamentsSkillToQuickstepAtStartOfExpedition", "improvedMeleeAttackPower"] + STR
        + wt_many(["大槍", "直剣", "刀"], ("atk", "find")),
    avoid=ATK_DEMERIT,
    nonrelic=["improvedStaminaRecovery", "reducedStaminaConsumption"],
    notes="""
- 一撃重視なので、付帯効果「まれに攻撃がかすめる」系は避けたい（無頼漢1段目投稿）。
- 「HP最大未満時、攻撃力低下」を許容する投稿（大槍1段目二刀）もあり、避けたいは目安。
""",
    sources=S(S_GLOSS, S_EFF,
              B("ステ変大槍1段目二刀", "2026-09-08"), B("クイステタニムラッシュ守護者", "2026-09-08"),
              B("バッター無頼漢(ただの１段目)", "2026-07-21"), B("妖刀一段目", "2026-07-19"),
              B("1段目直剣2刀", "2026-07-14"), B("【超回避】直剣レディ", "2026-07-18"), B("近接隠者", "2026-10-06")))

add(cat="攻撃パターン系", name="連撃", conf="中",
    aliases="連撃型、連続攻撃、攻撃連続時、連続時バフ、手数型、ガラス（＝ガラスの首飾り）、ハルハルガラス",
    desc="""
手数の多い武器で攻撃を途切れさせず当て続け、「攻撃連続時、○○」系を常時発動させる型。
- 「攻撃連続時、攻撃力上昇」: 最大3段階（5%→累計約12%→累計約22%）、効果約4秒。必要回数は武器種で異なる。内部的な「連撃ゲージ」で管理されると推測（遺物効果ページ）。
- 「攻撃連続時、FP回復」: 射撃・魔術・祈祷・飛び道具は対象外。ゲージの繰り越しは無い（遺物効果ページの検証）。
- 固有遺物「ガラスの首飾り」（葬儀屋）＝【葬儀屋】アーツ発動時、攻撃力上昇／攻撃連続時、攻撃力上昇／アーツゲージ自然蓄積+3。ハルハルと組む「ハルハルガラス」構成もある（用語集）。
""",
    chars="葬儀屋（ガラスの首飾り、【葬儀屋】連撃の最終攻撃命中時、攻撃力上昇。両刃剣・拳）、レディ（短剣再演）、追跡者（スキル+1でクローショット2回でも発動）、守護者（二刀のジャンプ/ダッシュ二刀攻撃）。",
    core=["successiveAttacksBoostAttackPower", "fpRestorationUponSuccessiveAttacks"],
    good=["undertakerAttackPowerIncreasedByLandingTheFinalBlowOfAChainAttack", "duchessDaggerChainAttackReprises"] + STAMREC + PHYS
         + wt_many(["両刃剣", "拳", "短剣", "曲剣", "刺剣"], ("atk", "3plus")),
    opt=wt_many(["両刃剣", "拳", "短剣", "曲剣", "刺剣"], ("hp", "fp", "find")) + REGAIN + UNIV + END,
    avoid=[],
    nonrelic=["successiveAttacksNegateDamage", "hpRestorationUponSuccessiveAttacks", "attackUpWhenWieldingTwoArmaments"],
    missing_note="- 「攻撃連続時、カット率上昇」「攻撃連続時、HP回復」は付帯効果のみ（遺物に無し）。",
    notes="""
- **1.03.2（2026-01-15）で「攻撃連続時、攻撃力上昇」は効果量が下方修正**（公式）。
- 「連撃」は葬儀屋の固有効果名にも出る語。用語集に「連撃」の独立見出しは無く、型名としては投稿名（「技ステ変連撃両刃剣葬儀屋」）での使用。
""",
    sources=S(S_EFF, S_GLOSS, C["葬儀屋"], C["追跡者"], B("技ステ変連撃両刃剣葬儀屋(拳もあるよ)", "2026-10-02"),
              B("固有効果乗せ乗せ葬儀屋", "2026-10-01"), B("ナメレス短剣再演レディ", "2026-07-05"), S_OFF1032))

add(cat="攻撃パターン系", name="致命・体勢崩し", conf="高",
    aliases="致命型、致命ビルド、致命特化、体勢崩し、崩し、ダウン取り、背後致命（バクスタ）、パリィ致命、落馬致命",
    desc="""
強靭削りで敵の体勢値を削り切り、**体勢崩し→致命の一撃** を何度も入れてダメージを稼ぐ型。今作では致命の一撃で拘束されている敵に他プレイヤーの攻撃もダメージが入るため、連携で袋叩きにできる（用語集）。
- 致命の発生条件: 体勢崩し・パリィ・ガード崩し・落馬・背後。ダメージは「落馬 ＞ 体勢崩し ＝ パリィ ＝ ガード崩し ＞ 背後」（用語集）。
- 致命の一撃の攻撃モーション中は無敵。
""",
    chars="追跡者（松明×致命の投稿例）、無頼漢（特大武器）、レディ（背後致命後に姿を隠す）。",
    core=CRIT + ["improvedStanceBreakingWhenWieldingTwoArmaments", "improvedStanceBreakingWhenTwoHanding"],
    good=CRITSIDE + ["duchessBecomeStealthyAfterCritFromBehind", "improvedGuardCounters", "improvedGuardCountersPlus1", "improvedGuardCountersPlus2"],
    opt=PHYS + UNIV,
    avoid=[],
    nonrelic=["improvedStanceBreaking", "improvedCriticalHits", "improvedJumpAttacks", "improvedChargeAttacks"],
    notes="""
- 「致命の一撃強化」は17%（+1は24%）。遺物にも付帯効果にもある（遺物効果ページ）。
- 「致命の一撃で、アーツゲージ増加」は致命モーションに入った瞬間に固定5%加算（遺物効果ページ）。
- 坩堝の騎士は致命の被ダメージを0.7倍に軽減。血の貴族・失地騎士はパリィ待機姿勢を取る（用語集）。
""",
    sources=S(S_GLOSS, S_EFF, B("より遠くを照らす致命追跡者", "2026-07-21")))

# ============================================================ 武器系
add(cat="武器系", name="二刀流", conf="高",
    aliases="二刀、二刀持ち、2刀",
    desc="""
左右に**同じ武器種**を持ち、ガードボタンが二刀攻撃に変わる状態。爪・拳は両手持ちで二刀扱い。一部例外的に異なる武器種で二刀になる組み合わせもある（用語集）。
- 長所: 瞬間火力。短所: スタミナ消費大、武器ガード不可、**状態異常の蓄積量が減衰**（用語集）。
- バッタ・1段目二刀・連撃と組み合わせて使われる「基盤」概念。遺物・付帯効果の「二刀持ちの○○」は二刀攻撃を強化する効果（用語集）。
""",
    chars="追跡者・無頼漢など得意武器の二刀攻撃が強いキャラで多い（用語集）。投稿例: 守護者（大槍二刀・爪拳）、葬儀屋（両刃剣・斧槍）、学者（刺剣・猛禽爪）、追跡者（直剣）。",
    core=["improvedStanceBreakingWhenWieldingTwoArmaments"] + END + STAMREC,
    good=["improvedInitialStandardAttack", "successiveAttacksBoostAttackPower"] + PHYS
         + wt_many(["大剣", "特大武器", "刀", "曲剣", "大槍", "斧槍", "爪", "拳"], ("3plus", "find")),
    opt=wt_many(["大剣", "特大武器", "刀", "曲剣", "大槍", "斧槍", "爪", "拳"], ("atk",)) + UNIV,
    avoid=[],
    nonrelic=["attackUpWhenWieldingTwoArmaments", "improvedStanceBreakingWhenWieldingTwoArmaments", "reducedStaminaConsumption"],
    missing_note="- 「二刀持ち攻撃力上昇」は付帯効果のみ（遺物に無し）。",
    notes="- 「○○を3つ以上装備していると攻撃力上昇」は3本必要（2本の二刀だけでは不足）。「潜在する力から、○○を見つけやすくなる」は複数付けると（深層も含め）左に付けたものが優先され、その武器種のみ見つけやすくなる。出現確率は拠点や強敵で大きく変わる（遺物効果ページ）。",
    sources=S(S_GLOSS, S_EFF, B("ステ変大槍1段目二刀", "2026-09-08"), B("爪拳守護者", "2026-09-05"), B("ステ変刺剣学者", "2026-09-15")))

add(cat="武器系", name="大型武器・タメ", conf="中",
    aliases="特大、特大武器、大型武器、タメ、溜め、タメ攻撃、R2タメ、脳筋、タメ斧槍、タメつむじ（守護者）、タメガーカン",
    desc="""
特大武器・大槌・大斧・特大剣などで **強攻撃のタメ攻撃** を主軸にする型。強靭削りが高く体勢崩しに直結。
- 用語集の区別: R2長押し＝「タメ攻撃」、魔術/祈祷/戦技の長押し＝「タメ使用」、スキル/アーツ＝「タメ発動」。付帯効果「タメ攻撃強化」は R2 のタメ攻撃のみ強化。
- 守護者は斧槍装備時のみガードカウンターもタメられる（タメガーカン）。
""",
    chars="無頼漢（特大武器・大斧・大槌）、追跡者（大剣）、守護者（斧槍タメ＝つむじ風）、学者（猛禽爪のタメ攻撃投稿）。",
    core=["improvedStanceBreakingWhenTwoHanding"] + PHYS,
    good=POISE + ["takingAttacksImprovesAttackPower", "guardianCreatesWhirlwindWhenChargingHalberd"] + CRIT + STR
         + wt_many(["特大武器", "大槌", "大斧", "特大剣", "大剣", "斧槍"], ("atk", "3plus", "find")),
    opt=END + REGAIN + UNIV + ["raiderCharacterSkillDamageUp", "raiderDamageTakenWhileUsingCharacterSkillImprovesAttack"],
    avoid=EVADE_DEMERIT,
    nonrelic=["improvedChargeAttacks", "dmgNegationUpWhileChargingAttacks", "improvedAttackPowerWhenTwoHanding", "improvedStanceBreakingWhenTwoHanding"],
    missing_note="- 「タメ攻撃強化」「タメ攻撃中、カット率上昇」は**遺物には無く付帯効果のみ**。",
    notes="""
- 1.03.2 で無頼漢の大斧・大槌・特大武器の各種攻撃（二刀攻撃・ジャンプ攻撃を除く）が高速化（公式）。
- 回避が苦手な重量級なので「回避直後の被ダメージ増加」等は避けたい側に置いた（深層デメリットの評価は遺物効果ページ参照。無頼漢は回避の無敵時間が短めと記載）。
""",
    sources=S(S_GLOSS, S_EFF, C["無頼漢"], B("フルゴ、マリスギミック対応汎用特大無頼漢", "2026-07-20"), B("技量ステ変猛禽爪しろがね人", "2026-09-13"), S_OFF1032))

add(cat="武器系", name="刀・出血", conf="中",
    aliases="刀、出血刀、血刀、執行者刀、妖刀（執行者スキル）",
    desc="刀（出血付き武器が多い）で手数と出血を両立する型。執行者の得意武器で、初期武器も出血付き。執行者の刀に別の状態異常を付加すると出血と複合し、出血を付加すると出血蓄積量が上がる（遺物効果ページ）。出血そのものの詳細は「出血」項を参照。",
    chars="執行者（主）、追跡者・レディ（刀を拾った場合）。",
    core=wt_keys("刀", ("atk", "3plus", "find")) + ["startingArmamentInflictsBloodLoss"],
    good=["successiveAttacksBoostAttackPower"] + ARC + PHYS
         + ["executorSkillBoostsAttackReducesCutRate", "executorUnlockingCursedSwordRestoresHP", "executorRoaringRestoresHPWhileArtActive", "executorSlowlyRestoreHPUponAbilityActivation"],
    opt=wt_keys("刀", ("hp", "fp")) + ["improvedInitialStandardAttack", "improvedRoarAndBreathAttacks"] + UNIV,
    avoid=["takingDamageCausesBloodLossBuildup"],
    notes="""
- 出血は恐るべき強敵・砦屋上のボス・襲撃イベントのボス・夜ボス・夜の王で割合ダメージ半減、さらにデュオ3/4・トリオ1/2（状態変化）。
- 「咆哮とブレス強化」は執行者のアーツ（獣化）の咆哮にも乗る（App 1.02 から。遺物効果ページ・執行者ページ）。価値は低いので任意。
- 1.03.2 で【執行者】スキル中の攻撃力上昇遺物は攻撃時のデメリットが「HP減少」から「カット率が下がる」ものに変更、妖刀中の戦技にも近接/戦技攻撃力上昇が乗るよう変更（公式）。
- 型名としては「刀」単体より「出血」「執行者」「妖刀」で語られることが多い。
""",
    sources=S(S_STATUS, S_EFF, C["執行者"], B("妖刀一段目", "2026-07-19"), B("お手軽４色刀", "2026-10-19"), S_OFF1032))

add(cat="武器系", name="弓・遠距離", conf="中",
    aliases="弓、弓型、遠距離、射撃、大弓、三弓流、弓チク、アロレ（アローレイン）、クロスボウ",
    desc="""
弓・大弓・クロスボウで中〜遠距離から攻撃する型。鉄の目の得意武器。
- 弓の通常攻撃は「通常攻撃の1段目強化」の対象（大弓・クロスボウは対象外）。
- 遠距離攻撃は救助で有用（弓・クロスボウが望ましい、救助ページ）。ただし 1.03.2 で射撃の距離減衰が状態異常蓄積・アーツゲージ増加・瀕死ゲージ削りにも適用（公式）。
""",
    chars="鉄の目（主。大弓アロレ＋弓）。守護者（大弓アロレ）、追跡者（クロスボウ）、学者（クロスボウサポート）。",
    core=["improvedBowAttackPower", "improvedAttackPowerWith3PlusBowsEquipped", "improvedGreatbowAttackPower", "improvedCrossbowAttackPower"] + PHYS,
    good=["improvedInitialStandardAttack", "changesCompatibleArmamentsSkillToRainOfArrowsAtStartOfExpedition",
          "ironeyeAdditionalCharacterSkillUse", "ironeyeExtendsDurationOfWeakPoint", "ironeyeBoostsThrustingCounterattacksAfterArt"] + DEX,
    opt=["hpRestorationUponBowAttacks", "fpRestorationUponBowAttacks", "hpRestorationUponGreatbowAttacks", "dormantPowerHelpsDiscoverBows", "dormantPowerHelpsDiscoverGreatbows", "dormantPowerHelpsDiscoverCrossbows", "improvedBallistaAttackPower"] + UNIV + ARTKILL,
    avoid=[],
    nonrelic=["lightningUponPrecisionAiming", "poisonMistUponPrecisionAiming"],
    missing_note="- 三弓流投稿が挙げる付帯効果「射撃強化」「減衰軽減」はファイル上で該当名を確認できず（付帯効果の別名称か未収録）。",
    notes="""
- **1.03.2 で「弓の攻撃力上昇」「弓の武器種を3つ以上装備していると攻撃力上昇」は効果量が下方修正**（1.03 で弓にも誤って適用されていた上方修正への対応、公式）。
- 「【鉄の目】神秘上昇、技量低下」は技量弓型には不向きだが、毒型では有用なので型ごとに判断（避けたいには入れていない）。
""",
    sources=S(S_GLOSS, S_EFF, S_RESCUE, C["鉄の目"], B("右手に大弓、左手に弓、背中に剛弓", "2026-10-01"),
              B("炎撃とアロレ大弓の片ハルブローチビルド", "2026-09-08"), B("クロスボウ追跡者", "2026-07-13"), S_OFF1032))

add(cat="武器系", name="盾・ガードカウンター", conf="高",
    aliases="ガーカン、ガードカウンター、タメガーカン、ガーカンHP、盾、大盾、ガード型、反射（ガード反射）、ハイガ（ハイガード）、ガードアーツ",
    desc="""
盾（主に大盾）でガードし、**ガード成功直後の強攻撃＝ガードカウンター** で強靭を削る型（用語集「ガーカン」）。守護者はハイガード（アビリティ）中のガード成功で衝撃波（通称「反射」）を出せる。
- ガードで受けた回数をアーツ回転・HP回復に変える構成が多い（耐久型守護者投稿）。
""",
    chars="守護者（主）。無頼漢（大盾☆無頼漢の投稿例）。",
    core=["improvedGuardCounters", "improvedGuardCountersPlus1", "improvedGuardCountersPlus2", "guardCounterIsGivenABoostBasedOnCurrentHP", "guardianSuccessfulGuardsSendOutShockwaves",
          "artGaugeChargedFromSuccessfulGuarding", "artGaugeChargedFromSuccessfulGuardingPlus1"],
    good=["hpRecoveryFromSuccessfulGuarding", "drawEnemyAttentionWhileGuarding", "maxHpUpWith3PlusGreatshieldsEquipped", "maxHpUpWith3PlusMediumShieldsEquipped", "maxHpUpWith3PlusSmallShieldsEquipped",
          "guardianIncreasedDurationForCharacterSkill"] + VIG + REGAIN,
    opt=["shieldGreaseInPossessionAtStartOfExpedition", "dormantPowerHelpsDiscoverGreatshields", "guardianCreatesWhirlwindWhenChargingHalberd"] + CUTA + PHYS,
    avoid=[],
    nonrelic=["improvedGuardCounters", "improvedGuardingAbility", "successfulGuardingUpsDmgNegation", "successfulGuardingUpsPoise", "hpRecoveryFromSuccessfulGuardingPlus", "fpRecoveryFromSuccessfulGuarding", "guardCountersActivateHolyAttacks"],
    notes="""
- 1.03.2 で「ガード成功時、HP回復」「ガード中、敵に狙われやすくなる」「【守護者】アビリティ発動中、ガード成功時、衝撃波が発生」が **上方修正**、守護者本体もカット率・ガード強度が上方修正（公式）。
- 「ガードカウンターに、自身の現在HPの一部を加える」= 最大HPの5%をガードカウンターに加算、複数ヒットなら毎ヒット（遺物効果ページ）。
- 「ガード成功時、アーツゲージ増加」は約1%/回、執行者の弾きでも発動、ガード崩しでは不発（遺物効果ページ）。
- 属性攻撃をガードすると貫通ダメージを受ける（→ ドレイン型が生まれた理由、用語集）。
""",
    sources=S(S_GLOSS, S_EFF, C["守護者"], B("耐久型守護者", "2026-09-07"), B("マサカリバード", "2026-08-03"), B("大盾☆無頼漢", "2026-08-21"), S_OFF1032))

add(cat="武器系", name="盾チク・刺突カウンター（ドレイン）", conf="中",
    aliases="盾チク、ドレイン、刺突カウンター、刺突回復、盾＋槍",
    desc="""
盾でガードを維持したまま刺剣・重刺剣・槍・大槍・（今作から）斧槍で攻撃する立ち回り（盾チク、用語集）。
「刺突カウンター発生時、HP回復」を積んで盾チクによる刺突カウンターで回復し続ける戦術を **ドレイン** と呼ぶ。属性ガードの貫通ダメージで盾が使いづらい深き夜への対策として守護者で編み出された。リゲイン・ガード成功時HP回復・○○の攻撃でHP回復との併用も挙げられている（用語集「ドレイン」）。
""",
    chars="守護者（主）、鉄の目（アーツ後の刺突カウンター強化）。刺突属性の武器なら他キャラも可（追跡者のクロスボウ、葬儀屋の錨＝大斧唯一の刺突属性）。",
    core=["hpRestorationUponThrustingCounterattack", "hpRestorationUponThrustingCounterattackPlus1"],
    good=["ironeyeBoostsThrustingCounterattacksAfterArt", "hpRecoveryFromSuccessfulGuarding"] + REGAIN + wt_many(["槍", "大槍", "刺剣", "重刺剣", "斧槍"], ("atk", "3plus", "hp")),
    opt=["successiveAttacksBoostAttackPower", "maxHpUpWith3PlusGreatshieldsEquipped"] + STAMREC,
    avoid=[],
    nonrelic=["improvedThrustingCounterattack"],
    missing_note="- 「刺突カウンター強化」は遺物に無い（付帯効果/潜在する力/タリスマン「槍のタリスマン」側、用語集）。遺物では鉄の目専用の「アーツ発動後、刺突カウンター強化」のみ。",
    notes="- 刺突カウンターは有効時間が極めて短く相打ちの懸念もあるが、盾チクならガードしつつ狙える（用語集）。盾チクは攻撃でスタミナを使いすぎるとガード崩しを起こす。",
    sources=S(S_GLOSS, S_EFF, C["守護者"], B("錨を担げ！（葬儀屋大斧ビルド）", "2026-07-21"), B("クロスボウ追跡者", "2026-07-13")))

add(cat="武器系", name="戦技", conf="高",
    aliases="戦技型、戦技ビルド、戦技特化、ハルハル（安寧の遺志＋安寧者の遺志）、赤ハル/青ハル/片ハル、ハルハルガラス、戦技ぶっぱ、属性戦技",
    desc="""
FPを使う武器の戦技を主力にする型。ハルモニア産の固有遺物「安寧の遺志」「安寧者の遺志」（どちらも近接攻撃力上昇＋戦技攻撃力上昇）を併用する「ハルハル」が定番。片方だけの採用は「片ハル」（用語集）。
- 「近接攻撃力上昇」は近接武器と盾の戦技・執行者のスキルにも乗る。「戦技攻撃力上昇」（15%）は執行者スキルの戦技にも乗る（遺物効果ページ）。
- 併用で近接攻撃力約12%・戦技攻撃力約32%、近接攻撃力も乗る戦技は約48%上昇（安寧の遺志ページ）。
- 深き夜でハルハル＋深層の遺物で戦技特化した「ハルハルサイス」（光輪のサイス）が確立されている（用語集）。
""",
    chars="レディ（属性戦技・上質ハルハル）、追跡者、執行者、学者（属性ハルハル壺サイス）、守護者（ハルハルWステ変）、無頼漢（大盾戦技）、鉄の目（ハルハル物理の目）。",
    core=["improvedSkillAttackPower", "improvedMeleeAttackPower"] + FPSUST,
    good=MIND + PHYS + ["occasionallyNullifyAttacksWhenDamageNegationsIsLowered", "fpRestorationUponSuccessiveAttacks"],
    opt=["changesCompatibleArmamentsSkillToGlintbladePhalanxAtStartOfExpedition", "changesCompatibleArmamentsSkillToFlamingStrikeAtStartOfExpedition", "changesCompatibleArmamentsSkillToDeterminationAtStartOfExpedition",
         "changesCompatibleArmamentsSkillToLightningSlashAtStartOfExpedition", "changesCompatibleArmamentsSkillToSacredBladeAtStartOfExpedition", "changesCompatibleArmamentsSkillToGravitasAtStartOfExpedition"] + AFF + UNIV,
    avoid=[],
    nonrelic=["improvedSkillAttackPower", "reducedSkillFpCost", "improvedChargedSkillAttackPower", "skillActivationImprovesPoise"],
    notes="""
- 1.03.2: 「安寧者の遺志」を複数入手できる不具合を修正。2つ以上同時装備しても1つ分のみ発動。「安寧者の遺志」と「安寧の遺志」の併用は従来どおり有効（公式）。
- 安寧の遺志の「カット率低下時、稀に敵から受ける攻撃を無効化」（20%）は、深層デメリット等でカット率が下がっている状態（常時型を含む）や地形効果でも条件を満たす（安寧の遺志ページ）。→ カット率が下がるデメリットはこの型では必ずしも「避けたい」ではないため、避けたいは空。
- 「出撃時の武器の戦技を○○にする」遺物（下の「特定戦技固定」）と組むことが多い。
""",
    sources=S(S_GLOSS, S_EFF, S_HAL, B("上質ハルハル物理レディ", "2026-07-28"), B("属性戦技レディ", "2026-09-13"),
              B("ステ変属性ハルハル壺（サイス）学者", "2026-07-03"), B("ハルハルWステ変バード", "2026-07-14"), S_OFF1032))

add(cat="武器系", name="特定戦技固定", conf="中",
    aliases="霜踏み○○、血の刃レディ、炎撃、冷気の霧、クイステ、初期戦技持ち込み、初期戦技指定",
    desc="「出撃時の武器の戦技を○○にする」遺物で初期武器に強戦技を付け、序盤から武器ガチャに頼らず戦う型。代表は **霜踏み**（範囲・凍傷の割合ダメージで汎用性が高く人気、用語集）、**冷気の霧**、**血の刃**、**炎撃**、**クイックステップ**。",
    chars="全キャラ可だが互換のある初期武器が必要（対応表は遺物効果ページ）。投稿例: 学者（霜踏み）、レディ（血の刃・霜踏み）、復讐者（霜踏み・炎撃）、守護者（クイステ・炎撃）、追跡者（冷気の霧）。",
    core=["changesCompatibleArmamentsSkillToHoarfrostStompAtStartOfExpedition", "changesCompatibleArmamentsSkillToChillingMistAtStartOfExpedition", "changesCompatibleArmamentsSkillToBloodBladeAtStartOfExpedition",
          "changesCompatibleArmamentsSkillToGlintbladePhalanxAtStartOfExpedition", "changesCompatibleArmamentsSkillToFlamingStrikeAtStartOfExpedition", "changesCompatibleArmamentsSkillToSeppukuAtStartOfExpedition",
          "changesCompatibleArmamentsSkillToQuickstepAtStartOfExpedition", "changesCompatibleArmamentsSkillToDeterminationAtStartOfExpedition", "changesCompatibleArmamentsSkillToRainOfArrowsAtStartOfExpedition"],
    good=["improvedSkillAttackPower", "improvedMeleeAttackPower"] + FPSUST,
    opt=MIND + ["attackPowerUpWhenFacingFrostbiteAfflictedEnemy", "attackPowerUpWhenFacingFrostbiteAfflictedEnemyPlus1", "attackPowerUpWhenFacingFrostbiteAfflictedEnemyPlus2"],
    avoid=[],
    notes="- 出撃時の武器の戦技/魔術/祈祷の変更、属性・状態異常の付加は、それぞれ複数セットしても**献器の最も左の遺物の効果のみ発動**（遺物効果ページ）。戦技変更と属性/状態異常付加は別枠なので併用できる。復讐者は初期祈祷変更と初期戦技変更を同時に付けると一番左のみ有効。",
    sources=S(S_GLOSS, S_EFF, C["復讐者"], B("サポ壺アーツぶん回し", "2026-10-03"), B("属性戦技レディ", "2026-09-13"), B("祈祷・属性型【追跡者】", "2026-10-25")))

add(cat="武器系", name="投擲・壺", conf="中",
    aliases="壺、壺おじ、壺学者、投擲壺、ナイフ（投擲ナイフ・投げ矢）、サポ壺",
    desc="投擲壺（火炎壺など）や投擲ナイフを主力・補助火力にする型。学者の代名詞（用語集「壺おじ」）。1.03.2 で火炎壺・スローイングダガーの購入数に上限が付いた（公式）。",
    chars="学者（主）。他キャラも補助として可。",
    core=["improvedThrowingPotDamage", "improvedThrowingPotDamagePlus1", "smallPouchInPossessionAtStartOfExpedition", "firePotsInPossessionAtStartOfExpedition"],
    good=FIRE + ["magicPotsInPossessionAtStartOfExpedition", "lightningPotsInPossessionAtStartOfExpedition", "holyWaterPotsInPossessionAtStartOfExpedition",
                 "improvedThrowingKnifeDamage", "improvedThrowingKnifeDamagePlus1", "throwingDaggersInPossessionAtStartOfExpedition", "poisonboneDartsInPossessionAtStartOfExpedition", "crystalDartsInPossessionAtStartOfExpedition"],
    opt=["improvedGlintstoneAndGravityStoneDamage", "improvedGlintstoneAndGravityStoneDamagePlus1", "glintstoneScrapsInPossessionAtStartOfExpedition", "gravityStoneChunksInPossessionAtStartOfExpedition",
         "itemsConferEffectToAllNearbyAllies", "improvedPerfumingArts", "improvedPerfumingArtsPlus1", "sparkAromaticInPossessionAtStartOfExpedition"] + ARTKILL,
    avoid=[],
    notes="""
- 「投擲壺の攻撃力上昇」（15%）の対象は毒壺・腐敗壺・眠り壺・誘い壺・獣誘いの壺**以外**の投擲壺。「投擲ナイフの攻撃力上昇」（14%）は骨の毒投げ矢・結晶投げ矢・スローイングダガー・ククリ・扇投暗器。「調香術強化」（14%）は火花の香りのみ（遺物効果ページ）。
- 物理攻撃力上昇等は「魔術・祈祷・アイテムにも効果あり」（遺物効果ページ）。
""",
    sources=S(S_GLOSS, S_EFF, C["学者"], B("サポ壺アーツぶん回し", "2026-10-03"), B("ステ変属性ハルハル壺（サイス）学者", "2026-07-03"), S_OFF1032))

# ============================================================ 魔術・祈祷系
add(cat="魔術・祈祷系", name="魔術特化", conf="高",
    aliases="魔術、魔術型、魔術ビルド、スペラー（魔術/祈祷を主攻撃にする役割）、術師、知力型、マジカル無頼漢（無頼漢で魔術）、魔術学者、輝剣隠者/カーリア隠者/結晶隠者（系統名＋キャラ）",
    desc="杖の魔術を主攻撃にする型。系統強化遺物「○○の魔術を強化」（12%・重ね掛け可）が系統ごとにあり、投稿も系統名で呼ぶのが実態（下の各系統項）。系統は魔術ページの「分類」列で確認できる。用語集「スペラー」は魔術/祈祷を主攻撃にするレディ・復讐者・隠者を指すロール語。",
    chars="隠者・レディ（主）。学者（魔術学者・魔力学者）、無頼漢（マジカル無頼漢）、追跡者（知信ステ変）。",
    core=SORC + MAG + INT + FPSUST,
    good=MIND + ["maxFpUpWith3PlusStavesEquipped", "maxFpPermanentlyIncreasedAfterReleasingSorcerersRiseMechanism", "extendedSpellDuration", "changesCompatibleArmamentsSorceryToMagicGlintbladeAtStartOfExpedition", "changesCompatibleArmamentsSorceryToCarianGreatswordAtStartOfExpedition",
                 "changesCompatibleArmamentsSorceryToNightShardAtStartOfExpedition", "changesCompatibleArmamentsSorceryToMagmaShotAtStartOfExpedition", "changesCompatibleArmamentsSorceryToBriarsOfPunishmentAtStartOfExpedition",
                 "recluseCollectingAffinityResidueActivatesTerraMagica", "recluseImprovedIntelligenceAndFaithReducedMind", "raiderImprovedMindAndIntelligenceReducedVigorAndEndurance", "wylderImprovedIntelligenceAndFaithReducedStrengthAndDexterity"] + AFF,
    opt=UNIV + ARTKILL + ["dormantPowerHelpsDiscoverStaves", "duchessUseCharacterSkillForBriefInvulnerability", "improvedRoarAndBreathAttacks"],
    avoid=["reducedStrengthAndIntelligence", "reducedIntelligenceAndDexterity", "duchessImprovedMindAndFaithReducedIntelligence"],
    nonrelic=["improvedChargedSorceries", "improvedSpellCastingSpeed", "reducedSpellFpCost", "dmgNegationUpWhileCastingSpells", "raisesSorceryIncantationPotency"],
    missing_note="- 「詠唱速度上昇」「タメ魔術強化」「魔術/祈祷の消費FP軽減」「詠唱中カット率上昇」はいずれも付帯効果のみ（遺物に無し）。",
    notes="""
- 遺物効果「魔術強化」と「魔力攻撃力上昇」は別物。物理/魔力等の攻撃力上昇は魔術にも乗るが、杖の魔術補正には反映されない（遺物効果ページ）。
- 系統特化の理論上限: 通常枠＝系統強化(12%)＋対応属性+2(6%)×3、深層枠＝系統強化＋対応属性+4(12%)×3 で合計約230%（遺物効果ページ FAQ。現実的には入手困難）。
- 「【レディ】スキル使用時、僅かに無敵」は効果の評価が出典で分かれるため任意に置く（中立）。
- 「咆哮とブレス強化」は隠者の混成魔法も対象（遺物効果ページ）→ 隠者のみ任意。
""",
    sources=S(S_GLOSS, S_SORC, S_EFF, C["隠者"], C["レディ"], B("表確定入手だけの簡単魔術ビルド", "2026-09-12"), B("杖出やすくない魔術学者", "2026-10-02"), B("魔力学者", "2026-07-31")))

SORC_SUB = [
    # (表示名, 系統強化key, 中核に入れる出撃時魔術/戦技, extra, 別名, 説明, キャラ, conf, 出典)
    ("輝剣", "improvedGlintbladeSorcery", ["changesCompatibleArmamentsSorceryToMagicGlintbladeAtStartOfExpedition"], MAG,
     "輝剣、輝剣隠者、輝剣型（魔術の輝剣・輝剣の円陣・カーリアの円陣・巨剣陣）",
     "輝剣の魔術（魔術の輝剣・輝剣の円陣など）を主力にする。投稿例は「輝剣の魔術強化」6枠＋魔力攻撃力で、持ち込みはしない構成。用語集「浮遊」は輝剣の円陣など周囲に待機して自動射出するスペルの総称。",
     "隠者、レディ", "中", S(B("輝剣隠者", "2026-10-03"), S_GLOSS)),
    ("重力", "improvedGravitySorcery", [], MAG + PHYS,
     "重力、重力魔術、隕石の杖（重力弾・星砕き・岩石弾・メテオライト・アステール・メテオ）",
     "重力の魔術を主力にする。岩石弾は物理、メテオライト等は物理＋魔力（魔術ページ）。輝剣隠者投稿に「輝剣強化を重力強化に変えてもよいが、隕石の杖がなかなか出ない」とある。",
     "隠者、レディ", "低", S(B("輝剣隠者", "2026-10-03"))),
    ("カーリア", "improvedCarianSwordSorcery", ["changesCompatibleArmamentsSorceryToCarianGreatswordAtStartOfExpedition"], MAG,
     "カーリア、カーリア隠者、カーリアの剣（速剣・大剣・貫き・アデューラの月の剣）",
     "カーリアの剣の魔術で近〜中距離を斬る。カーリアの速剣は消費FP4と燃費が良い（魔術ページ）。投稿例は系統強化6枠＋魔力攻撃力、持ち込みなし。",
     "隠者、レディ", "中", S(B("カーリア隠者", "2026-10-12"), B("属攻盛りローグライク大好きお姉ちゃん", "2026-10-13"))),
    ("結晶", "improvedCrystalianSorcery", [], MAG,
     "結晶、結晶隠者、結晶杖（砕け散る結晶・放たれる結晶・結晶の解放）",
     "結晶人の魔術（砕け散る結晶など）。用語集「結晶」は砕け散る結晶または結晶杖を指すことが多い。輝剣隠者投稿はカリゴ戦では結晶か炎を推奨。1.03.2で砕け散る結晶の消費FP増加、腐敗した結晶杖の1つ目の魔術が結晶の解放に変更（公式）。",
     "隠者、レディ", "中", S(B("結晶隠者", "2026-10-03"), B("Wステ変家族の首隠者", "2026-07-04"), S_GLOSS, S_OFF1032)),
    ("不可視", "improvedInvisibilitySorcery", ["changesCompatibleArmamentsSorceryToNightShardAtStartOfExpedition"], MAG,
     "不可視、不可視特化（夜のつぶて・夜の彗星）",
     "不可視の魔術（夜のつぶて・夜の彗星。魔術ページの分類）に特化。投稿例は不可視強化6枠、夜のつぶて持ち込み→夜の彗星を拾ったら乗り換え。夜の彗星は燃費が悪く、撃破時アーツ等で補う。",
     "隠者、レディ", "中", S(B("不可視特化ビルド", "2026-09-23"))),
    ("茨", "improvedThornSorcery", ["changesCompatibleArmamentsSorceryToBriarsOfPunishmentAtStartOfExpedition"], MAG,
     "茨、瓦礫茨隠者、罰の茨・罪の茨",
     "茨の魔術（罰の茨・罪の茨。魔力＋出血）。自傷で自分の出血ゲージを溜められるので「瓦礫」と組む投稿がある（→「瓦礫」項）。",
     "隠者", "中", S(B("瓦礫茨隠者", "2026-09-29"))),
    ("石掘り", "improvedStonediggerSorcery", [], MAG,
     "石掘り（岩盤砕き・岩盤発破）",
     "石掘りの魔術（岩盤砕き＝石掘り杖の固定魔術、岩盤発破）。型としての投稿は見つからないが、系統強化遺物があり組める。",
     "隠者、レディ", "低", ""),
]
for nm, key, spells, extra, al, d, ch, cf, src in SORC_SUB:
    add(cat="魔術・祈祷系", name=f"魔術（{nm}）", conf=cf,
        aliases=al, desc=d, chars=ch,
        core=[key] + spells, good=SORC + extra + INT, opt=FPSUST + MIND + UNIV + AFF,
        avoid=["reducedStrengthAndIntelligence", "reducedIntelligenceAndDexterity"],
        notes=f"- 系統強化は12%・重ね掛け可（遺物効果ページの検証: 1つ12%／2つ25%／3つ40%）。{DEEP_SCHOOL}\n- 「出撃時の武器の魔術を○○にする」は献器の最も左のみ有効。共通事項は「魔術特化」参照。",
        sources=S(*(x for x in [src, S_SORC, S_EFF] if x)))

add(cat="魔術・祈祷系", name="祈祷特化", conf="高",
    aliases="祈祷、祈祷型、信仰型、聖印、祈祷葬儀屋、信仰バード（信仰守護者）、祈祷・属性型、怒り復（黄金の怒り復讐者）",
    desc="聖印の祈祷を主攻撃・支援にする型。系統強化遺物「○○の祈祷を強化」（12%・重ね掛け可）が系統ごとにあり、投稿も系統名で呼ぶ（ビースト、狂い火、雷の槍など、下の各項）。系統は祈祷ページの「分類」列で確認できる。",
    chars="復讐者（主）、葬儀屋（祈祷葬儀屋、【葬儀屋】祈祷による補助効果発生時、物理攻撃力上昇）、守護者・追跡者（信仰ステ変・祈祷属性型）、隠者。",
    core=INC + FAI + FPSUST,
    good=MIND + ["maxFpUpWith3PlusSacredSealsEquipped", "extendedSpellDuration", "undertakerPhysicalAttacksBoostedWhileAssistEffectFromIncantationIsActiveForSelf",
                 "guardianImprovedMindAndFaithReducedVigor", "undertakerImprovedMindAndFaithReducedStrength", "duchessImprovedMindAndFaithReducedIntelligence", "wylderImprovedIntelligenceAndFaithReducedStrengthAndDexterity",
                 "changesCompatibleArmamentsIncantationToWrathOfGoldAtStartOfExpedition"] + AFF,
    opt=UNIV + ["dormantPowerHelpsDiscoverSacredSeals"] + FIRE[:3] + LIT[:3] + HOLY[:3],
    avoid=["reducedDexterityAndFaith", "reducedFaithAndStrength", "revenantImprovedStrengthReducedFaith"],
    nonrelic=["improvedChargedIncantation", "improvedSpellCastingSpeed", "reducedSpellFpCost"],
    notes="""
- 祈祷の多くは属性（炎・雷・聖）攻撃なので「属性攻撃力上昇」系が乗る（祈祷・属性型追跡者、祈祷葬儀屋の投稿は属攻盛り）。物理の祈祷（獣など）は物理攻撃力上昇。
- 「出撃時の武器の祈祷を「黄金の怒り」にする」は系統強化で特化できないが、初期聖印に付与できる唯一の聖属性祈祷（復讐者ページ）。
- 復讐者はもともと聖印の入手率が高く「聖印を見つけやすくなる」は効果が無い（復讐者ページ）。
""",
    sources=S(S_INC, S_EFF, C["復讐者"], B("祈祷葬儀屋", "2026-10-12"), B("汎用型信仰バード", "2026-07-17"),
              B("汎用型怒り復", "2026-09-04"), B("祈祷・属性型【追跡者】", "2026-10-25")))

INC_SUB = [
    ("竜餐", "improvedDragonCommunionIncantations", ["changesCompatibleArmamentsIncantationToDragonfireAtStartOfExpedition", "improvedRoarAndBreathAttacks"], FIRE + MAG[:3],
     "竜餐、竜餐祈祷、竜炎、ブレス",
     "竜餐の祈祷（竜炎・輝石ブレス・竜氷・腐敗ブレス・竜爪・グレイオールの咆哮など）。ブレス・咆哮系は「咆哮とブレス強化」（15%）の対象で、竜炎は系統強化＋咆哮とブレス強化の両方が乗り特化時の火力は高いが FP 消費が非常に大きい（復讐者ページ）。ブレスの属性は炎・魔力・冷気・腐敗と様々（祈祷ページ）。用語集: 竜餐の対象は「飛竜」のみで「古竜」は対象外。",
     "復讐者、隠者", "中", S(S_GLOSS, C["復讐者"])),
    ("王都古竜", "improvedDragonCultIncantations", ["changesCompatibleArmamentsIncantationToLightningSpearAtStartOfExpedition"], LIT,
     "雷、雷の槍、古竜、王都古竜、雷祈祷",
     "王都古竜信仰の祈祷（雷の槍など）。雷の槍は素直な弾道で射程が長め、エデレ・グノスター・カリゴ以外の夜の王に有効で汎用性が高い（復讐者ページ）。投稿例は雷の槍持ち込み＋王都古竜強化×3＋属性攻撃力＋ハルハル。",
     "復讐者（主）、隠者、追跡者・守護者（信仰ステ変）", "中", S(B("対マリス用雷の槍ver.2", "2026-07-31"), C["復讐者"])),
    ("巨人の火", "improvedGiantsFlameIncantations", ["changesCompatibleArmamentsIncantationToOFlameAtStartOfExpedition"], FIRE,
     "火、炎祈祷、巨人の火（火よ！・巨人の火をくらえ）",
     "巨人の火の祈祷（火よ！・巨人の火をくらえ など、全て炎属性で数も多い）。巨人の聖印の固定祈祷が「巨人の火をくらえ」に変わって実用性が向上。持ち込みの「火よ！」は射程が非常に短い（復讐者ページ）。",
     "復讐者", "中", S(C["復讐者"])),
    ("黄金律", "improvedFundamentalistIncantations", [], HOLY,
     "聖、聖祈祷、黄金律原理主義（光輪・三なる光輪・ラダゴンの光輪）",
     "黄金律原理主義の祈祷（光輪系）。黄金律の聖印はレアで入手性に難がある（復讐者ページ）。初期聖印を「黄金の怒り」（聖属性）にする遺物はあるが、黄金の怒りは系統強化の対象外なので聖攻撃力上昇・属性攻撃力上昇で補う。",
     "復讐者、守護者・葬儀屋（信仰）", "低", S(C["復讐者"])),
    ("神狩り", "improvedGodslayerIncantations", [], FIRE,
     "黒炎、神狩り（黒炎・薙ぎ払う黒炎・黒炎の儀式）",
     "神狩りの祈祷（黒炎系）。神狩りの聖印はアンコモンで入手しやすいが、**黒炎のスリップダメージは系統強化・バフ等で強化されない**ため威力が伸び悩む（遺物効果ページ・復讐者ページ）。",
     "復讐者", "低", S(C["復讐者"])),
    ("獣", "improvedBestialIncantations", ["changesCompatibleArmamentsIncantationToBeastClawAtStartOfExpedition"] + PHYS, [],
     "ビースト、ビースト復讐者、ビーフク、ビーフ、獣爪、獣の祈祷",
     "獣の祈祷（獣爪・グラングの獣爪・獣の石・グラングの岩。いずれも **物理属性**、祈祷ページ）に特化した復讐者。遺物「出撃時の武器の祈祷を「獣爪」にする」を契機に主要ビルドとして台頭（用語集）。獣爪＋「獣の祈祷を強化」または「物理攻撃力上昇+2」は1つの遺物内で噛み合う組み合わせとして用語集に挙がる。獣爪は相手を選ばず使え、FP効率・命中率に優れる（復讐者ページ）。",
     "復讐者", "中", S(S_GLOSS, C["復讐者"], S_OFF1032)),
    ("狂い火", "improvedFrenziedFlameIncantations", [], FIRE + ["madnessInVicinityImprovesAttackPower", "madnessInVicinityImprovesAttackPowerPlus1", "statusAilmentGaugesSlowlyIncreaseAttackPower"],
     "狂い火、瓦礫狂い火、発狂祈祷",
     "狂い火の祈祷（狂い火・堪えきれぬ狂い火など。炎＋発狂）。強力だが自分にも発狂が溜まり、狂い火の聖印はレアで入手しにくい（復讐者ページ）。自分の発狂ゲージを「瓦礫の夜」で火力に変える投稿あり。",
     "復讐者", "中", S(B("瓦礫狂い火ダフネ", "2026-09-20"), C["復讐者"])),
]
for nm, key, spells, extra, al, d, ch, cf, src in INC_SUB:
    note = f"- 系統強化は12%・重ね掛け可（遺物効果ページ）。{DEEP_SCHOOL}\n- 「出撃時の武器の祈祷を○○にする」は献器の最も左のみ有効。共通事項は「祈祷特化」参照。"
    if nm.startswith("獣"):
        note += "\n- **筋力は獣の祈祷の威力を伸ばさない**（オーナー確認）ため筋力系は載せていない。物理攻撃力上昇は有効で、祈祷にも乗る（遺物効果ページ:「魔術・祈祷・アイテムにも効果あり」）。\n- 1.03.2 で獣爪の消費FP増加、攻撃判定が消滅する不具合を修正（公式）。"
    add(cat="魔術・祈祷系", name=f"祈祷（{nm}）", conf=cf,
        aliases=al, desc=d, chars=ch,
        core=[key] + spells, good=INC + extra + FAI, opt=FPSUST + MIND + UNIV + ([] if nm.startswith("獣") else AFF),
        avoid=["reducedDexterityAndFaith", "reducedFaithAndStrength"],
        notes=note,
        sources=S(src, S_INC, S_EFF))

add(cat="魔術・祈祷系", name="特定術の固定", conf="中",
    aliases="持ち込み、初期魔術/初期祈祷固定、○○固定、表確定（確定入手遺物のみ）",
    desc="「出撃時の武器の魔術/祈祷を○○にする」遺物（Ver.1.03 追加・DLC 適用時のみ）で、隠者の初期杖・復讐者の初期聖印の通常攻撃ボタン側の術を確定させ、ランダム性を排除する型。獣爪・雷の槍・魔術の輝剣などが代表（遺物効果ページ）。",
    chars="隠者・復讐者（変更できるのはこの2キャラの初期触媒）。",
    core=["changesCompatibleArmamentsSorceryToMagicGlintbladeAtStartOfExpedition", "changesCompatibleArmamentsSorceryToCarianGreatswordAtStartOfExpedition", "changesCompatibleArmamentsSorceryToNightShardAtStartOfExpedition",
          "changesCompatibleArmamentsSorceryToMagmaShotAtStartOfExpedition", "changesCompatibleArmamentsSorceryToBriarsOfPunishmentAtStartOfExpedition",
          "changesCompatibleArmamentsIncantationToWrathOfGoldAtStartOfExpedition", "changesCompatibleArmamentsIncantationToLightningSpearAtStartOfExpedition", "changesCompatibleArmamentsIncantationToOFlameAtStartOfExpedition",
          "changesCompatibleArmamentsIncantationToBeastClawAtStartOfExpedition", "changesCompatibleArmamentsIncantationToDragonfireAtStartOfExpedition"],
    good=SORC + INC, opt=FPSUST, avoid=[],
    notes="- 献器の最も左の遺物の効果のみ発動。各術の系統: 魔術の輝剣＝輝剣、カーリアの大剣＝カーリアの剣、夜のつぶて＝不可視、罰の茨＝茨、雷の槍＝王都古竜信仰、火よ！＝巨人の火、獣爪＝獣、竜炎＝竜餐、溶岩弾・黄金の怒り＝系統なし（遺物効果ページ）。\n- 輝剣隠者・カーリア隠者の投稿は「持ち込まない」構成で、固定は必須ではない。",
    sources=S(S_EFF, S_GLOSS, C["復讐者"], B("輝剣隠者", "2026-10-03"), B("カーリア隠者", "2026-10-12")))

# ============================================================ 状態異常・属性系
add(cat="状態異常・属性系", name="出血", conf="高",
    aliases="出血、出血型、血、血の刃、切腹、スキル出血（追跡者）、自傷出血（隠者）",
    desc="出血の発症で**最大HPの12.5%+100**の割合ダメージ（発症時に怯む）。恐るべき強敵・砦屋上のボス・襲撃イベントのボス・夜ボス・夜の王はダメージ半減、さらにデュオ3/4・トリオ1/2。ナイトレインでは全ての状態異常の蓄積量が神秘で増える（武器による蓄積のみ。道具・魔術・祈祷そのものの蓄積は対象外）（状態変化）。",
    chars="執行者（主）、追跡者（【追跡者】スキルに出血付加。投稿で多用）、レディ（血の刃）、隠者（自身が出血状態になり攻撃力上昇）。",
    core=["startingArmamentInflictsBloodLoss", "wylderCharacterSkillInflictsBloodLoss"] + ARC,
    good=["changesCompatibleArmamentsSkillToBloodBladeAtStartOfExpedition", "changesCompatibleArmamentsSkillToSeppukuAtStartOfExpedition",
          "recluseSufferBloodLossAndIncreaseAttackPower", "successiveAttacksBoostAttackPower"],
    opt=["executorImprovedDexterityAndArcaneReducedVigor", "raiderImprovedArcaneReducedVigor", "ironeyeImprovedArcaneReducedDexterity"] + UNIV,
    avoid=["takingDamageCausesBloodLossBuildup", "reducedVigorAndArcane"],
    notes="- 「出撃時の武器に出血の状態異常を付加」は全属性の攻撃力0.85倍・蓄積量25（遺物効果ページ）。二刀は状態異常蓄積量が減る（用語集）。",
    sources=S(S_STATUS, S_EFF, C["執行者"], C["追跡者"], B("全部乗せ瓦礫切腹追跡者", "2026-07-13")))

FROST_APPLY = ["startingArmamentInflictsFrost", "changesCompatibleArmamentsSkillToHoarfrostStompAtStartOfExpedition", "changesCompatibleArmamentsSkillToChillingMistAtStartOfExpedition"]
FROST_DMG = ["attackPowerUpWhenFacingFrostbiteAfflictedEnemy", "attackPowerUpWhenFacingFrostbiteAfflictedEnemyPlus1", "attackPowerUpWhenFacingFrostbiteAfflictedEnemyPlus2"]
FIRE_HIT = ["startingArmamentDealsFireDamage", "fireGreaseInPossessionAtStartOfExpedition", "flameShroudingCrackedTearInPossessionAtStartOfExpedition",
            "changesCompatibleArmamentsSkillToFlamingStrikeAtStartOfExpedition", "changesCompatibleArmamentsSkillToEruptionAtStartOfExpedition",
            "wylderStandardAttacksEnhancedWithFieryFollowUpsWhenUsingCharacterSkill", "wylderArtActivationSpreadsFireInArea", "firePotsInPossessionAtStartOfExpedition"]

add(cat="状態異常・属性系", name="凍傷", conf="高",
    aliases="凍傷、冷気、凍傷型、凍傷維持、霜踏み、冷気の霧、凍傷特効（凍傷状態の敵に対する攻撃を強化）",
    desc="""
**凍傷を敵に入れたまま維持し、効果時間中の被ダメージ上昇で全体の DPS を上げる型。**
- 凍傷発症で最大HPの10%+50（強敵・夜ボス等は半減、デュオ3/4・トリオ1/2）、**30秒間被ダメージ1.15倍**。凍傷中は冷気が蓄積しない。炎のヒットで解除される（状態変化）。
- 冷気耐性が高く繰り返し凍傷にしにくい敵には、炎以外で凍傷を解除せずに攻撃した方が効率的（用語集「凍傷ループ」）。→ 炎で即解除する運用は別型「凍傷ループ」。
""",
    chars="追跡者（霜踏み・冷気の霧）、執行者（毒＋霜踏み：凍傷の被ダメ上昇デバフを入れて毒・出血で削る構成）、学者（霜踏み）、レディ（霜踏み・冷気付与）、守護者・鉄の目（冷気付与）。",
    core=FROST_APPLY + FROST_DMG,
    good=["nearbyFrostbiteConcealsSelf"] + ARC,
    opt=UNIV + ARTKILL,
    avoid=FIRE_HIT,
    notes="""
- 「凍傷状態の敵に対する攻撃を強化」は +0/+1/+2 で 10%/16%/20%、+値が違えば重ね掛け可（遺物効果ページ）。凍傷中だけ効くので、凍傷を維持するこの型で価値が高い。
- 「避けたい」の炎系は、自分の炎ヒットで凍傷が解除されてしまうため（状態変化）。炎攻撃力上昇の遺物自体は炎ヒットを生まないので避けたいには入れていない。
- 「出撃時の武器に冷気の状態異常を付加」は全属性の攻撃力0.85倍・蓄積量35（遺物効果ページ）。
- マルチでは味方の炎で解除されることも多い（鉄の目ページのコメント）。
""",
    sources=S(S_STATUS, S_GLOSS, S_EFF, C["執行者"], C["追跡者"], C["鉄の目"], B("サポ壺アーツぶん回し", "2026-10-03"), B("ロマン死かき棒", "2026-07-13")))

add(cat="状態異常・属性系", name="凍傷ループ", conf="高",
    aliases="凍傷ループ、凍傷解凍ループ、解凍ループ",
    desc="""
**炎属性の攻撃で凍傷を即解除→冷気を再蓄積→再発症を繰り返し、発症時の割合ダメージを何度も与える型**（用語集「凍傷ループ」）。
- 通常は凍傷が30秒続き、その間は冷気が蓄積しない。炎のヒットで解除すれば再び蓄積・発症できる（状態変化・用語集）。
- トロルや植物系など冷気耐性が低い敵に特に有効。冷気耐性の高い敵には非効率（その場合は「凍傷」型の維持が有利）。
- 炎の手段: 炎攻撃力を持つ武器、火脂、火炎壺など（守護者ページ）。追跡者の大剣追撃（炎）や冷気の霧との組み合わせ（追跡者ページのコメント）、学者の火炎壺（学者ページ）、執行者の炎属性手段（執行者ページ）。
""",
    chars="追跡者（冷気の霧/霜踏み＋大剣追撃・延焼）、学者（霜踏み＋火炎壺。投稿で「壺レベル3の凍傷ループ」）、執行者、守護者（霜踏み＋火脂/火炎壺）。",
    core=FROST_APPLY + FIRE_HIT,
    good=["improvedThrowingPotDamage", "improvedThrowingPotDamagePlus1", "smallPouchInPossessionAtStartOfExpedition"] + FIRE + ARC,
    opt=FROST_DMG + UNIV + ARTKILL,
    avoid=[],
    notes="""
- 出撃時の武器の「戦技変更」と「属性/状態異常付加」はそれぞれ最も左の1つだけ有効だが**別枠**なので、「霜踏み/冷気の霧（戦技）＋炎攻撃力を付加（付加）」や「冷気の状態異常を付加＋炎撃（戦技）」は併用できる（遺物効果ページ）。
- 炎で解除すると凍傷中の被ダメ1.15倍の時間は短くなるので、「凍傷状態の敵に対する攻撃を強化」は任意に置いた。
- 敵は状態異常を発症するたびに耐性値が一段階上がる（状態変化）ため、ループの回数には限りがある。
""",
    sources=S(S_GLOSS, S_STATUS, S_EFF, C["守護者"], C["追跡者"], C["学者"], C["執行者"], B("杖出やすくない魔術学者", "2026-10-02")))

add(cat="状態異常・属性系", name="毒", conf="中",
    aliases="毒、毒ビルド、毒の目（鉄の目の毒スキル）、毒鉄の目、スキル毒、猛毒",
    desc="""
**敵を毒にしてスリップダメージを与え、毒状態の敵への攻撃強化で上乗せする型。** 自分側のゲージを使う運用は「瓦礫」項。オーナーの方針で「腐敗」とは別の型にした（鉄の目に毒ビルドがあるため）。
- 毒: 40秒間に31回、1回あたり最大HP0.1%+10（累計約3.1%+310）。糞壺・毒の噴霧による「猛毒」は約3.565%+372（状態変化）。
- 鉄の目は専用遺物（スキルに毒を付加し毒状態の敵に大ダメージ／アーツのタメ発動時、毒の状態異常を付加＝蓄積量300でほぼ一撃で毒）で毒型の代表（鉄の目ページ）。
- マルチでは凍傷・出血より他人と重複しづらく、解除もされにくい（鉄の目ページ）。
""",
    chars="鉄の目（毒。スキル毒・アーツタメ毒）、執行者（毒＋霜踏み、4色刀）。",
    core=["startingArmamentInflictsPoison",
          "attackPowerUpWhenFacingPoisonAfflictedEnemy", "attackPowerUpWhenFacingPoisonAfflictedEnemyPlus1", "attackPowerUpWhenFacingPoisonAfflictedEnemyPlus2"],
    good=["ironeyeCharacterSkillInflictsHeavyPoisonDamageOnPoisonedEnemies", "ironeyeArtChargeActivationAddsPoisonEffect", "poisonAndRotInVicinityIncreasesAttackPower",
          "changesCompatibleArmamentsSkillToPoisonousMistAtStartOfExpedition", "changesCompatibleArmamentsSkillToPoisonMothFlightAtStartOfExpedition"] + ARC,
    opt=["poisonSpraymistInPossessionAtStartOfExpedition", "poisonboneDartsInPossessionAtStartOfExpedition", "ironeyeAdditionalCharacterSkillUse", "ironeyeImprovedArcaneReducedDexterity"],
    avoid=["takingDamageCausesPoisonBuildup", "poisonBuildupWhenBelowMaxHP"],
    notes="""
- 「毒状態の敵に対する攻撃を強化」は 10%/16%/20%（+0/+1/+2、+値違いで重ね掛け可）、魔術/祈祷や属性攻撃も対象（遺物効果ページ）。
- 「周囲で毒/腐敗状態の発生時、攻撃力上昇」は12%・20秒（遺物効果ページ）。自分の毒でも発動する（執行者ページ、オーナー確認 Q19）。
- 「避けたい」の自分側の毒デメリットは、この型ではスリップダメージを自分が受けるだけなので避けたい側（「瓦礫」型ではあえて採用する＝相性良）。遺物効果ページでは毒の被ダメ蓄積デメリットは比較的影響が小さい部類とされる。
- 状態変化ページのコメントに、長期戦なら毒・腐敗の累積ダメージは凍傷・出血を上回り得るという試算がある。
""",
    sources=S(S_STATUS, S_EFF, C["鉄の目"], C["執行者"], B("両刃剣の目", "2026-07-19"), B("単一遺物プリセット鉄の目", "2026-10-23"), B("お手軽４色刀", "2026-10-19")))

add(cat="状態異常・属性系", name="腐敗", conf="中",
    aliases="腐敗、朱い腐敗、腐れ、腐敗ビルド",
    desc="""
**敵を腐敗にしてスリップダメージを与え、腐敗状態の敵への攻撃強化で上乗せする型。** 自分側のゲージを使う運用は「瓦礫」項。オーナーの方針で「毒」とは別の型にした。
- 腐敗: 40秒間に31回、1回あたり最大HP0.15%+15（累計約4.65%+465）。毒より減少量が多い（状態変化）。
- 遺物で出撃時の武器に腐敗を付ける手段は現行のゲームに無く、腐敗の武器・道具を拾うか、瓦礫の夜の「被ダメージ時、腐敗の状態異常を付加」（被弾で武器に腐敗を付加）で付ける。
""",
    chars="キャラ非依存（腐敗の武器・道具を拾った場合や瓦礫の夜を使う場合）。投稿例: 無頼漢（腐れ発狂無頼漢）。",
    core=["attackPowerUpWhenFacingScarletRotAfflictedEnemy", "attackPowerUpWhenFacingScarletRotAfflictedEnemyPlus1", "attackPowerUpWhenFacingScarletRotAfflictedEnemyPlus2"],
    good=["poisonAndRotInVicinityIncreasesAttackPower", "attacksInflictRotWhenDamageIsTaken", "rotInVicinityCausesContinuousHpRecovery"] + ARC,
    opt=UNIV,
    avoid=["takingDamageCausesRotBuildup", "rotBuildupWhenBelowMaxHP"],
    notes="""
- 「腐敗状態の敵に対する攻撃を強化」は +0/+1/+2 の段階があり、+値違いで重ね掛け可（遺物効果ページ）。
- 「被ダメージ時、腐敗の状態異常を付加」「周囲で腐敗状態の発生時、HP持続回復」は瓦礫の夜の固有効果。前者は武器に腐敗エンチャントを強制上書きするので、他のエンチャントと併用しにくい（瓦礫の夜ページ）。
- 「周囲で毒/腐敗状態の発生時、攻撃力上昇」は自分の腐敗でも発動する（執行者ページ、オーナー確認 Q19）。
- 自分側の腐敗デメリットは、この型ではスリップダメージを自分が受けるだけなので避けたい側（「瓦礫」型ではあえて採用する）。
""",
    sources=S(S_STATUS, S_EFF, S_GAREKI, B("腐れ発狂無頼漢", "2026-10-03")))

add(cat="状態異常・属性系", name="瓦礫", conf="高",
    aliases="瓦礫、瓦礫型、瓦礫バフ、瓦礫の夜、ストラゲス遺物、ガレキング遺物、瓦礫○○（瓦礫茨隠者・瓦礫狂い火ダフネ・全部乗せ瓦礫切腹追跡者・瓦礫ナメ鉄）",
    desc="""
固有遺物「瓦礫の夜」（瓦礫の王撃破で入手）の **「状態異常ゲージがある時、徐々に攻撃力上昇」** を軸に、**自分の状態異常ゲージを出し続けて**攻撃力バフを積む型。
- バフはゲージ発生時に1回、以後20秒ごとに追加、最大10回（3分）で約1.45倍。20秒ごとの判定時にゲージが無いとバフは解除（瓦礫の夜ページ・遺物効果ページ）。
- 自分のゲージを維持する手段: 深層デメリット「HP最大未満時、毒/腐敗が蓄積」（HP85%以下で蓄積）を付け、戦技「切腹」の自傷などでHPを85%以下に下げる。盾3つで最大HP上昇→盾を捨てて拾い直す方法もある（瓦礫の夜ページ）。ほかに茨の魔術の自傷出血、狂い火の自己発狂、リブラ遺物の「あぐら」で発狂、敵や地形からの被蓄積。
""",
    chars="全キャラ。投稿例: 追跡者（切腹）、隠者（茨＋HP最大未満時毒）、復讐者（狂い火）、鉄の目（ナメレス遺物と併用）、無頼漢（あぐら・腐れ発狂）、執行者（切腹＋未満腐敗のコメント、4色刀）。",
    core=["statusAilmentGaugesSlowlyIncreaseAttackPower", "poisonBuildupWhenBelowMaxHP", "rotBuildupWhenBelowMaxHP"],
    good=["changesCompatibleArmamentsSkillToSeppukuAtStartOfExpedition", "takingDamageCausesPoisonBuildup", "takingDamageCausesRotBuildup",
          "improvedThornSorcery", "changesCompatibleArmamentsSorceryToBriarsOfPunishmentAtStartOfExpedition", "recluseSufferBloodLossAndIncreaseAttackPower",
          "improvedFrenziedFlameIncantations", "gestureCrossedLegsBuildsUpMadness",
          "slowlyRestoreHpForSelfAndNearbyAlliesWhenHpIsLow", "continuousHpRecovery", "improvedDamageNegationAtLowHP"] + REGAIN,
    opt=["attacksInflictRotWhenDamageIsTaken", "rotInVicinityCausesContinuousHpRecovery", "madnessContinuallyRecoversFP",
         "maxHpUpWith3PlusGreatshieldsEquipped", "maxHpUpWith3PlusMediumShieldsEquipped", "maxHpUpWith3PlusSmallShieldsEquipped"] + PHYS + UNIV,
    avoid=["lowerAttackWhenBelowMaxHP", "takingDamageCausesDeathBuildup"],
    notes="""
- オーナー確認: ゲージは **自分側**。瓦礫の夜ページも「HP最大未満時、○○が蓄積」との組み合わせで発動・累積させやすいと説明している。
- 「被ダメージ時、腐敗の状態異常を付加」「周囲で腐敗状態の発生時、HP持続回復」は瓦礫の夜に同居する固有効果（実質セット）。ただし前者は武器に腐敗エンチャントを強制上書きするので他のエンチャントと併用しにくく、自分の腐敗発症は回復で打ち消しきれないので敢えて自分を腐敗状態にする運用は避けた方がよい、とページにある → 任意。
- 祝福・聖杯瓶などで HP が戻るとゲージが消えてリセットされやすい（ページコメント）。腐れ森の恩寵は深層の「HP最大未満時、腐敗が蓄積」も無効化する（コメント）。
- 「HP最大未満時、攻撃力低下」は HP を下げて戦う本型と衝突するので避けたい。「被ダメージ時、死を蓄積」は発症＝即瀕死なので避けたい。
""",
    sources=S(S_GAREKI, S_EFF, S_GLOSS, B("全部乗せ瓦礫切腹追跡者", "2026-07-13"), B("瓦礫茨隠者", "2026-09-29"),
              B("瓦礫狂い火ダフネ", "2026-09-20"), B("瓦礫ナメ鉄・瓦礫ナメの目", "2026-08-23"), B("腐れ発狂無頼漢", "2026-10-03")))

add(cat="状態異常・属性系", name="睡眠", conf="低",
    aliases="睡眠、眠り",
    desc="敵の睡眠リアクション中は被ダメージ1.2倍。眠り込む敵は放置すればしばらく止まり、眠り込み中に致命を入れられる敵もいる。眠り込まない敵もふらつきで少し止まる。発症時に実行中の行動は最後まで行うので攻撃キャンセルには使えない（状態変化）。遺物で睡眠を付ける手段は現行では無く、睡眠武器・道具を拾った場合の型。",
    chars="キャラ非依存（睡眠を蓄積できる武器・道具を拾った場合）。投稿では葬儀屋（大斧ビルド）が「周囲で睡眠状態の発生時、攻撃力上昇」を採用。",
    core=["sleepInVicinityImprovesAttackPower", "sleepInVicinityImprovesAttackPowerPlus1"],
    good=ARC,
    opt=["improvedSleepResistance", "improvedSleepResistancePlus1"] + UNIV,
    avoid=["takingDamageCausesSleepBuildup"],
    notes="""
- 「周囲で睡眠状態の発生時、攻撃力上昇」は 12%（+1 は 22%）、+値違いで重ね掛け可（遺物効果ページ）。自分が睡眠状態になった場合にも発動するかは未確認。
- 睡眠耐性は深海の夜、マリスの「睡眠誘い」対策として投稿で採用されている（単一遺物プリセット鉄の目）。練習用・耐久寄りの構成でも有用。
- 型としての投稿はほぼ無く、提供価値は低め（信頼度 低）。
""",
    sources=S(S_STATUS, S_EFF, B("錨を担げ！（葬儀屋大斧ビルド）", "2026-07-21"), B("単一遺物プリセット鉄の目", "2026-10-23")))

add(cat="状態異常・属性系", name="発狂", conf="中",
    aliases="発狂、狂い火、あぐら、発狂バフ、腐れ発狂",
    desc="敵への発狂（最大HP・FPの20%＋行動不能、被ダメ1.2倍）が有効なのはリブラ（常夜含む）・夜の侵入者・常夜リブラが召喚する罪人・訓練場の人形兵のみ（状態変化）。ナイトレインではむしろ **自分を発狂させてバフを得る** 使い方が型として成立している（魔の暗き夜の「あぐら」で自分に発狂→FP持続回復、周囲で発狂発生時攻撃力上昇、瓦礫の夜）。",
    chars="無頼漢（腐れ発狂無頼漢：被弾バフと組む）、復讐者（狂い火）、追跡者（対リブラ決戦）。",
    core=["madnessInVicinityImprovesAttackPower", "madnessInVicinityImprovesAttackPowerPlus1", "gestureCrossedLegsBuildsUpMadness", "madnessContinuallyRecoversFP"],
    good=["takingAttacksImprovesAttackPower", "statusAilmentGaugesSlowlyIncreaseAttackPower", "improvedFrenziedFlameIncantations"] + REGAIN + ["slowlyRestoreHpForSelfAndNearbyAlliesWhenHpIsLow"],
    opt=["raiderCharacterSkillDamageUp", "raiderDamageTakenWhileUsingCharacterSkillImprovesAttack", "takingDamageCausesMadnessBuildup", "improvedMadnessResistance", "improvedMadnessResistancePlus1"],
    avoid=["lowerAttackWhenBelowMaxHP"],
    notes="""
- 「あぐら」は姿勢を戻すまで高速で発狂が蓄積（執行者Lv15で蓄積〜発症まで約6秒）。「発狂状態になると、FP持続回復」は25秒間毎秒2回復（遺物効果ページ）。
- 投稿者は「スペラーや戦技ビルドでは被弾バフが無駄になりやすく、あぐら待ちが長くリスクに見合わない」としている。
- 「被ダメージ時、発狂を蓄積」は自分の発狂を起こす手段にもなるが、リブラ戦では事故要因（遺物効果ページ）→ 中立に任意。発狂耐性は対リブラ投稿で採用（練習用・耐久寄り）。
- 発狂は発症時に最大HPの20%を失うので、「HP最大未満時、攻撃力低下」は避けたい。
""",
    sources=S(S_STATUS, S_EFF, B("腐れ発狂無頼漢", "2026-10-03"), B("瓦礫狂い火ダフネ", "2026-09-20"), B("対リブラ決戦兄貴", "2026-07-14")))

for nm, base, startkey, grease, tear, skill_keys, char, posts in [
    ("魔力", MAG, "startingArmamentDealsMagicDamage", "magicGreaseInPossessionAtStartOfExpedition", "magicShroudingCrackedTearInPossessionAtStartOfExpedition",
     ["changesCompatibleArmamentsSkillToGlintbladePhalanxAtStartOfExpedition", "changesCompatibleArmamentsSkillToGravitasAtStartOfExpedition"],
     "隠者・レディ（魔術）、復讐者（呪爪に魔力付与）、学者（鈴＋魔力攻撃力）", [B("呪爪フク", "2026-10-02"), B("鈴と鎌とすばやい紳士", "2026-07-21")]),
    ("炎", FIRE, "startingArmamentDealsFireDamage", "fireGreaseInPossessionAtStartOfExpedition", "flameShroudingCrackedTearInPossessionAtStartOfExpedition",
     ["changesCompatibleArmamentsSkillToFlamingStrikeAtStartOfExpedition", "changesCompatibleArmamentsSkillToEruptionAtStartOfExpedition", "wylderStandardAttacksEnhancedWithFieryFollowUpsWhenUsingCharacterSkill", "wylderArtActivationSpreadsFireInArea"],
     "追跡者（大剣追撃・アーツ延焼）、学者（壺）、復讐者（巨人の火）", [B("大剣追撃特化追跡者", "2026-07-04")]),
    ("雷", LIT, "startingArmamentDealsLightningDamage", "lightningGreaseInPossessionAtStartOfExpedition", "lightningShroudingCrackedTearInPossessionAtStartOfExpedition",
     ["changesCompatibleArmamentsSkillToThunderboltAtStartOfExpedition", "changesCompatibleArmamentsSkillToLightningSlashAtStartOfExpedition"],
     "復讐者（雷の槍）、無頼漢（雷撃斬）", [B("対マリス用雷の槍ver.2", "2026-07-31"), B("フルゴ、マリスギミック対応汎用特大無頼漢", "2026-07-20")]),
    ("聖", HOLY, "startingArmamentDealsHolyDamage", "holyGreaseInPossessionAtStartOfExpedition", "holyShroudingCrackedTearInPossessionAtStartOfExpedition",
     ["changesCompatibleArmamentsSkillToSacredBladeAtStartOfExpedition", "changesCompatibleArmamentsSkillToPrayerfulStrikeAtStartOfExpedition"],
     "鉄の目（常夜グラディウス向け聖属性付加）、守護者、復讐者", [B("初めての常夜グラディウス(鉄の目)", "2026-07-20")]),
]:
    add(cat="状態異常・属性系", name=f"{nm}属性", conf="中",
        aliases=f"{nm}、{nm}属性、{nm}付与、{nm}エンチャ、{nm}脂、属攻（属性攻撃力）盛り",
        desc=f"武器を{nm}属性化（出撃時付加・脂・割れ雫・戦技）したり{nm}属性の術を使い、{nm}攻撃力上昇／属性攻撃力上昇 を積む型。ボスの弱点属性に合わせて選ぶことが多い。",
        chars=char,
        core=base + [startkey],
        good=AFF + ["boostsAttackPowerOfAddedAffinityAttacks", grease, tear] + skill_keys,
        opt=["switchingWeaponsAddsAnAffinityAttack"] + UNIV,
        avoid=[],
        notes="- 「○○攻撃力上昇」は武器の表示攻撃力ではなく与ダメージに乗算。戦技・脂のエンチャ分にも乗るが増加分の4〜6%程度（遺物効果ページの検証）。\n- 「出撃時の武器に○○攻撃力を付加」は表示攻撃力がほぼ変わらず、付加される属性攻撃力はレアリティごとに固定（Lvで伸びない）。強靭削りボーナスや特殊怯み目当てで付けるもの。複数付けても最も左のみ有効（遺物効果ページ）。\n- 「脂アイテム使用時、追加で物理攻撃力上昇」は物理のみで、属性型には直接乗らない。",
        sources=S(S_EFF, S_GLOSS, *posts))

add(cat="状態異常・属性系", name="属性付与（属攻盛り）", conf="中",
    aliases="属攻盛り、属性盛り、エンチャント、エンチャ、属性付与、属性型、狩人の暗き夜",
    desc="特定の属性に固定せず、**属性攻撃力上昇**（全属性共通）と「属性攻撃力が付加された時、属性攻撃力上昇」を盛り、拾った脂・祈祷・戦技で属性を付け替える型。後者は「付加された時」とあるが常時効果で、武器・エンチャント・戦技・道具・アーツの属性与ダメージを約1.1倍にする（エンチャント以外の魔術・祈祷は対象外、遺物効果ページ）。この効果を持つ確定入手遺物「狩人の暗き夜」（常夜フルゴール）が軸。「エンチャント」はゲーム内正式用語ではない（用語集）。",
    chars="復讐者（呪爪フク）、追跡者（属攻盛り、祈祷・属性型、知信ステ変短剣）、レディ（属性戦技）、葬儀屋（祈祷葬儀屋）。",
    core=AFF + ["boostsAttackPowerOfAddedAffinityAttacks"],
    good=["switchingWeaponsAddsAnAffinityAttack", "startingArmamentDealsMagicDamage", "startingArmamentDealsFireDamage", "startingArmamentDealsLightningDamage", "startingArmamentDealsHolyDamage",
          "fireGreaseInPossessionAtStartOfExpedition", "magicGreaseInPossessionAtStartOfExpedition", "lightningGreaseInPossessionAtStartOfExpedition", "holyGreaseInPossessionAtStartOfExpedition"] + ARTKILL + END,
    opt=UNIV + MAG[:3] + FIRE[:3] + LIT[:3] + HOLY[:3],
    avoid=[],
    notes="- 1.03.2で「武器の持ち替え時、いずれかの属性攻撃力を付加」発動中、持ち替えた手と逆の手の武器の属性が消える不具合が修正（公式）。同効果は魔力・炎・雷・聖のいずれかを+10、10秒（遺物効果ページ）。",
    sources=S(S_GLOSS, S_EFF, B("呪爪フク", "2026-10-02"), B("祈祷・属性型【追跡者】", "2026-10-25"),
              B("属攻盛りローグライク大好きお姉ちゃん", "2026-10-13"), B("知信ステ変短剣属性盛り自認妹お兄ちゃん", "2026-07-13"), S_OFF1032))

# ============================================================ 役割系
add(cat="役割系", name="タンク", conf="高",
    aliases="タンク、盾役、耐久型、ヘイト役、ヘイト管理、HPタンク（無頼漢）、回避タンク（レディ）、硬い",
    desc="敵の攻撃を引き受ける役割。ナイトレインでは基本的に**守護者**を指す。盾で防ぐだけでなく攻撃でダメージやヘイトを稼ぎ、自分を狙う範囲攻撃に味方を巻き込まない立ち回りが必要。リゲインで回復するHPタンクの無頼漢、回避で引き付ける回避タンクのレディを含めることもある（用語集）。耐久を盛った構成は、被弾しても崩れにくいので **練習用・耐久目的**（夜の王の動きを覚える、事故を減らす）にも使える。",
    chars="守護者（主）、無頼漢（被弾バフ・リゲイン）、レディ（回避）。",
    core=VIG + CUTP + CUTA + ["drawEnemyAttentionWhileGuarding"],
    good=POISE + REGAIN + ["improvedDamageNegationAtLowHP", "continuousHpRecovery", "hpRecoveryFromSuccessfulGuarding", "takingAttacksImprovesAttackPower",
                           "improvedPoiseDamageNegationWhenKnockedBackByDamage", "slowlyRestoreHpForSelfAndNearbyAlliesWhenHpIsLow", "maxHpUpWith3PlusGreatshieldsEquipped",
                           "guardianImprovedStrengthAndDexterityReducedVigor", "revenantImprovedVigorAndEnduranceReducedMind", "executorImprovedVigorAndEnduranceReducedArcane"],
    opt=["magicDamageNegationUp", "fireDamageNegationUp", "lightningDamageNegationUp", "holyDamageNegationUp", "raiderCharacterSkillDamageUp", "raiderHitWithCharacterSkillToReduceEnemyAttackPower"],
    avoid=["continuousHPLoss", "nearDeathReducesMaxHP", "reducedVigorAndArcane"] + EVADE_DEMERIT,
    nonrelic=["lessLikelyToBeTargeted", "improvedDamageNegationAtFullHP"],
    notes="""
- ヘイトコントロールの手段として遺物「ガード中、敵に狙われやすくなる」、付帯効果「敵から狙われ難くなる」がある（用語集「ヘイト」）。後者はタンク以外が付けるとタンクに集まる。
- 「ガード中、敵に狙われやすくなる」は 1.03.2 で上方修正（公式）。詳細な仕様は要検証（遺物効果ページ）。
- 「【無頼漢】スキル命中時、敵の攻撃力低下」は効果の評価が出典で分かれるため任意（中立）。
- 「HP持続減少」「瀕死時、最大HP低下」は遺物効果ページで影響が大きいハズレ扱い。
""",
    sources=S(S_GLOSS, S_EFF, C["守護者"], B("耐久型守護者", "2026-09-07"), B("バードパンチャー・鷹の爪ビルド", "2026-09-08"), S_OFF1032))

add(cat="役割系", name="被弾・リゲイン", conf="中",
    aliases="被弾バフ、被ダメバフ、リゲイン、殴られ型、HPタンク、スキル被弾バフ（無頼漢）",
    desc="攻撃を受けることで攻撃力を上げ（攻撃を受けると攻撃力上昇＝約1.15倍10秒）、被弾直後の攻撃でHPを取り戻す（リゲイン）型。無頼漢のスキル（受けて反撃）と特に相性が良い。発狂・瓦礫と組む派生あり。タンクの下位分類として扱ってもよい。",
    chars="無頼漢（主）、守護者、葬儀屋。",
    core=["takingAttacksImprovesAttackPower"] + REGAIN,
    good=["raiderCharacterSkillDamageUp", "raiderDamageTakenWhileUsingCharacterSkillImprovesAttack", "slowlyRestoreHpForSelfAndNearbyAlliesWhenHpIsLow",
          "improvedPoiseDamageNegationWhenKnockedBackByDamage", "improvedDamageNegationAtLowHP"] + VIG + POISE,
    opt=["madnessInVicinityImprovesAttackPower", "statusAilmentGaugesSlowlyIncreaseAttackPower", "raiderHitWithCharacterSkillToReduceEnemyAttackPower"],
    avoid=["lowerAttackWhenBelowMaxHP", "takingDamageCausesSleepBuildup", "takingDamageCausesMadnessBuildup", "takingDamageCausesDeathBuildup"],
    notes="""
- 「攻撃を受けると攻撃力上昇」は属性ガードの貫通ダメージでも発動、自傷ダメージや0以下の被ダメでは発動しないが「夜巫女の霧」は他者からの攻撃扱いで自己誘発可（遺物効果ページ）。
- 被弾前提なので、被ダメージで行動不能・即死につながる蓄積デメリット（睡眠・発狂・死）は避けたい。
- 「【無頼漢】スキル命中時、敵の攻撃力低下」は評価が分かれるため任意（中立）。
""",
    sources=S(S_EFF, C["無頼漢"], B("腐れ発狂無頼漢", "2026-10-03"), B("汎用無頼漢・HP回復付き", "2026-08-22"), B("物理16無頼漢", "2026-07-03"),
              B("【表固有遺物のみ】これから始めたい方の為の葬儀屋入門ガイド拳編", "2026-08-08")))

add(cat="役割系", name="ヒーラー・サポート", conf="中",
    aliases="ヒーラー、回復役、サポート、サポ、サポ学、支援、バフ役",
    desc="味方のHP回復・カット率/攻撃力バフ・アイテム共有などでパーティを支える型。専用のヒーラーキャラは無く、復讐者（アーツで救助・霊炎）・守護者（スキルで周囲の味方のカット率上昇）・葬儀屋（アーツ中に触れた味方回復）・学者（スキル対象の味方攻撃力上昇・アイテム共有）が担う。回復祈祷（回復・大回復など）も使える（祈祷ページ）。",
    chars="学者（サポ学）、復讐者、守護者、葬儀屋。",
    core=["flaskAlsoHealsAllies", "slowlyRestoreHpForSelfAndNearbyAlliesWhenHpIsLow", "defeatingEnemiesRestoresHPForAlliesButNotForSelf",
          "revenantExpendOwnHPToFullyHealNearbyAllies", "revenantStrengthensFamilyAndAlliesWhenUltimateArtActivated",
          "guardianSlowlyRestoresNearbyAlliesHP", "guardianCharacterSkillBoostsDamageNegationOfNearbyAllies",
          "scholarAlliesTargetedByCharacterSkillGainBoostedAttack", "undertakerContactWithAlliesRestoresTheirHpWhileUltimateArtIsActivated"],
    good=["raisedStaminaRecoveryForNearbyAlliesButNotForSelf", "itemsConferEffectToAllNearbyAllies", "extendedSpellDuration", "improvedFlaskHPRestoration", "increasedRuneAcquisitionForSelfAndAllies"] + INC + ARTCHG,
    opt=["scholarContinuousDamageInflictedOnTargetsThreadedByUltimateArt", "raiderHitWithCharacterSkillToReduceEnemyAttackPower"] + ARTKILL,
    avoid=["reducedFlaskHPRestoration", "reducedDamageNegationForFlaskUsages"],
    notes="""
- 「【復讐者】アーツ発動時、ファミリーと味方を強化」は味方の攻撃力を30秒間1.25倍、自身には無効（復讐者ページ）。
- 「聖杯瓶の回復を、周囲の味方に分配」「アイテムの効果が周囲の味方にも発動」はファミリーにも効く（復讐者ページ）。
- 「魔術／祈祷、効果時間延長」は+50%（遺物効果ページ）。
- 「【無頼漢】スキル命中時、敵の攻撃力低下」は評価が分かれるため任意（中立）。
""",
    sources=S(S_INC, S_EFF, C["復讐者"], C["学者"], B("サポ壺アーツぶん回し", "2026-10-03"), B("クロスボウサポート学者", "2026-07-14")))

add(cat="役割系", name="スキル・アーツ回転", conf="中",
    aliases="アーツ回転、アーツぶん回し、アーツ連打、アーツ型、スキル回転、スキルCT、CT短縮、撃破アーツ（敵を倒した時アーツ増加）、敵倒アーツ、ガードアーツ",
    desc="キャラ固有のスキル（クールタイム制）・アーツ（ゲージ制）の使用頻度を最大化する型。アーツは無敵を持ち救助にも強い（救助ページ）。スキル使用回数+1（追跡者・鉄の目）や「アーツ発動後、スキル再使用可能」（葬儀屋）など固有効果も多い。",
    chars="守護者（アーツ連打バード）、学者（サポ壺アーツぶん回し）、追跡者、鉄の目、葬儀屋、無頼漢（墓石召喚系）、レディ。",
    core=SKILLCD + ARTCHG + ARTKILL,
    good=["artGaugeFillsModeratelyUponCriticalHit", "artGaugeFillsModeratelyUponCriticalHitPlus1",
          "artGaugeChargedFromSuccessfulGuarding", "artGaugeChargedFromSuccessfulGuardingPlus1",
          "wylderAdditionalCharacterSkillUse", "ironeyeAdditionalCharacterSkillUse", "wylderArtGaugeGreatlyFilledWhenAbilityActivated", "undertakerExecutingArtReadiesCharacterSkill",
          "scholarPreventSlowingOfCharacterSkillProgress"],
    opt=["undertakerActivatingUltimateArtIncreasesAttackPower", "raiderDurationOfUltimateArtExtended",
         "revenantTriggerGhostflameExplosionDuringUltimateArtActivation", "recluseActivatingUltimateArtRaisesMaxHP", "improvedRoarAndBreathAttacks"],
    avoid=["ultimateArtChargingImpaired"],
    notes="""
- 「スキルクールタイム軽減+1/+2/+3」は約5%/7.5%/10%、「アーツゲージ自然蓄積+1/+2/+3」は約5%/7.5%/10%、いずれも重ね掛け可。「敵を倒した時、アーツゲージ増加」は撃破ごと約5%、自分以外の撃破でも有効（遺物効果ページ）。
- 「アーツゲージ蓄積鈍化」（約0.85倍）は時間経過・攻撃命中・撃破・致命など全ての充填に適用（遺物効果ページ）。
- 「咆哮とブレス強化」は執行者のアーツの咆哮にも乗る（低価値・任意）。キャラ固有効果は対象キャラ以外では無効なので、ツール側でキャラ絞り込みが必要。
""",
    sources=S(S_EFF, S_RESCUE, C["執行者"], B("アーツ連打バード", "2026-09-17"), B("サポ壺アーツぶん回し", "2026-10-03"),
              B("墓石召喚系海賊", "2026-09-14"), B("耐久型守護者", "2026-09-07")))

add(cat="役割系", name="蘇生役", conf="中",
    aliases="蘇生、救助、起こし役、起こし性能",
    desc="瀕死の味方に攻撃を当てて瀕死ゲージを削り切る役。遠距離攻撃（弓・クロスボウ、スローイングダガーも有用）は射線を確保できれば安全に、スキル・アーツはスタミナを消費せずアーツは無敵なので安全に救助できる。魔術・祈祷はタメても削り量が増えないのでタメずに連続で当てる（救助ページ）。**蘇生に直接効く遺物効果は無く**、遺物との関係は間接的（アーツ回転・遠距離手段・耐久）。耐久を盛った構成は自分が倒れないための**練習用・耐久目的**にもなる。",
    chars="復讐者（アーツ・セバスチャンの咆哮）、追跡者（アーツ225削りで2目盛りまで一撃）、守護者（斧槍ジャンプ二刀攻撃は1ゲージを一撃）、執行者（アーツ中の咆哮）、隠者（魔術）、鉄の目（弓・マーキングで射線確保）。",
    core=ARTCHG + ARTKILL,
    good=SKILLCD + ["revenantExpendOwnHPToFullyHealNearbyAllies", "undertakerContactWithAlliesRestoresTheirHpWhileUltimateArtIsActivated", "wylderArtActivationSpreadsFireInArea", "executorRoaringRestoresHPWhileArtActive"] + VIG,
    opt=["improvedBowAttackPower", "improvedInitialStandardAttack", "throwingDaggersInPossessionAtStartOfExpedition"] + SORC,
    avoid=["ultimateArtChargingImpaired", "nearDeathReducesMaxHP"],
    missing_note="- 「救助速度上昇」「瀕死ゲージ減少量増加」のような蘇生専用の遺物効果はファイルに無し。",
    notes="- 1.03.2で遠距離攻撃の瀕死ゲージ削りに距離減衰が適用（公式）。追跡者の「アーツ発動時、周囲を延焼」は3ゲージでも瀕死ゲージの戻りを阻害できる（救助ページ）。役割として「型」にするかは要判断（キャラ選択でほぼ決まる）。",
    sources=S(S_RESCUE, S_GLOSS, C["守護者"], C["執行者"], C["復讐者"], S_OFF1032))

add(cat="役割系", name="回避型", conf="低",
    aliases="回避タンク、超回避、ローリング、ジャスト回避、クイステ",
    desc="回避（ローリング・クイックステップ）で被弾を避けて攻撃し続ける型。用語集ではレディを「回避タンク」と呼ぶ例あり。回避と相性の良い直剣一段目で隙の少ない攻撃を入れる投稿や、守護者の回避の弱点をクイステで補う投稿がある。耐久を盛らずとも倒れにくい立ち回りの **練習用・耐久目的** にもなる。",
    chars="レディ（【超回避】直剣レディ）、守護者（クイステ）。",
    core=["changesCompatibleArmamentsSkillToQuickstepAtStartOfExpedition"] + END + STAMREC,
    good=["improvedInitialStandardAttack"] + VIG,
    opt=["duchessUseCharacterSkillForBriefInvulnerability", "wylderArtGaugeGreatlyFilledWhenAbilityActivated"],
    avoid=EVADE_DEMERIT,
    nonrelic=["improvedDodging", "lightningUponDodging"],
    missing_note="- 「回避性能上昇」「回避時、雷を発生」は付帯効果/潜在のみ（遺物に無し）。",
    notes="""
- 深層デメリット「回避直後の被ダメージ増加」（wiki の検証ではカット率-45%、回避モーション全体が対象）、「回避連続時、カット率低下」（-35%・15秒・スタック上限なし）は回避型と最も衝突する（遺物効果ページ）。
- 「【レディ】スキル使用時、僅かに無敵」は効果の評価が出典で分かれるため任意（中立）。
- 型としての独立性は低く、デメリット選択（回避系デメリットを避ける）用のタグとしての価値が大きい。
""",
    sources=S(S_GLOSS, S_EFF, B("【超回避】直剣レディ", "2026-07-18"), B("クイステタニムラッシュ守護者", "2026-09-08"), B("クイステ2刀の理想形の1案", "2026-09-08")))

# ============================================================ 参考（別軸）
add(cat="参考（別軸）", name="武器種特化", conf="中", axis="weapon",
    aliases="○○使い、○○特化（大槍特化・拳追跡者・斧ぃちゃん等）、得意武器、○○出やすい、○○3つ",
    desc="**型ではなく独立した別軸（武器種フィルタ）として扱う参考項目。** 特定の武器種に絞り、武器種名つき遺物（○○の攻撃力上昇／○○の武器種を3つ以上装備していると攻撃力上昇／潜在する力から○○を見つけやすくなる／○○の攻撃でHP・FP回復）を積む。キャラの得意武器と合わせるのが基本。",
    chars="全キャラ。投稿例: 拳追跡者、斧ぃちゃん（斧）、ローグライク型物理大槍、ステ変直剣追跡者、猛禽の鉤爪追跡者（爪）、マサカリバード（斧）、錨を担げ！（大斧）。",
    core=wt_many(["大剣"], ("atk", "3plus", "find")),
    good=wt_many(["大剣"], ("hp", "fp")),
    opt=[], avoid=[],
    notes="- 上の効果は「大剣」を例示。実装では選んだ武器種に置換する（全24武器種＋大弓/クロスボウ/バリスタ、盾・杖・聖印の3本系あり）。\n- 「潜在する力から、○○を見つけやすくなる」は出現しやすい武器種を置き換える効果。複数付けると（深層も含め）左に付けたものが優先される。出現確率は拠点や強敵で大きく変わる（遺物効果ページ FAQ、復讐者ページ）。当初は深層専用だったが Ver.1.03 から通常の遺物にも付く。\n- 同じ「攻撃力」分類（武器種の攻撃力上昇・3本で攻撃力上昇・物理攻撃力上昇など）は1つの遺物に同時に付かない（遺物効果ページ「組み合わせのルール」）。",
    sources=S(S_EFF, C["復讐者"], B("拳追跡者", "2026-07-05"), B("斧ぃちゃん", "2026-07-13"), B("ローグライク型物理大槍", "2026-07-14"), B("ステ変直剣追跡者", "2026-07-03")))
