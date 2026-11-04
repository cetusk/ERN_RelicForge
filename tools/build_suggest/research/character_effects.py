"""キャラごとのデメリットの評価（ビルド提案の条件に使うもの）。出典は神攻略wiki のみ（2026-11-01 調査）

全キャラ共通の評価（characters_gen.py の AVOID_COMMON など）と違う扱いになるものだけを書く。根拠の一覧と集計は
character_research.json（付録 catalog/characters.md の元データ）。

オーナーの方針（2026-11-01）:
  - 本文（キャラページ・遺物効果ページの本文）の評価を主に使う → tier "body"（除外の重み: 推奨）
  - コメント欄の評価は、複数の投稿で一致したものだけ使う → tier "comment"（除外の重み: 任意）
      一致 = 同じ評価の投稿が 3 件以上、かつ反対の 2 倍以上（同じ人の連投は 1 件）
  - 本文の評価でも、最近のコメントがはっきり反対していれば（3 件以上かつ 2 倍以上）「割れる」として扱いを変えない
  - 版ごとの性能変更の影響を加味する: 関係する変更より前の投稿は数えない（例: 被ダメージ時の蓄積は
    Ver.1.02.3 からガードでは溜まらない → 守護者はそれ以降の投稿だけ）
  - 条件付きの評価（「瓦礫ビルドなら」「重ね付けしなければ」など）は使わない
  - 理由（why）は画面にそのまま出すので短く。キャラの数値は該当するものだけを添える

各項目: ids（effects_data.json の ID）, verdict（"avoid"）, tier（"body" / "comment"）, why（短い理由）
"""

DEMERITS = {
    '追跡者': [
        dict(ids=[6840200], verdict='avoid', tier='comment', why='カリゴなどの大技阻止にアーツが要る'),
    ],
    '守護者': [
        dict(ids=[6850700], verdict='avoid', tier='body', why='ステップの無敵が全キャラで最短（20F）'),
        dict(ids=[6820400, 6820500], verdict='avoid', tier='body', why='発症すると隙が大きい'),
        dict(ids=[6840200], verdict='avoid', tier='body', why='回復のアーツが必要な時に溜まっていない'),
        dict(ids=[6851700], verdict='avoid', tier='body', why='HPが減るとガードカウンターも弱まる'),
        dict(ids=[6851200, 6851300, 6851400], verdict='avoid', tier='comment', why='ガードの貫通でHPが削れたまま戦いやすい'),
    ],
    'レディ': [
        dict(ids=[6851300], verdict='avoid', tier='comment', why='リブラなどの長期戦で重い'),
    ],
    '無頼漢': [
        dict(ids=[6850700], verdict='avoid', tier='body', why='回避の無敵が短く（25F）体が大きい'),
        dict(ids=[6851200], verdict='avoid', tier='comment', why='被弾しながら殴るので常に発動しやすい'),
        dict(ids=[6820400, 6820500], verdict='avoid', tier='comment', why='発症するとスキル受けのカットが剥がれる'),
    ],
    '復讐者': [
        dict(ids=[6840100, 6850300], verdict='avoid', tier='body', why='HP最大時の付帯が戻るまでが長くなる'),
        dict(ids=[6820400], verdict='avoid', tier='body', why='狂い火の祈祷を使いにくくなる'),
        dict(ids=[6820600], verdict='avoid', tier='body', why='夜の王戦でアーツの回転が落ちる'),
        dict(ids=[6850200], verdict='avoid', tier='body', why='狂い火のタメ2回で発狂するようになる'),
        dict(ids=[6850800], verdict='avoid', tier='body', why='ローリングが主な守り'),
        dict(ids=[6840000], verdict='avoid', tier='body', why='星光の欠片などを買いたい'),
        dict(ids=[6851700], verdict='avoid', tier='body', why='一撃死の線を簡単に下回る'),
        dict(ids=[6850500], verdict='avoid', tier='body', why='HP最大時の付帯が生命線'),
    ],
    '隠者': [
        dict(ids=[6840200], verdict='avoid', tier='body', why='アーツの高回転が立ち回りの軸'),
        dict(ids=[6850500], verdict='avoid', tier='body', why='HP最大時の付帯が剥がれる'),
    ],
    '執行者': [
        dict(ids=[6830400], verdict='avoid', tier='comment', why='神秘で状態異常を伸ばし、HPも高くない'),
    ],
    '葬儀屋': [
        dict(ids=[6830400], verdict='avoid', tier='body', why='もともと耐久がぎりぎり'),
        dict(ids=[6820400], verdict='avoid', tier='comment', why='長く止まり、トランスでの押し切りが効かない'),
    ],
}

# そのキャラでは仕組み上はたらかない効果（本文の記述）。ビルド提案はこのキャラでは使わない
USELESS = {
    '隠者': [
        dict(ids=[7122700, 7122800, 7122900, 7123000, 7123100, 7123200, 7123300, 7123400, 7123500, 7123600, 7123700,
                  7123800, 7123900, 7124000, 7124100, 7124300, 7124400, 7124500, 7124600, 7124700],
             why='出撃時の武器が杖なので戦技を付けられない'),
        dict(ids=[10000, 7036000], why='魔術では発動しない'),
    ],
}

# オーナーが確認した事実で、調査（character_research.json、神攻略wiki）の値を上書きするもの。
# キャラ図鑑と付録 catalog/characters.md に使う。stats は基本データの項目名、traits は特性の項目名で指定する
OWNER_NOTES = {
    'レディ': {
        'stats': {
            '回避': 'ステップ（2段まで）。1段目のみ: 無敵 27F／2段目も入力: 1段目から無敵が続き、入力の時機により合計 43〜50F'
                    '（全体Fは未確認）［オーナーの確認］',
        },
        'traits': {
            '回避（ステップ）': '硬直がかなり短いステップで、2段目までの回避モーションがある（アビリティ「華麗な身ごなし」）。'
                             '1段目のみなら無敵 27F。2段目も入力すると、1段目から無敵を保ったまま2段目のモーションになり、'
                             '入力の時機により合計 43〜50F の無敵（全体Fは未確認）［オーナーの確認。Wiki の計測は単発 全体28F・'
                             '無敵27F、連続 全体59F・無敵43F］。2段目を敵から離れる方向に入れると側転・バク転になるが、無敵は同じ（Wiki）',
        },
    },
}


def apply_owner_notes(research):
    """Overwrite research values with OWNER_NOTES (in place); returns the research dict"""
    for ch, notes in OWNER_NOTES.items():
        c = research['characters'][ch]
        c['stats'].update(notes.get('stats', {}))
        for t in c['traits']:
            if t['what'] in notes.get('traits', {}):
                t['value'] = notes['traits'][t['what']]
        missing = set(notes.get('traits', {})) - {t['what'] for t in c['traits']}
        if missing:
            raise KeyError(f'OWNER_NOTES {ch}: unknown traits {sorted(missing)}')
    return research
