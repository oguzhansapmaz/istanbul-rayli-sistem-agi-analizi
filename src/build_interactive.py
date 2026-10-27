from __future__ import annotations
import json
from pathlib import Path
from .common import ROOT, OUTPUT_DIR

TEMPLATE = r'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>İstanbul Raylı Sistem Ağı | Etkileşimli</title>
<style>
:root{--ink:#152238;--muted:#536276;--bg:#f5f7fa;--line:#d8dee8;--accent:#176b87}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:Segoe UI,Arial,sans-serif;color:var(--ink)}
header{padding:16px 22px;background:#fff;border-bottom:1px solid var(--line)}h1{font-size:22px;margin:0 0 5px}header p{margin:0;color:var(--muted);font-size:13px}
main{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:12px;padding:12px;height:calc(100vh - 77px)}
#network{background:white;border:1px solid var(--line);border-radius:10px;min-height:500px}
aside{background:white;border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto}label{display:block;font-size:12px;font-weight:600;margin:12px 0 5px}input,select,button{width:100%;padding:9px;border:1px solid #cbd5e1;border-radius:7px;background:white;font:inherit}button{margin-top:8px;background:var(--accent);color:white;border:0;cursor:pointer}.kv{font-size:13px;margin:9px 0;line-height:1.4}.kv b{display:block;color:var(--muted);font-size:11px;text-transform:uppercase}.notice{margin-top:16px;border-top:1px solid var(--line);padding-top:12px;color:#7f3131;font-size:12px;line-height:1.4}
@media(max-width:850px){main{grid-template-columns:1fr;height:auto}#network{height:68vh}aside{min-height:240px}}
</style><script src="https://unpkg.com/cytoscape@3.30.2/dist/cytoscape.min.js"></script></head>
<body><header><h1>İstanbul Raylı Sistem Yolcu Ağı</h1><p>2025 İBB istasyon verisi + hat sırası kaynakları docs/topology_validation.csv içinde</p></header>
<main><div id="network"></div><aside>
<label for="search">İstasyon ara</label><input id="search" placeholder="Örn. Sirkeci, Yenikapı">
<button id="searchBtn">İstasyona git</button>
<label for="community">Louvain topluluğu</label><select id="community"><option value="all">Tüm topluluklar</option></select>
<div id="details"><h2 style="font-size:18px">Bir düğüme tıkla</h2><p style="color:#536276;font-size:13px">İstasyon bilgileri burada açılacak.</p></div>
<div class="notice"><b>Önemli metodolojik not:</b> Kenar ağırlığı, iki uç istasyonun ortalama günlük yolcu aktivitesinden türetilen bir vekil ölçüdür; gerçek istasyonlar arası yolcu akışı değildir. Sıralar numeric işlenir; docs/topology_validation.csv içinde kaynak ve kalan alias/aktarma kontrolleri listelenir. Bu ağ, kaynakta OD matrisi olmadığı için gerçek istasyonlar arası yolculuk akışını göstermez.</div>
</aside></main>
<script>
const elements = __GRAPH_DATA__;
const cy = cytoscape({container:document.getElementById('network'),elements:elements,layout:{name:'cose',animate:false,fit:true,padding:30,idealEdgeLength:70,nodeRepulsion:4500,gravity:0.18},
style:[
{selector:'node',style:{'label':'data(label)','font-size':8,'text-wrap':'wrap','text-max-width':100,'background-color':'mapData(community,0,25,#2a9d8f,#e76f51)','width':'mapData(degree,0,8,7,22)','height':'mapData(degree,0,8,7,22)','border-width':1,'border-color':'#ffffff','color':'#263238','text-valign':'bottom','text-margin-y':3}},
{selector:'edge',style:{'width':'mapData(strength,1,30000,0.5,3.5)','line-color':'#99a6b6','opacity':0.55,'curve-style':'bezier'}},
{selector:'.faded',style:{'opacity':0.08,'text-opacity':0.06}},
{selector:'.searched',style:{'border-width':4,'border-color':'#ffb703','background-color':'#fb8500'}}]});
const communities=[...new Set(elements.nodes.map(n=>String(n.data.community)))].sort((a,b)=>Number(a)-Number(b));
const communitySelect=document.getElementById('community'); communities.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent='Topluluk '+c;communitySelect.appendChild(o)});
function showDetails(n){const d=n.data();document.getElementById('details').innerHTML=`<h2 style="font-size:18px">${d.label}</h2><div class="kv"><b>Hat(lar)</b>${d.lines||'Belirtilmemiş'}</div><div class="kv"><b>Ortalama günlük yolcu kaydı</b>${d.has_passenger_data?Math.round(d.passenger_mean_daily).toLocaleString('tr-TR'):'Bu düğüme eşleşen yolcu verisi yok'}</div><div class="kv"><b>Derece</b>${d.degree}</div><div class="kv"><b>Betweenness</b>${Number(d.betweenness).toFixed(5)}</div><div class="kv"><b>Louvain topluluğu</b>${d.community}</div>`}
cy.on('tap','node',evt=>showDetails(evt.target));
communitySelect.addEventListener('change',()=>{const c=communitySelect.value;cy.nodes().forEach(n=>{const yes=c==='all'||String(n.data('community'))===c;n.toggleClass('faded',!yes)});cy.edges().forEach(e=>{const yes=c==='all'||String(e.source().data('community'))===c||String(e.target().data('community'))===c;e.toggleClass('faded',!yes)})});
function search(){const q=document.getElementById('search').value.trim().toLocaleLowerCase('tr-TR');cy.nodes().removeClass('searched');if(!q)return;const matches=cy.nodes().filter(n=>n.data('label').toLocaleLowerCase('tr-TR').includes(q));if(matches.length){matches.addClass('searched');cy.fit(matches,100);showDetails(matches[0])}}
document.getElementById('searchBtn').addEventListener('click',search);document.getElementById('search').addEventListener('keydown',e=>{if(e.key==='Enter')search()});
</script></body></html>'''

def main():
    elements_path=ROOT/'web'/'graph_elements.json'
    if not elements_path.exists(): raise FileNotFoundError('Önce analiz çalışmalı: python -m src.analyze_network')
    data=json.loads(elements_path.read_text(encoding='utf-8'))
    html=TEMPLATE.replace('__GRAPH_DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')))
    target=ROOT/'web'/'interactive_network.html'
    target.write_text(html,encoding='utf-8')
    print('Interactive network created:',target)

if __name__=='__main__': main()
