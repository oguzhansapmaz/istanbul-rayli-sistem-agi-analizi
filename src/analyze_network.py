from __future__ import annotations
import argparse, json, math, time, warnings, hashlib
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
from .common import ROOT, OUTPUT_DIR, ensure_dirs, write_json


def safe_float(x):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)): return None
        return float(x)
    except Exception:
        return None

def _contingency(labels_true, labels_pred):
    """Build a contingency matrix using NumPy only (no SciPy/scikit-learn)."""
    y_true = np.asarray(labels_true)
    y_pred = np.asarray(labels_pred)
    if y_true.shape[0] != y_pred.shape[0]:
        raise ValueError('Label arrays must have the same length.')
    if y_true.size == 0:
        return np.zeros((0, 0), dtype=np.int64)
    _, true_inv = np.unique(y_true, return_inverse=True)
    _, pred_inv = np.unique(y_pred, return_inverse=True)
    table = np.zeros((true_inv.max() + 1, pred_inv.max() + 1), dtype=np.int64)
    np.add.at(table, (true_inv, pred_inv), 1)
    return table


def adjusted_rand_score(labels_true, labels_pred):
    """Adjusted Rand index, implemented without scikit-learn."""
    table = _contingency(labels_true, labels_pred)
    n = int(table.sum())
    if n <= 1:
        return 1.0
    comb2 = lambda values: np.asarray(values, dtype=float) * (np.asarray(values, dtype=float) - 1.0) / 2.0
    sum_cells = float(comb2(table).sum())
    sum_rows = float(comb2(table.sum(axis=1)).sum())
    sum_cols = float(comb2(table.sum(axis=0)).sum())
    total = float(n * (n - 1) / 2.0)
    expected = sum_rows * sum_cols / total
    maximum = 0.5 * (sum_rows + sum_cols)
    denominator = maximum - expected
    if abs(denominator) < 1e-15:
        return 1.0
    return float((sum_cells - expected) / denominator)


def normalized_mutual_info_score(labels_true, labels_pred):
    """Arithmetic-normalized mutual information, matching sklearn's default."""
    table = _contingency(labels_true, labels_pred).astype(float)
    n = float(table.sum())
    if n == 0:
        return 1.0
    row = table.sum(axis=1)
    col = table.sum(axis=0)
    def entropy(counts):
        probs = counts[counts > 0] / n
        return float(-np.sum(probs * np.log(probs)))
    h_true = entropy(row)
    h_pred = entropy(col)
    denom = (h_true + h_pred) / 2.0
    if denom == 0:
        return 1.0
    mi = 0.0
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            nij = table[i, j]
            if nij > 0:
                mi += (nij / n) * math.log((nij * n) / (row[i] * col[j]))
    return float(mi / denom)

def safe_communities(G, seed=42, weight='strength'):
    if G.number_of_nodes() == 0:
        return []
    try:
        return nx.community.louvain_communities(G, weight=weight, seed=seed)
    except Exception:
        return list(nx.community.greedy_modularity_communities(G, weight=weight))

def comm_labels(G, communities):
    labels={}
    for i, community in enumerate(communities):
        for node in community: labels[node]=i
    return labels

def get_partition_metrics(G, communities, weight='strength'):
    try: q=nx.community.modularity(G, communities, weight=weight)
    except Exception: q=float('nan')
    return {'community_count':len(communities),'modularity':safe_float(q),'sizes':sorted([len(c) for c in communities],reverse=True)}

def main():
    parser=argparse.ArgumentParser(description='Compute network-analysis metrics for the Istanbul railway graph.')
    parser.add_argument('--null-models',type=int,default=100,help='Number of degree-preserving null networks (default 100).')
    parser.add_argument('--stability-seeds',type=int,default=10,help='Random seeds for Louvain stability (default 10).')
    parser.add_argument('--skip-null',action='store_true',help='Skip null model during quick development.')
    parser.add_argument('--skip-powerlaw',action='store_true',help='Skip optional powerlaw fit.')
    args=parser.parse_args()
    ensure_dirs()
    graph_path=OUTPUT_DIR/'istanbul_rail_2025.graphml'
    if not graph_path.exists(): raise FileNotFoundError('Önce python -m src.build_network çalıştırın.')
    G=nx.read_graphml(graph_path)
    # Keep only simple graph characteristics; edge weights have a clearly documented proxy interpretation.
    G=nx.Graph(G)
    if G.number_of_nodes()==0: raise ValueError('Ağ boş.')

    comps=sorted(nx.connected_components(G), key=len, reverse=True)
    largest=G.subgraph(comps[0]).copy()
    degrees=dict(G.degree())
    deg_c=nx.degree_centrality(G)
    bet_unw=nx.betweenness_centrality(G, normalized=True, weight=None)
    bet_w=nx.betweenness_centrality(G, normalized=True, weight='distance')
    close_unw=nx.closeness_centrality(G, distance=None)
    close_w=nx.closeness_centrality(G, distance='distance')
    try: page=nx.pagerank(G,weight='strength')
    except Exception: page={n:0.0 for n in G.nodes}
    eig={n:0.0 for n in G.nodes}
    try:
        el=nx.eigenvector_centrality(largest,weight='strength',max_iter=5000,tol=1e-8)
        eig.update(el)
    except Exception:
        try:
            el=nx.eigenvector_centrality_numpy(largest,weight='strength'); eig.update(el)
        except Exception: pass

    # Current-flow betweenness requires a connected undirected graph. Calculate on largest component and label the scope.
    cf={n:0.0 for n in G.nodes}
    cf_status='calculated on largest connected component only'
    try:
        if largest.number_of_nodes() >= 3:
            cf.update(nx.current_flow_betweenness_centrality(largest,normalized=True,weight=None,solver='full'))
        else: cf_status='not calculated: largest connected component has fewer than 3 nodes'
    except Exception as exc:
        cf_status=f'not calculated: {type(exc).__name__}: {exc}'

    strengths={n:float(G.degree(n,weight='strength')) for n in G.nodes}
    measures=pd.DataFrame({
        'node_key':list(G.nodes),
        'label':[G.nodes[n].get('label',G.nodes[n].get('station_name',n)) for n in G.nodes],
        'lines':[G.nodes[n].get('lines','') for n in G.nodes],
        'has_passenger_data':[bool(G.nodes[n].get('has_passenger_data',False)) for n in G.nodes],
        'passenger_mean_daily':[float(G.nodes[n].get('passenger_mean_daily',0) or 0) for n in G.nodes],
        'degree':[degrees[n] for n in G.nodes], 'degree_centrality':[deg_c[n] for n in G.nodes],
        'weighted_degree_strength':[strengths[n] for n in G.nodes], 'betweenness_unweighted':[bet_unw[n] for n in G.nodes],
        'betweenness_weighted':[bet_w[n] for n in G.nodes], 'closeness_unweighted':[close_unw[n] for n in G.nodes],
        'closeness_weighted':[close_w[n] for n in G.nodes], 'eigenvector_lcc':[eig[n] for n in G.nodes],
        'pagerank_strength':[page[n] for n in G.nodes], 'current_flow_betweenness_lcc':[cf[n] for n in G.nodes]
    })
    louvain = safe_communities(G,seed=42,weight='strength')
    louvain_labels=comm_labels(G,louvain)
    measures['louvain_community']=[louvain_labels.get(n,-1) for n in measures['node_key']]
    q_louvain=get_partition_metrics(G,louvain,weight='strength')
    # Louvain stability across distinct random seeds, compared with seed 42 by ARI and NMI.
    stability_rows=[]
    base_order=list(G.nodes)
    base_labels=np.array([louvain_labels.get(n,-1) for n in base_order])
    for seed in range(100, 100 + max(args.stability_seeds, 1)):
        communities_seed=safe_communities(G,seed=seed,weight='strength')
        labels_seed=comm_labels(G,communities_seed)
        vec=np.array([labels_seed.get(n,-1) for n in base_order])
        stability_rows.append({'seed':seed,'community_count':len(communities_seed),
            'modularity':get_partition_metrics(G,communities_seed,weight='strength')['modularity'],
            'ARI_vs_seed42':float(adjusted_rand_score(base_labels,vec)),
            'NMI_vs_seed42':float(normalized_mutual_info_score(base_labels,vec))})
    pd.DataFrame(stability_rows).to_csv(OUTPUT_DIR/'community_stability_louvain.csv',index=False,encoding='utf-8-sig')
    louvain_stability={'n_seeds':len(stability_rows),'mean_ARI_vs_seed42':safe_float(pd.DataFrame(stability_rows)['ARI_vs_seed42'].mean()),
        'min_ARI_vs_seed42':safe_float(pd.DataFrame(stability_rows)['ARI_vs_seed42'].min()),
        'mean_NMI_vs_seed42':safe_float(pd.DataFrame(stability_rows)['NMI_vs_seed42'].mean()),
        'seed42_baseline':'Louvain, random seed 42'}

    # Leiden is required by the assignment. If the dependency is absent, say so rather than fabricate a result.
    leiden_status='not installed; install igraph and leidenalg to compute this required comparison'
    leiden_communities=[]; leiden_q=None; leiden_stability={'status':'not calculated'}
    try:
        import igraph as ig
        import leidenalg
        node_order=list(G.nodes); idx={n:i for i,n in enumerate(node_order)}
        ig_edges=[(idx[u],idx[v]) for u,v in G.edges]
        igg=ig.Graph(n=len(node_order),edges=ig_edges,directed=False)
        igg.vs['name']=node_order
        weights=[float(G[u][v].get('strength',1)) for u,v in G.edges]
        part=leidenalg.find_partition(igg,leidenalg.RBConfigurationVertexPartition,weights=weights,seed=42)
        leiden_communities=[{node_order[i] for i in community} for community in part]
        leiden_q=get_partition_metrics(G,leiden_communities,weight='strength')
        leiden_base_labels=np.array([comm_labels(G,leiden_communities).get(n,-1) for n in node_order])
        leiden_stability_rows=[]
        for seed in range(100, 100 + max(args.stability_seeds, 1)):
            part_seed=leidenalg.find_partition(igg,leidenalg.RBConfigurationVertexPartition,weights=weights,seed=seed)
            communities_seed=[{node_order[i] for i in community} for community in part_seed]
            labels_seed=comm_labels(G,communities_seed)
            vec=np.array([labels_seed.get(n,-1) for n in node_order])
            leiden_stability_rows.append({'seed':seed,'community_count':len(communities_seed),
                'modularity':get_partition_metrics(G,communities_seed,weight='strength')['modularity'],
                'ARI_vs_seed42':float(adjusted_rand_score(leiden_base_labels,vec)),
                'NMI_vs_seed42':float(normalized_mutual_info_score(leiden_base_labels,vec))})
        pd.DataFrame(leiden_stability_rows).to_csv(OUTPUT_DIR/'community_stability_leiden.csv',index=False,encoding='utf-8-sig')
        leiden_stability={'status':'calculated','n_seeds':len(leiden_stability_rows),
            'mean_ARI_vs_seed42':safe_float(pd.DataFrame(leiden_stability_rows)['ARI_vs_seed42'].mean()),
            'min_ARI_vs_seed42':safe_float(pd.DataFrame(leiden_stability_rows)['ARI_vs_seed42'].min()),
            'mean_NMI_vs_seed42':safe_float(pd.DataFrame(leiden_stability_rows)['NMI_vs_seed42'].mean())}
        leiden_status='calculated with leidenalg RBConfigurationVertexPartition'
    except Exception as exc:
        leiden_status=f'not calculated: {type(exc).__name__}: {exc}'

    measures['leiden_community']=-1
    if leiden_communities:
        llabels=comm_labels(G,leiden_communities)
        measures['leiden_community']=[llabels.get(n,-1) for n in measures['node_key']]

    measures.to_csv(OUTPUT_DIR/'centrality_and_communities.csv',index=False,encoding='utf-8-sig')
    # Spearman correlations between centrality measures.
    corr_cols=['degree_centrality','weighted_degree_strength','betweenness_unweighted','betweenness_weighted','closeness_unweighted','closeness_weighted','eigenvector_lcc','pagerank_strength','current_flow_betweenness_lcc']
    corr={}
    # Spearman rho is the Pearson correlation of average ranks. This pandas-only
    # implementation avoids SciPy's compiled extension, which can be blocked by
    # some Windows application-control policies. Significance p-values are omitted.
    ranked = measures[corr_cols].rank(method='average')
    corr_matrix = ranked.corr(method='pearson')
    for i,a in enumerate(corr_cols):
        for b in corr_cols[i+1:]:
            r = corr_matrix.loc[a, b]
            corr[f'{a}__{b}']={'rho':safe_float(r),'p_value':None,
                'method_note':'Spearman rho computed from average ranks; p-value omitted to avoid SciPy dependency.'}

    corr_rows=[]
    for pair, value in corr.items():
        a,b=pair.split('__',1)
        corr_rows.append({'measure_a':a,'measure_b':b,'spearman_rho':value.get('rho'),'p_value':value.get('p_value'),'method_note':value.get('method_note','')})
    pd.DataFrame(corr_rows).sort_values('spearman_rho',key=lambda x:x.abs(),ascending=False).to_csv(OUTPUT_DIR/'centrality_spearman_correlations.csv',index=False,encoding='utf-8-sig')

    try: assort=safe_float(nx.degree_assortativity_coefficient(G))
    except Exception: assort=None
    try: clustering=safe_float(nx.average_clustering(G))
    except Exception: clustering=None
    try: transitivity=safe_float(nx.transitivity(G))
    except Exception: transitivity=None
    try: avg_path_lcc=safe_float(nx.average_shortest_path_length(largest)) if largest.number_of_nodes()>1 else None
    except Exception: avg_path_lcc=None
    try: diameter_lcc=int(nx.diameter(largest)) if largest.number_of_nodes()>1 else None
    except Exception: diameter_lcc=None
    # Weighted centrality rankings and top-three community summaries.
    top_columns=['degree','betweenness_unweighted','betweenness_weighted','current_flow_betweenness_lcc','pagerank_strength','passenger_mean_daily']
    top={}
    for col in top_columns:
        top[col]=measures.sort_values(col,ascending=False).head(10)[['node_key','label','lines',col]].to_dict('records')
    community_detail=[]
    # Keep the true Louvain ID while ordering profiles by size, so the report and interactive filter agree.
    for rank,(raw_id,community) in enumerate(sorted(enumerate(louvain),key=lambda item:len(item[1]),reverse=True),1):
        sub=measures[measures.node_key.isin(community)]
        top_stations=sub.sort_values('passenger_mean_daily',ascending=False).head(5)['label'].tolist()
        top_betweenness=sub.sort_values('betweenness_unweighted',ascending=False).head(3)['label'].tolist()
        line_counts=Counter()
        for node in community:
            for line in str(G.nodes[node].get('lines','')).split(','):
                line=line.strip()
                if line: line_counts[line]+=1
        dominant_lines=[line for line,_ in line_counts.most_common(3)]
        line_set=set(dominant_lines)
        if {'M7','T4'}.issubset(line_set):
            candidate_name='Kuzeybatı metro-tramvay koridoru (M7–T4)'
        elif {'M1','M3'}.issubset(line_set):
            candidate_name='Batı raylı sistem aktarma koridoru (M1–M3)'
        elif {'T1','MAR'}.issubset(line_set) or {'T1','SIRKECI'}.issubset(line_set):
            candidate_name='Merkez ve tarihî yarımada aktarma koridoru (T1–Marmaray)'
        elif {'M4','M8'}.issubset(line_set) or {'M4','MAR'}.issubset(line_set):
            candidate_name='Anadolu yakası metro–Marmaray koridoru (M4/M8)'
        elif {'M2','M6'}.issubset(line_set) or {'M2','M11'}.issubset(line_set):
            candidate_name='Kuzey-merkez metro omurgası (M2/M6/M11)'
        elif {'M1','T1'}.issubset(line_set):
            candidate_name='M1–T1 merkez-batı aktarma çevresi'
        else:
            candidate_name=' / '.join(dominant_lines[:2])+' ağırlıklı istasyon topluluğu' if dominant_lines else 'Etiketi gözden geçirilecek istasyon topluluğu'
        community_detail.append({'community':int(raw_id),'rank_by_size':rank,'size':len(community),
            'candidate_name':candidate_name,'dominant_lines':dominant_lines,
            'top_passenger_stations':top_stations,'top_betweenness_stations':top_betweenness,
            'name_note':'Hat üyeliklerinden türetilmiş önerilen isim; öğrenci bağlamla kontrol edip sunumda kendi cümlesiyle açıklamalıdır.'})
    pd.DataFrame(community_detail).to_csv(OUTPUT_DIR/'community_profile.csv',index=False,encoding='utf-8-sig')

    # Degree distribution: fit power-law and compare with alternatives when installed.
    powerlaw_result={'status':'not run'}
    degrees_positive=[int(d) for _,d in G.degree() if d>0]
    if not args.skip_powerlaw:
        try:
            import powerlaw
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                fit=powerlaw.Fit(degrees_positive,discrete=True,verbose=False)
                p_ex=fit.distribution_compare('power_law','exponential')
                p_ln=fit.distribution_compare('power_law','lognormal')
                powerlaw_result={'status':'calculated','n_positive_degree':len(degrees_positive),'alpha':safe_float(fit.power_law.alpha),'xmin':safe_float(fit.power_law.xmin),
                    'power_law_vs_exponential':{'R':safe_float(p_ex[0]),'p_value':safe_float(p_ex[1])},
                    'power_law_vs_lognormal':{'R':safe_float(p_ln[0]),'p_value':safe_float(p_ln[1])},
                    'interpretation_note':'A non-significant p-value or small fit range does not establish a power law; report sample size and comparison result.'}
        except Exception as exc:
            powerlaw_result={'status':'not calculated','reason':f'{type(exc).__name__}: {exc}','install_hint':'pip install powerlaw'}

    # Closure simulation: top betweenness transfer candidate (degree >= 3 preferred); this is topological rerouting, not OD demand.
    candidates=measures[measures.degree>=3]
    if candidates.empty: candidates=measures
    if not candidates.empty:
        closure_node=str(candidates.sort_values('betweenness_unweighted',ascending=False).iloc[0]['node_key'])
        closure_label=str(candidates.sort_values('betweenness_unweighted',ascending=False).iloc[0]['label'])
        H=G.copy(); H.remove_node(closure_node)
        hcomps=sorted(nx.connected_components(H),key=len,reverse=True)
        hlcc=H.subgraph(hcomps[0]).copy() if hcomps else H
        path_after=safe_float(nx.average_shortest_path_length(hlcc)) if hlcc.number_of_nodes()>1 else None
        before_on_giant=safe_float(nx.average_shortest_path_length(largest)) if largest.number_of_nodes()>1 else None
        def connected_pair_fraction(graph):
            n=graph.number_of_nodes()
            total=n*(n-1)/2
            if total <= 0: return 1.0
            connected=sum(len(c)*(len(c)-1)/2 for c in nx.connected_components(graph))
            return float(connected/total)
        global_eff_before=safe_float(nx.global_efficiency(G))
        global_eff_after=safe_float(nx.global_efficiency(H))
        pair_fraction_before=connected_pair_fraction(G)
        pair_fraction_after=connected_pair_fraction(H)
        before_bet=nx.betweenness_centrality(G,normalized=True)
        after_bet=nx.betweenness_centrality(H,normalized=True)
        shifts=[]
        for n,val in after_bet.items():
            delta=float(val-before_bet.get(n,0))
            if delta>0: shifts.append({'node_key':n,'label':G.nodes[n].get('label',n),'betweenness_before':float(before_bet.get(n,0)),'betweenness_after':float(val),'delta':delta})
        shifts.sort(key=lambda x:x['delta'],reverse=True)
        closure={'node_key':closure_node,'station':closure_label,'components_before':len(comps),'components_after':len(hcomps),
                 'largest_component_nodes_before':len(largest),'largest_component_nodes_after':len(hlcc),
                 'largest_component_fraction_before':float(len(largest)/max(G.number_of_nodes(),1)),
                 'largest_component_fraction_after':float(len(hlcc)/max(H.number_of_nodes(),1)),
                 'connected_pair_fraction_before':pair_fraction_before,'connected_pair_fraction_after':pair_fraction_after,
                 'global_efficiency_before':global_eff_before,'global_efficiency_after':global_eff_after,
                 'average_shortest_path_lcc_before':before_on_giant,'average_shortest_path_lcc_after':path_after,
                 'top_betweenness_increases_after_closure':shifts[:10],
                 'interpretation_note':'Idealized node deletion: it removes the station and all incident edges. Global efficiency and connected-pair fraction are unweighted topological measures. This is not a measured passenger redistribution because origin-destination trips are absent; a real station closure may allow trains to pass through the station.'}
    else: closure={'status':'not run; no candidate nodes'}

    # Degree-preserving null model. Observed and null metrics are calculated on the
    # same largest connected component; modularity is UNWEIGHTED on both sides.
    # Connected swaps preserve connectedness and the degree sequence.
    null_result={'status':'skipped' if args.skip_null else 'not calculated'}
    if not args.skip_null and largest.number_of_nodes() >= 5 and largest.number_of_edges() >= 5:
        samples=[]; start=time.time()
        observed_null_communities = safe_communities(largest, seed=42, weight=None)
        base_metrics={
            'average_clustering_lcc': safe_float(nx.average_clustering(largest)),
            'average_shortest_path_lcc': safe_float(nx.average_shortest_path_length(largest)),
            'modularity_unweighted_lcc': safe_float(nx.community.modularity(largest, observed_null_communities, weight=None)),
        }
        edge_count=largest.number_of_edges()
        attempts=0
        while len(samples) < args.null_models and attempts < args.null_models * 10:
            replicate=len(samples)+1
            seed=7000+attempts
            attempts += 1
            R=largest.copy()
            requested_swaps=max(edge_count*5,1)
            swaps_done=0
            try:
                swaps_done=nx.connected_double_edge_swap(R, nswap=requested_swaps, seed=seed)
            except Exception:
                # Some degree sequences cannot support the requested number of
                # connected swaps. Retry a smaller number on a fresh graph.
                R=largest.copy()
                try:
                    swaps_done=nx.connected_double_edge_swap(R, nswap=max(edge_count,1), seed=seed+100000)
                except Exception:
                    continue
            if not nx.is_connected(R):
                continue
            original_degrees = sorted(dict(largest.degree()).values())
            randomized_degrees = sorted(dict(R.degree()).values())
            degree_preserved = original_degrees == randomized_degrees
            if not degree_preserved:
                continue
            cs=safe_communities(R,seed=seed,weight=None)
            canonical_edges = sorted((min(str(u), str(v)), max(str(u), str(v))) for u,v in R.edges())
            edge_hash = hashlib.sha256(json.dumps(canonical_edges, ensure_ascii=False).encode('utf-8')).hexdigest()
            samples.append({'replicate':replicate,'seed':seed,'connected_swaps_completed':int(swaps_done or 0),
                'is_connected':True,'degree_sequence_preserved':degree_preserved,'edge_set_hash':edge_hash,
                'average_clustering_lcc':safe_float(nx.average_clustering(R)),
                'average_shortest_path_lcc':safe_float(nx.average_shortest_path_length(R)),
                'modularity_unweighted_lcc':safe_float(nx.community.modularity(R,cs,weight=None)),
                'largest_component_fraction':1.0})
        sdf=pd.DataFrame(samples); sdf.to_csv(OUTPUT_DIR/'null_model_results.csv',index=False,encoding='utf-8-sig')
        stats={}
        for metric in ['average_clustering_lcc','average_shortest_path_lcc','modularity_unweighted_lcc']:
            vals=pd.to_numeric(sdf[metric],errors='coerce').dropna() if len(sdf) else pd.Series(dtype=float)
            obs=base_metrics.get(metric)
            mean=safe_float(vals.mean()) if len(vals) else None
            sd=safe_float(vals.std(ddof=1)) if len(vals)>1 else None
            z=(obs-mean)/sd if obs is not None and mean is not None and sd not in (None,0) else None
            p_emp=(1+int((vals >= obs).sum()))/(1+len(vals)) if obs is not None and len(vals)>0 else None
            stats[metric]={'observed':obs,'null_mean':mean,'null_std':sd,'z_score':safe_float(z),
                'empirical_upper_tail_p':safe_float(p_emp),'n_valid':int(len(vals))}
        null_df = pd.DataFrame(samples)
        unique_networks = int(null_df['edge_set_hash'].nunique()) if len(null_df) and 'edge_set_hash' in null_df else 0
        degree_preserved_count = int(null_df['degree_sequence_preserved'].sum()) if len(null_df) and 'degree_sequence_preserved' in null_df else 0
        null_result={'status':'calculated' if len(samples)==args.null_models and unique_networks==len(samples) and degree_preserved_count==len(samples) else 'incomplete',
            'replicates_requested':args.null_models,'replicates_completed':len(samples),'attempts':attempts,
            'unique_random_networks':unique_networks,'degree_sequence_preserved_count':degree_preserved_count,
            'all_null_graphs_connected':bool(len(samples) and null_df['is_connected'].all()),
            'base_graph_scope':'largest connected component; observed and null graph metrics use the same node set; connected degree-preserving swaps.',
            'modularity_comparison':'unweighted Louvain modularity on observed LCC and each null LCC; same definition on both sides.',
            'metrics':stats,'seconds':round(time.time()-start,2)}

    # Node-link JSON for Cytoscape is produced after community and centrality labels are attached.
    node_records=[]
    comm_map=comm_labels(G,louvain)
    for n,d in G.nodes(data=True):
        row=measures[measures.node_key==n].iloc[0]
        node_records.append({'data':{'id':str(n),'label':str(d.get('label',n)),'lines':str(d.get('lines','')),
            'passenger_mean_daily':float(d.get('passenger_mean_daily',0) or 0),'has_passenger_data':bool(d.get('has_passenger_data',False)),
            'degree':int(G.degree(n)),'betweenness':float(bet_unw[n]),'community':int(comm_map.get(n,-1))}})
    edge_records=[{'data':{'id':f'e{i}','source':str(u),'target':str(v),'strength':float(d.get('strength',1)),'routes':str(d.get('routes',''))}} for i,(u,v,d) in enumerate(G.edges(data=True))]
    write_json(ROOT/'web'/'graph_elements.json',{'nodes':node_records,'edges':edge_records})

    summary={
        'data_file':'data/raw/2025-yl-rayl-sistemler-istasyon-bazl-yolcu-ve-yolculuk-saylar.csv',
        'graph':{'nodes':G.number_of_nodes(),'edges':G.number_of_edges(),'density':safe_float(nx.density(G)),'connected_components':len(comps),
                 'component_sizes':[len(c) for c in comps],'largest_component_nodes':largest.number_of_nodes(),'largest_component_edges':largest.number_of_edges(),
                 'average_clustering_all_graph':clustering,'transitivity_all_graph':transitivity,'degree_assortativity':assort,
                 'average_shortest_path_largest_component':avg_path_lcc,'diameter_largest_component':diameter_lcc},
        'current_flow_status':cf_status,
        'community_detection':{'louvain':q_louvain,'louvain_stability':louvain_stability,'leiden':{'status':leiden_status,'metrics':leiden_q,'stability':leiden_stability}},
        'louvain_community_details':community_detail,
        'centrality_spearman_correlations':corr,
        'top_centrality_tables':top,
        'powerlaw':powerlaw_result,
        'null_model':null_result,
        'closure_scenario':closure,
        'critical_limitations':[
            'The topology CSV is a manually transcribed draft based on the official network map and must be checked line-by-line before final submission.',
            'Source line has 345 distinct nonblank station labels but many are directional entrances/platform variants; canonical station aliases are manual and need review.',
            'No origin-destination matrix is included, so edge weights and closure load shifts are passenger-activity/topological proxies, not observed interstation passenger flows.',
            'The graph has fewer than 500 nodes despite the generic assignment threshold; do not fabricate nodes. Ask the instructor whether the station-level case is exempt or whether scope must be expanded with valid data.',
            'The supplied source contains 728 records with blank station name and 23,858 records with blank coordinates per axis; coordinate cleaning only fixes malformed numeric formatting and does not impute missing locations.',
            'Power-law and Leiden results are only valid when their optional dependencies report calculated status; never describe a skipped calculation as a finding.'
        ]
    }
    write_json(OUTPUT_DIR/'analysis_summary.json',summary)
    print(json.dumps({'graph':summary['graph'],'current_flow':cf_status,'louvain':q_louvain,'leiden':leiden_status,'powerlaw':powerlaw_result,'null_model':null_result.get('status'),'closure':closure.get('station')},ensure_ascii=False,indent=2))
    print('Centralities:',OUTPUT_DIR/'centrality_and_communities.csv')

if __name__=='__main__': main()
