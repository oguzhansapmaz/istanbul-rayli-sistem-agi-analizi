from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
import pandas as pd
import networkx as nx
from .common import ROOT, PROCESSED_DIR, OUTPUT_DIR, TOPOLOGY_FILE, canonical_station, load_raw, ensure_dirs, write_json


def keynorm(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value or '')).strip().replace('I', 'ı').replace('İ', 'i').casefold().split())


def main():
    ensure_dirs()
    clean_file = PROCESSED_DIR / 'clean_station_daily.csv'
    if not clean_file.exists():
        raise FileNotFoundError('Önce python -m src.prepare_data komutunu çalıştırın.')
    topo = pd.read_csv(TOPOLOGY_FILE, dtype=str, encoding='utf-8-sig')
    # CSV columns are initially strings; route order MUST be numeric (otherwise 10 sorts before 2).
    topo['station_order'] = pd.to_numeric(topo['station_order'], errors='raise').astype(int)
    data = pd.read_csv(clean_file, dtype={'line':str,'source_station_name':str,'station_canonical':str}, parse_dates=['date'], low_memory=False)
    data['line'] = data['line'].fillna('').str.strip()
    data['station_canonical'] = data['station_canonical'].fillna('').str.strip()
    data['match_key'] = data['station_canonical'].map(keynorm)

    topo['match_station'] = topo['match_station'].fillna(topo['station_name']) if 'match_station' in topo.columns else topo['station_name']
    topo['station_canonical'] = topo['match_station'].map(canonical_station)
    topo['match_key'] = topo['station_canonical'].map(keynorm)
    # Each source line + canonical station name maps to a specific graph node.
    match_map = {}
    ambiguity = []
    for r in topo.itertuples(index=False):
        k = (str(r.source_line).strip(), r.match_key)
        if k in match_map and match_map[k] != r.node_key:
            ambiguity.append({'source_line':k[0], 'station':k[1], 'first':match_map[k], 'second':r.node_key})
        else:
            match_map[k] = r.node_key

    data['node_key'] = [match_map.get((line, st), '') if st else '' for line, st in zip(data['line'], data['match_key'])]
    matched = data[data['node_key'].astype(str).str.strip().ne('')].copy()
    matched['passenger_count'] = pd.to_numeric(matched['passenger_count'], errors='coerce')
    matched['passage_count'] = pd.to_numeric(matched['passage_count'], errors='coerce')
    matched['longitude_clean'] = pd.to_numeric(matched['longitude_clean'], errors='coerce')
    matched['latitude_clean'] = pd.to_numeric(matched['latitude_clean'], errors='coerce')

    # Node attributes built from matched source records. Counts at transfer stations can combine line/entrance records;
    # this is a station-activity proxy, not an OD flow matrix.
    node_day = matched[matched['date'].notna() & matched['passenger_count'].notna()].groupby(['node_key','date'], as_index=False).agg(
        passenger_count=('passenger_count','sum'), passage_count=('passage_count','sum'), source_records=('node_key','size')
    )
    node_stats = node_day.groupby('node_key', as_index=False).agg(
        observed_days=('date','nunique'), passenger_mean_daily=('passenger_count','mean'),
        passenger_median_daily=('passenger_count','median'), passenger_total_source_sum=('passenger_count','sum'),
        passenger_max_daily=('passenger_count','max'), passage_mean_daily=('passage_count','mean'),
        matched_daily_records=('source_records','sum')
    )
    node_stats_map = node_stats.set_index('node_key').to_dict('index') if len(node_stats) else {}

    G = nx.Graph()
    # Nodes are defined from the manually transcribed route topology, not inferred from counts.
    for key, group in topo.groupby('node_key', sort=False):
        labels = list(dict.fromkeys(group['station_name'].tolist()))
        line_groups = list(dict.fromkeys(group['line_group'].tolist()))
        source_lines = list(dict.fromkeys(group['source_line'].tolist()))
        attrs = node_stats_map.get(key, {})
        G.add_node(key, label=' / '.join(labels), station_name=labels[0], lines=', '.join(line_groups),
                   source_lines=' | '.join(source_lines), has_passenger_data=bool(attrs),
                   passenger_mean_daily=float(attrs.get('passenger_mean_daily', 0.0)) if attrs else 0.0,
                   passenger_median_daily=float(attrs.get('passenger_median_daily', 0.0)) if attrs else 0.0,
                   passenger_total_source_sum=float(attrs.get('passenger_total_source_sum', 0.0)) if attrs else 0.0,
                   passenger_max_daily=float(attrs.get('passenger_max_daily', 0.0)) if attrs else 0.0,
                   observed_days=int(attrs.get('observed_days', 0)) if attrs else 0,
)
    edge_count_before = G.number_of_edges()
    for route_id, group in topo.groupby('route_id', sort=False):
        group = group.sort_values('station_order', kind='stable')
        rows = list(group[['node_key','station_name']].itertuples(index=False, name=None))
        pairs = list(zip(rows, rows[1:]))
        # T3 Kadıköy-Moda is a ring: include the last-to-first segment explicitly.
        circular = ('is_circular' in group.columns and group['is_circular'].astype(str).str.lower().eq('true').any())
        if circular and len(rows) > 2:
            pairs.append((rows[-1], rows[0]))
        for (u, ulabel), (v, vlabel) in pairs:
            if u == v:
                continue
            if G.has_edge(u,v):
                existing = G[u][v].get('routes','')
                if route_id not in existing.split(' | '):
                    G[u][v]['routes'] = (existing + f' | {route_id}').strip(' |')
            else:
                G.add_edge(u,v, routes=route_id, station_u=ulabel, station_v=vlabel, edge_type='route')
    # Explicit transfer edges connect separately named stations where the operator
    # describes a transfer; do not silently merge distinct station nodes.
    transfer_file = ROOT / 'topology' / 'transfer_edges.csv'
    if transfer_file.exists():
        transfers = pd.read_csv(transfer_file, dtype=str, encoding='utf-8-sig').fillna('')
        for t in transfers.itertuples(index=False):
            u, v = str(t.node_u), str(t.node_v)
            if u not in G or v not in G:
                raise ValueError(f'Transfer edge references unknown node: {u} / {v}')
            if G.has_edge(u, v):
                G[u][v]['routes'] = (str(G[u][v].get('routes', '')) + f' | TRANSFER:{t.route_u}-{t.route_v}').strip(' |')
                G[u][v]['edge_type'] = 'route+transfer'
            else:
                G.add_edge(u, v, routes=f'TRANSFER:{t.route_u}-{t.route_v}',
                           station_u=str(t.station_u), station_v=str(t.station_v),
                           edge_type='transfer', transfer_reason=str(t.reason), transfer_source=str(t.source_url))

    # Node passenger activity is the basis for edge strength; it is not an observed station-to-station OD flow.
    measured = [d['passenger_mean_daily'] for _,d in G.nodes(data=True) if d.get('has_passenger_data') and d.get('passenger_mean_daily',0)>0]
    fallback = float(pd.Series(measured).median()) if measured else 1.0
    for u,v,d in G.edges(data=True):
        pu = float(G.nodes[u].get('passenger_mean_daily',0) or 0)
        pv = float(G.nodes[v].get('passenger_mean_daily',0) or 0)
        if pu > 0 and pv > 0:
            strength = (pu + pv) / 2.0
        else:
            strength = (pu if pu>0 else pv if pv>0 else fallback)
        d['strength'] = max(strength, 1.0)
        d['distance'] = 1.0 / d['strength']

    nx.write_graphml(G, OUTPUT_DIR / 'istanbul_rail_2025.graphml')
    nodes = []
    for n,d in G.nodes(data=True):
        nodes.append({'node_key':n, **d, 'degree':int(G.degree(n)), 'weighted_degree_strength':float(G.degree(n,weight='strength'))})
    pd.DataFrame(nodes).to_csv(OUTPUT_DIR / 'nodes.csv',index=False,encoding='utf-8-sig')
    edges = [{'source':u,'target':v,**d} for u,v,d in G.edges(data=True)]
    pd.DataFrame(edges).to_csv(OUTPUT_DIR / 'edges.csv',index=False,encoding='utf-8-sig')
    unmatched = data[data['node_key'].astype(str).str.strip().eq('')]
    unmatched.groupby(['line','station_canonical'],dropna=False).size().reset_index(name='records').sort_values('records',ascending=False).to_csv(OUTPUT_DIR/'unmatched_source_stations.csv',index=False,encoding='utf-8-sig')
    matched.groupby(['line','station_canonical','node_key'],dropna=False).size().reset_index(name='records').to_csv(OUTPUT_DIR/'source_to_node_mapping.csv',index=False,encoding='utf-8-sig')
    nx.node_link_data(G, edges='edges')
    write_json(OUTPUT_DIR/'graph_metadata.json', {
        'node_count':G.number_of_nodes(),'edge_count':G.number_of_edges(),'connected_components':nx.number_connected_components(G),
        'matched_source_records':int(len(matched)),'unmatched_source_records':int(len(data)-len(matched)),
        'match_rate_percent': round(100*len(matched)/max(len(data),1),2),
        'topology_station_rows':int(len(topo)),'route_count':int(topo.route_id.nunique()),
        'explicit_transfer_edges': int(pd.read_csv(transfer_file).shape[0]) if transfer_file.exists() else 0,
        'topology_ambiguous_mappings':ambiguity,
        'topology_note':'Route order was corrected to numeric order; selected routes were cross-checked against official Metro Istanbul/IETT route lists. Remaining routes, name aliases, and transfer edges require review against docs/topology_validation.csv before submission.',
        'weight_note':'Edge strength is the mean of endpoint average daily passenger counts when available; edge distance is 1/strength. This is a passenger-activity proxy, not observed OD flow.'
    })
    print(f'Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {nx.number_connected_components(G)} components')
    print(f'Source records matched to topology: {len(matched):,}/{len(data):,} ({100*len(matched)/max(len(data),1):.1f}%)')
    print(f'Outputs: {OUTPUT_DIR / "istanbul_rail_2025.graphml"}, nodes.csv, edges.csv, unmatched_source_stations.csv')

if __name__ == '__main__': main()
