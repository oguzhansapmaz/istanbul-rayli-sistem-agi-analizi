from __future__ import annotations
import json, math
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from .common import ROOT, OUTPUT_DIR, ensure_dirs


def main():
    ensure_dirs()
    G=nx.read_graphml(OUTPUT_DIR/'istanbul_rail_2025.graphml')
    G=nx.Graph(G)
    measures=pd.read_csv(OUTPUT_DIR/'centrality_and_communities.csv')
    summary=json.loads((OUTPUT_DIR/'analysis_summary.json').read_text(encoding='utf-8'))
    plots=OUTPUT_DIR/'plots'; plots.mkdir(parents=True,exist_ok=True)
    communities=measures.set_index('node_key')['louvain_community'].to_dict()
    bet=measures.set_index('node_key')['betweenness_unweighted'].to_dict()
    degree=measures.set_index('node_key')['degree'].to_dict()
    labels={n:G.nodes[n].get('label',G.nodes[n].get('station_name',str(n))) for n in G.nodes}
    pos=nx.spring_layout(G,seed=42,k=0.28,iterations=180,weight=None)
    uniq=sorted(set(communities.values()))
    palette=plt.get_cmap('tab20')
    color_map={c:palette(i%20) for i,c in enumerate(uniq)}
    ncolors=[color_map.get(communities.get(n,-1),(0.5,0.5,0.5,1)) for n in G.nodes]
    nsizes=[22+34*math.log1p(max(degree.get(n,0),0)) for n in G.nodes]
    edge_strength=[float(G[u][v].get('strength',1) or 1) for u,v in G.edges]
    widths=[0.25+0.45*(math.log1p(w)/max(math.log1p(max(edge_strength,default=1)),1)) for w in edge_strength]

    # A3 poster (landscape); dense station labels are limited to highly central nodes for readability.
    fig=plt.figure(figsize=(16.54,11.69),facecolor='white')
    ax=fig.add_axes([0.03,0.09,0.64,0.84]); ax.axis('off')
    nx.draw_networkx_edges(G,pos,ax=ax,width=widths,alpha=0.35,edge_color='#7B8794')
    nx.draw_networkx_nodes(G,pos,ax=ax,node_size=nsizes,node_color=ncolors,linewidths=0.25,edgecolors='white',alpha=0.92)
    top_nodes=measures.sort_values('betweenness_unweighted',ascending=False).head(22)['node_key'].tolist()
    nx.draw_networkx_labels(G,pos,labels={n:labels[n] for n in top_nodes},font_size=5.8,font_family='DejaVu Sans',ax=ax)
    fig.text(0.04,0.955,'İSTANBUL RAYLI SİSTEM YOLCU AĞI',fontsize=23,fontweight='bold',color='#152238')
    fig.text(0.04,0.925,'2025 istasyon bazlı yolcu kayıtları + resmi ağ haritasından elle aktarılan hat sıraları',fontsize=10,color='#536276')
    fig.text(0.72,0.86,'ÖN BULGULAR',fontsize=14,fontweight='bold',color='#152238')
    g=summary['graph']
    metrics=[('Düğüm',g['nodes']),('Kenar',g['edges']),('Bileşen',g['connected_components']),('En büyük bileşen',g['largest_component_nodes']),('Yoğunluk',f"{g['density']:.4f}"),('Ortalama yol (B.B.)',f"{g['average_shortest_path_largest_component']:.2f}"),('Çap (B.B.)',g['diameter_largest_component'])]
    yy=0.81
    for label,value in metrics:
        fig.text(0.72,yy,label,fontsize=9,color='#536276'); fig.text(0.93,yy,str(value),fontsize=10,fontweight='bold',ha='right',color='#152238'); yy-=0.045
    fig.text(0.72,yy-0.01,'YÖNTEM',fontsize=12,fontweight='bold',color='#152238'); yy-=0.055
    methods=['Düğüm: istasyon / fiziksel aktarma düğümü','Kenar: aynı hattaki ardışık istasyonlar','Ağırlık: uç istasyonların ort. günlük yolcu aktivitesi','Mesafe: 1 / kenar gücü','Current-flow: en büyük bağlı bileşende']
    for m in methods:
        fig.text(0.72,yy,'• '+m,fontsize=8,color='#344054'); yy-=0.035
    fig.text(0.72,yy-0.005,'SINIRLAR / TESLİM ÖNCESİ',fontsize=12,fontweight='bold',color='#9C2F2F'); yy-=0.055
    limitations=['Hat sırası sayısal olarak sıralanır; docs/topology_validation.csv içinde kaynak ve kontrol kapsamı belirtilir; listelenen manuel kontroller kapanmadan final değildir.','OD matrisi yok: kenar ağırlığı yolcu aktivitesi vekili; kapanma sonucu gerçek yolcu yönlenmesi değildir.','Grafikte gerçek istasyonlar temel alınır; 500 düğüm şartı karşılanmadığı için öğretim elemanıyla kapsam netleştirilmelidir.','Leiden / powerlaw durumu analysis_summary.json içinde kontrol edilmelidir; hesaplanmayan yöntem bulgu gibi sunulmamalıdır.']
    for m in limitations:
        fig.text(0.72,yy,'• '+m,fontsize=8,color='#7A2525'); yy-=0.047
    fig.text(0.04,0.035,'Kaynak: İBB Açık Veri Portalı (2025 istasyon verisi); Metro İstanbul resmi raylı sistemler ağı haritası. Bu poster doğrulama gerektiren taslaktır.',fontsize=8,color='#536276')
    fig.savefig(OUTPUT_DIR/'ag_posteri_A3_TASLAK.pdf')
    fig.savefig(plots/'network_overview.png',dpi=180,bbox_inches='tight')
    plt.close(fig)

    # Degree distribution chart (include zero-degree nodes only as a note; log-log chart uses positive degrees).
    deg=np.array([d for _,d in G.degree() if d>0])
    counts=np.bincount(deg)
    x=np.arange(1,len(counts)); y=counts[1:]
    mask=y>0
    fig,ax=plt.subplots(figsize=(7,5))
    ax.scatter(x[mask],y[mask],s=36)
    ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel('Derece (log)'); ax.set_ylabel('Düğüm sayısı (log)')
    ax.set_title('Derece dağılımı - log-log (pozitif dereceler)'); ax.grid(True,which='both',alpha=0.25)
    fig.tight_layout(); fig.savefig(plots/'degree_distribution_loglog.png',dpi=180); plt.close(fig)

    # Top 12 by unweighted betweenness.
    top=measures.sort_values('betweenness_unweighted',ascending=False).head(12).sort_values('betweenness_unweighted')
    fig,ax=plt.subplots(figsize=(9,6))
    ax.barh(top['label'],top['betweenness_unweighted'])
    ax.set_xlabel('Betweenness merkeziyeti'); ax.set_title('En yüksek betweenness değerine sahip istasyon düğümleri')
    ax.grid(axis='x',alpha=0.25); fig.tight_layout(); fig.savefig(plots/'top_betweenness.png',dpi=180); plt.close(fig)

    # Weighted vs unweighted comparison scatter.
    fig,ax=plt.subplots(figsize=(7,5))
    ax.scatter(measures['betweenness_unweighted'],measures['betweenness_weighted'],s=18,alpha=0.65)
    ax.set_xlabel('Ağırlıksız betweenness'); ax.set_ylabel('Ağırlıklı betweenness (1/güç mesafesi)')
    ax.set_title('Topolojik ve yolcu-aktivitesi ağırlıklı merkeziyet karşılaştırması')
    ax.grid(True,alpha=0.25); fig.tight_layout(); fig.savefig(plots/'weighted_unweighted_betweenness.png',dpi=180); plt.close(fig)

    # Null model comparison if present.
    null_path=OUTPUT_DIR/'null_model_results.csv'
    if null_path.exists():
        df=pd.read_csv(null_path)
        for metric,title,outfile in [
            ('average_clustering_lcc','Gözlenen / null model: kümelenme','null_clustering.png'),
            ('average_shortest_path_lcc','Gözlenen / null model: ortalama yol','null_path_length.png'),
            ('modularity_unweighted_lcc','Gözlenen / null model: ağırlıksız modülerlik','null_modularity.png')]:
            fig,ax=plt.subplots(figsize=(7,4.5))
            ax.hist(pd.to_numeric(df[metric],errors='coerce').dropna(),bins=18,alpha=0.75)
            ax.set_title(title+' (null dağılımı)'); ax.set_xlabel(metric); ax.set_ylabel('Tekrar sayısı'); ax.grid(axis='y',alpha=0.2)
            fig.tight_layout(); fig.savefig(plots/outfile,dpi=160); plt.close(fig)
    print('Visuals created in',OUTPUT_DIR)

if __name__=='__main__': main()
