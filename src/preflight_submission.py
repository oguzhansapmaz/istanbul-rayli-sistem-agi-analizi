from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'

REQUIRED_FILES = {
    'Rapor PDF (6-10 sayfa)': OUT / 'rapor_TASLAK.pdf',
    'A3 poster PDF': OUT / 'ag_posteri_A3_TASLAK.pdf',
    'Sunum PowerPoint (8-10 slayt)': OUT / 'sunum_TASLAK.pptx',
    'Sunum PDF (yönergede isteniyor)': OUT / 'sunum_TASLAK.pdf',
    'GraphML ağ': OUT / 'istanbul_rail_2025.graphml',
    'Düğüm CSV': OUT / 'nodes.csv',
    'Kenar CSV': OUT / 'edges.csv',
    'Merkeziyet CSV': OUT / 'centrality_and_communities.csv',
    'Null model sonuçları': OUT / 'null_model_results.csv',
    'Analiz özeti': OUT / 'analysis_summary.json',
    'Etkileşimli ağ HTML': ROOT / 'web' / 'interactive_network.html',
    'Jupyter defteri': ROOT / 'notebooks' / '01_network_analysis.ipynb',
    'Veri sözlüğü': ROOT / 'docs' / 'data_dictionary.csv',
    'Topoloji doğrulama listesi': ROOT / 'docs' / 'topology_validation.csv',
    'Açık aktarma kenarları': ROOT / 'topology' / 'transfer_edges.csv',
}

def main() -> int:
    rows = []
    for label, path in REQUIRED_FILES.items():
        rows.append((label, path.exists(), str(path.relative_to(ROOT))))
    summary_path = OUT / 'analysis_summary.json'
    summary = {}
    if summary_path.exists():
        try: summary = json.loads(summary_path.read_text(encoding='utf-8'))
        except Exception as exc: summary = {'read_error': str(exc)}
    graph = summary.get('graph', {}) if isinstance(summary, dict) else {}
    node_count = graph.get('nodes')
    community = summary.get('community_detection', {}) if isinstance(summary, dict) else {}
    louvain = community.get('louvain', {})
    leiden = community.get('leiden', {})
    powerlaw = summary.get('powerlaw', {}) if isinstance(summary, dict) else {}
    metadata_path = OUT / 'graph_metadata.json'
    metadata = json.loads(metadata_path.read_text(encoding='utf-8')) if metadata_path.exists() else {}

    lines = [
        'SOSYAL AG ANALIZI — TESLIM ON KONTROLU',
        'Bu rapor otomatik dosya/mevcut yöntem kontrolüdür; öğretim elemanı onayı yerine geçmez.',
        '',
        'DOSYA KONTROLLERİ'
    ]
    for label, exists, rel in rows:
        lines.append(f"{'[OK]' if exists else '[EKSIK]'} {label}: {rel}")
    powerpoint = OUT / 'sunum_TASLAK.pptx'
    presentation_pdf = OUT / 'sunum_TASLAK.pdf'
    presentation_pdf_stale = presentation_pdf.exists() and powerpoint.exists() and presentation_pdf.stat().st_mtime < powerpoint.stat().st_mtime - 2
    lines += [
        '', 'ANALIZ DURUMU',
        f"Düğüm sayısı: {node_count if node_count is not None else 'özet bulunamadı'}",
        f"Kenar sayısı: {graph.get('edges', 'bilinmiyor')}",
        f"Kaynak kayıt eşleşme oranı (%): {metadata.get('match_rate_percent', 'bilinmiyor')}",
        f"Louvain: {louvain.get('community_count', 'bilinmiyor')} topluluk; modülerlik={louvain.get('modularity', 'bilinmiyor')}",
        f"Leiden durumu: {leiden.get('status', 'özet içinde yok')}",
        f"Power-law durumu: {powerlaw.get('status', 'özet içinde yok')}",
        f"Sunum PDF güncelliği: {'ESKİ — PowerPoint/LibreOffice ile yeniden dışa aktarılmalı' if presentation_pdf_stale else 'dosya mevcut ve PPTX ile güncellik açısından çelişki tespit edilmedi'}",
        '', 'TESLIM ONCESI INSAN / HOCAYA BAGLI KONTROLLER',
        '[!] Yönergedeki en az 500 düğüm şartı için öğretim elemanından kapsam açıklaması alınmalı. Fiziksel istasyon olmayan düğümler uydurulmamalı.',
        '[!] Kaynak istasyon adları, aliaslar ve aktarma kenarları docs/topology_validation.csv, topology/transfer_edges.csv, data/processed/station_alias_review.csv üzerinden insan tarafından gözden geçirilmeli.',
        '[!] Bu veri setinde başlangıç-varış (OD) matrisi yoktur. Kenar ağırlığı yolcu aktivitesi vekilidir; gerçek yolcu akışının kaydığı iddia edilmemeli.',
        '[!] Veri setinin resmî lisans/atıf metaverisi portal kaydından doğrulanmalı.',
        '[!] HTML etkileşimi tarayıcıda test edilmeli; CDN kullanıyorsa internet bağlantısı gerekir.',
        '[!] Slaytlar 8–10 adet olmalı ve öğrenci tüm ölçüleri kendi cümleleriyle açıklayabilmeli.',
        '', 'SONUC: Dosyalar mevcutsa bile bu çalışma otomatik olarak “teslime hazır / %100” demez.'
    ]
    report = '\n'.join(lines) + '\n'
    target = OUT / 'submission_preflight.txt'
    target.write_text(report, encoding='utf-8')
    print(report)
    print(f'Kontrol raporu yazıldı: {target}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
