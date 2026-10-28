"""照合結果のレビューページ（単一 HTML）"""

import html
import json

_TEMPLATE = r'''<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><title>効果データ照合レビュー</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#1a1a1a;--bg2:#242424;--bg3:#2d2d2d;--tx:#e0e0e0;--tx2:#a0a0a0;--mu:#707070;--ac:#4cc9b0;--wa:#f0a830;--ng:#e07070;--bd:#3a3a3a}
body{margin:0;background:var(--bg);color:var(--tx);font:13px/1.5 'Segoe UI',Meiryo,sans-serif}
header{padding:16px 20px;border-bottom:1px solid var(--bd)}h1{margin:0 0 6px;font-size:18px;color:var(--ac)}
.sum{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}.tile{background:var(--bg2);border:1px solid var(--bd);border-radius:6px;padding:6px 12px}
.tile b{font-size:16px;display:block}.bar{display:flex;gap:10px;flex-wrap:wrap;padding:10px 20px;background:var(--bg2);position:sticky;top:0;z-index:2;border-bottom:1px solid var(--bd)}
select,input{background:var(--bg3);color:var(--tx);border:1px solid var(--bd);border-radius:4px;padding:4px 8px}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid var(--bd);padding:6px 8px;vertical-align:top;text-align:left}
th{background:var(--bg3);position:sticky;top:46px;font-weight:600;color:var(--tx2)}
.id{color:var(--mu);font-size:11px}.w{color:var(--tx2);font-size:11px}.chg{color:var(--wa);font-weight:600}.old{color:var(--mu);text-decoration:line-through}
.tag{display:inline-block;font-size:10px;padding:0 5px;border-radius:3px;margin:1px 2px 1px 0;background:var(--bg3);color:var(--tx2)}
.tag.s{background:rgba(240,168,48,.18);color:var(--wa)}.tag.r{background:rgba(224,112,112,.18);color:var(--ng)}
.st{white-space:nowrap}.wrap{max-width:420px}section{padding:10px 20px}
</style></head><body>
<header><h1>効果データ照合レビュー（攻略 Wiki「遺物効果」__UPDATED__ 更新版との比較）</h1>
<div class="w">対象: 遺物に付く効果。「セーブ出現」= 照合に使ったセーブファイルに実際に出現した効果。提案値は Wiki の「重ね掛け」「備考」から作成。</div>
<div class="sum" id="sum"></div></header>
<div class="bar">
<label>表示: <select id="fStatus"><option value="">すべて</option><option value="重複変更">重複が変わる</option><option value="要約変更">要約が変わる</option><option value="全文変更">全文が変わる</option><option value="公開状況変更">公開状況が変わる</option><option value="unreleased">未公開</option><option value="変更なし">変更なし</option><option value="flag">要確認の印あり</option></select></label>
<label>出現: <select id="fSeen"><option value="seen">セーブに出現した効果のみ</option><option value="">すべて</option><option value="unseen">出現しない効果のみ</option></select></label>
<input id="q" placeholder="効果名で絞り込み" size="24"><span class="w" id="cnt"></span></div>
<table><thead><tr><th>効果</th><th class="st">重複（現在→提案）</th><th>要約（現在 → 提案）</th><th>全文（詳細パネル用）</th><th>Wiki の対応行</th><th>メモ</th></tr></thead><tbody id="tb"></tbody></table>
<section><h3>Wiki にあるが、どの効果にも対応しなかった行</h3><div id="wo" class="w"></div></section>
<script>
const D=__DATA__;
const sym=v=>v===true?'○':v===false?'×':v==='conditional'?'△':String(v);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function summary(){const seen=D.items.filter(x=>x.seen);const c=(a,f)=>a.filter(f).length;
 document.getElementById('sum').innerHTML=[['対象の効果（同名は1行）',D.items.length],['セーブに出現',seen.length],['うち重複が変わる',c(seen,x=>x.status.includes('重複変更'))],['うち要約が変わる',c(seen,x=>x.status.includes('要約変更'))],['うち要確認の印',c(seen,x=>x.flags.length)],['Wikiに無い（出現なし）',c(D.items,x=>!x.seen&&x.flags.includes('Wikiに無し'))],['未公開',c(D.items,x=>x.unreleased)]].map(([k,v])=>`<div class="tile"><b>${v}</b>${k}</div>`).join('');}
function render(){const fs=fStatus.value,fe=fSeen.value,q=document.getElementById('q').value.trim();
 const rows=D.items.filter(x=>(!fe||(fe==='seen')===x.seen)&&(!fs||(fs==='flag'?x.flags.length:fs==='unreleased'?x.unreleased:x.status.includes(fs)))&&(!q||x.name_ja.includes(q)));
 cnt.textContent=rows.length+' 件';
 tb.innerHTML=rows.map(x=>{const sc=x.status.includes('重複変更'),nc=x.status.includes('要約変更');
  return `<tr><td>${esc(x.name_ja)}<div class="id">ID ${x.ids.join(', ')} ${x.deep_id?'深層':'通常'}${x.seen?' / セーブ出現':''}${x.ids.length>1?' / 同名の効果が'+x.ids.length+'つ（固有遺物用など）':''}</div></td>
  <td class="st">${sc?`<span class="old">${sym(x.cur_stack)}</span> → <span class="chg">${sym(x.prop_stack)}</span>`:sym(x.cur_stack)}</td>
  <td class="wrap">${nc?`<div class="old">${esc(x.cur_notes)||'（空）'}</div><div class="chg">${esc(x.prop_short)||'（空）'}</div>`:esc(x.cur_notes)}<div class="id">${esc(x.short_src)}</div></td>
  <td class="wrap w">${esc(x.prop_notes).split(' / ').join('<br>')}</td>
  <td class="w">${x.w_name?`${esc(x.w_section)}<br>${esc(x.w_name)}<br>重ね掛け: ${esc(x.w_stack)}`:(x.how==='section-rule'?'節の説明（左優先）':'—')}${x.suggestion?`<br>候補: ${esc(x.suggestion)}`:''}</td>
  <td>${x.flags.map(f=>`<span class="tag ${f.includes('無し')?'r':'s'}">${esc(f)}</span>`).join('')}<span class="tag">${esc(x.how)}</span></td></tr>`}).join('');}
summary();render();[fStatus,fSeen].forEach(e=>e.onchange=render);document.getElementById('q').oninput=render;
wo.innerHTML=D.wiki_only.map(r=>`${r.deep?'深層':'通常'} / ${esc(r.section)}: ${esc(r.name)}（${esc(r.stack)}）`).join('<br>')||'なし';
</script></body></html>'''


def group_same_name(items):
    """Effects with the same name and identical values (e.g. unique-relic copies) -> one row."""
    groups = {}
    for x in items:
        k = (x['name_ja'], x['seen'], str(x['cur_stack']), x['cur_notes'], str(x['prop_stack']), x['prop_short'], x['prop_notes'])
        if k in groups:
            groups[k]['ids'].append(x['id'])
        else:
            groups[k] = {**x, 'ids': [x['id']]}
    return list(groups.values())


def write(path, items, wiki_only, updated):
    data = json.dumps({'items': group_same_name(items), 'wiki_only': wiki_only}, ensure_ascii=False).replace('</', '<\\/')
    page = _TEMPLATE.replace('__UPDATED__', html.escape(updated or '?')).replace('__DATA__', data)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(page)
