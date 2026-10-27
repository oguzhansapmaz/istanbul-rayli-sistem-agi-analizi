from __future__ import annotations
import json, math
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepTogether
from .common import ROOT, OUTPUT_DIR, ensure_dirs


def fmt(x, digits=3):
    if x is None: return 'Hesaplanmadı'
    try:
        if math.isnan(float(x)): return 'Hesaplanmadı'
        return f'{float(x):.{digits}f}'
    except Exception:
        return str(x)

def fmt_p(x):
    if x is None: return 'n/a'
    try:
        v=float(x)
        return f'{v:.2e}' if 0 < abs(v) < 0.001 else f'{v:.4f}'
    except Exception:
        return str(x)

def para(s, style): return Paragraph(s, style)

TABLE_BODY_STYLE = None
TABLE_HEADER_STYLE = None

def make_table(rows, widths=None, header=True):
    wrapped=[]
    for ri,row in enumerate(rows):
        wrapped_row=[]
        for cell in row:
            if isinstance(cell, Paragraph):
                wrapped_row.append(cell)
            else:
                st = TABLE_HEADER_STYLE if header and ri == 0 else TABLE_BODY_STYLE
                wrapped_row.append(Paragraph(escape(str(cell)), st) if st else escape(str(cell)))
        wrapped.append(wrapped_row)
    t=Table(wrapped,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
    commands=[('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#D7DEE8')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]
    if header:
        commands += [('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF0F6')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#152238')),('FONTNAME',(0,0),(-1,0),TABLE_HEADER_STYLE.fontName if TABLE_HEADER_STYLE else 'Helvetica-Bold')]
    t.setStyle(TableStyle(commands)); return t

def main():
    ensure_dirs()
    audit=json.loads((OUTPUT_DIR/'data_audit.json').read_text(encoding='utf-8'))
    summary=json.loads((OUTPUT_DIR/'analysis_summary.json').read_text(encoding='utf-8'))
    g=summary['graph']; comm=summary['community_detection']; null=summary['null_model']; closure=summary['closure_scenario']
    # Prefer Unicode fonts so Turkish characters render correctly on Linux and Windows.
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    win_font=Path('C:/Windows/Fonts/arial.ttf'); win_bold=Path('C:/Windows/Fonts/arialbd.ttf')
    if Path(font).exists() and Path(bold).exists():
        pdfmetrics.registerFont(TTFont('DejaVu',font)); pdfmetrics.registerFont(TTFont('DejaVu-Bold',bold)); F='DejaVu'; FB='DejaVu-Bold'
    elif win_font.exists() and win_bold.exists():
        pdfmetrics.registerFont(TTFont('ArialTR',str(win_font))); pdfmetrics.registerFont(TTFont('ArialTR-Bold',str(win_bold))); F='ArialTR'; FB='ArialTR-Bold'
    else: F='Helvetica'; FB='Helvetica-Bold'
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleTR',fontName=FB,fontSize=22,leading=28,textColor=colors.HexColor('#152238'),alignment=TA_LEFT,spaceAfter=9))
    styles.add(ParagraphStyle(name='SubTR',fontName=F,fontSize=10.5,leading=15,textColor=colors.HexColor('#536276'),spaceAfter=8))
    styles.add(ParagraphStyle(name='H1TR',fontName=FB,fontSize=15,leading=20,textColor=colors.HexColor('#152238'),spaceBefore=4,spaceAfter=8))
    styles.add(ParagraphStyle(name='H2TR',fontName=FB,fontSize=11.5,leading=15,textColor=colors.HexColor('#176B87'),spaceBefore=5,spaceAfter=5))
    styles.add(ParagraphStyle(name='BodyTR',fontName=F,fontSize=9.3,leading=13.5,textColor=colors.HexColor('#263445'),spaceAfter=7))
    styles.add(ParagraphStyle(name='SmallTR',fontName=F,fontSize=7.7,leading=10.5,textColor=colors.HexColor('#536276'),spaceAfter=5))
    styles.add(ParagraphStyle(name='WarnTR',fontName=FB,fontSize=9.2,leading=13,textColor=colors.HexColor('#8F2D2D'),borderColor=colors.HexColor('#E6B8B8'),borderWidth=0.7,borderPadding=7,backColor=colors.HexColor('#FFF5F5'),spaceBefore=5,spaceAfter=9))
    global TABLE_BODY_STYLE, TABLE_HEADER_STYLE
    TABLE_BODY_STYLE=ParagraphStyle(name='TableBodyTR',fontName=F,fontSize=7.8,leading=10,textColor=colors.HexColor('#263445'))
    TABLE_HEADER_STYLE=ParagraphStyle(name='TableHeaderTR',fontName=FB,fontSize=8,leading=10,textColor=colors.HexColor('#152238'))
    output=OUTPUT_DIR/'rapor_TASLAK.pdf'
    doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=17*mm,bottomMargin=17*mm,title='İstanbul Raylı Sistem Yolcu Akışı - Ön Rapor',author='Oğuzhan Sapmaz')
    story=[]
    # Page 1: cover and executive summary
    story += [Spacer(1,18*mm),para('İSTANBUL RAYLI SİSTEM YOLCU AĞI',styles['TitleTR']),para('Sosyal Ağ Analizi | 2025 istasyon bazlı yolcu verisi',styles['SubTR']),Spacer(1,5*mm)]
    story.append(para('PROJE RAPORU — TOPLOJİ VE KAPSAM KONTROLLERİ AÇIKÇA BELİRTİLMİŞTİR',styles['WarnTR']))
    story += [Spacer(1,7*mm),para('<b>Öğrenci:</b> Oğuzhan Sapmaz &nbsp;&nbsp; <b>Numara:</b> 2516016021',styles['BodyTR']),para('<b>Ders:</b> Sosyal Ağ Analizi &nbsp;&nbsp; <b>Dönem:</b> 2026-2027 Güz',styles['BodyTR']),para('<b>Rapor tarihi:</b> 27 Ekim 2026',styles['BodyTR']),Spacer(1,5*mm),para('Yönetici özeti',styles['H1TR']),para(f"Bu çalışma, İBB Açık Veri Portalı'nda yayımlanan 2025 istasyon bazlı yolcu ve yolculuk kayıtlarını kullanarak İstanbul raylı sistemleri için bir istasyon ağı kurmayı hedefler. CSV dosyası {audit['rows']:,} kayıt, {audit['distinct_lines']} hat ve {audit['distinct_station_numbers']} farklı istasyon kodu içerir. Ön ağ taslağı {g['nodes']} düğüm ve {g['edges']} kenardan oluşmuştur; en büyük bağlı bileşende {g['largest_component_nodes']} düğüm vardır.",styles['BodyTR']),para('Bu PDF, çalışan analiz zincirinin rapor çıktısıdır; topoloji sıraları numeric olarak kurulur ve seçilen hatlar resmî Metro İstanbul/IETT sayfalarına göre gözden geçirilmiştir. Ancak hatların tamamında tüm aktarma/alias kararları kesinleştirilmiş değildir. Genel yönergedeki 500 düğüm şartı, OD akışının bulunmaması ve source alias kayıtları final kararından önce açıkça değerlendirilmelidir.',styles['BodyTR']),PageBreak()]
    # Page 2 research question/data
    story += [para('1. Araştırma sorusu ve veri kaynağı',styles['H1TR']),para('<b>Araştırma sorusu 1:</b> Topolojik olarak merkezi istasyonlar, 2025 yolcu aktivitesi yüksek istasyonlarla aynı mıdır?',styles['BodyTR']),para('<b>Araştırma sorusu 2:</b> Bir aktarma düğümü kapatıldığında erişilebilirlik ve en kısa yollar nasıl değişir; hangi düğümlerin betweenness değeri artar?',styles['BodyTR']),para('Kaynak verinin içinde transaction_year, transaction_month, transaction_day, line, station_name, station_number, town, longitude, latitude, passage_cnt ve passanger_cnt alanları vardır. Kaynak alan adı passanger_cnt yazım hatasıyla yayımlanmıştır; kod bunu passenger_count olarak yeniden adlandırır, kaynak dosyayı değiştirmez.',styles['BodyTR']),make_table([
        ['Denetim ölçütü','Gözlenen değer'],['Kaynak kayıt sayısı',f"{audit['rows']:,}"],['Kaynak sütun sayısı',str(audit['columns'])],['Yıl',', '.join(audit['years'])],['Hat sayısı',str(audit['distinct_lines'])],['Farklı ham istasyon adı',str(audit['distinct_source_station_names_including_blank'])],['Farklı istasyon kodu',str(audit['distinct_station_numbers'])],['Tam yinelenen satır',str(audit['duplicate_full_source_rows'])]
    ],[85*mm,75*mm]),Spacer(1,5*mm),para('Kaynak bağlantıları',styles['H2TR']),para('İBB Açık Veri Portalı: https://data.ibb.gov.tr/ — “Raylı Sistemler İstasyon Bazlı Yolcu ve Yolculuk Sayıları” veri seti.',styles['SmallTR']),para('Metro İstanbul resmi ağ haritası: https://www.metro.istanbul/Content/assets/uploaded/%C4%B0stanbul%20Rayl%C4%B1%20Sistemler%20Haritas%C4%B1.pdf',styles['SmallTR']),PageBreak()]
    # Page 3 data cleanup
    story += [para('2. Veri hazırlama ve kalite kontrolleri',styles['H1TR']),para('CSV, noktalı virgül ayırıcıyla okunur. Kayıt tarihi üç tarih alanından oluşturulur. passenger_count ve passage_count sayısal tipe dönüştürülür. Koordinatlar kaynakta “289.335.555.555.556” gibi hatalı gruplandırılmış bir biçimde olduğundan, İstanbul için iki basamaklı derece bölümü korunup geri kalan basamaklar kesir kısmı olarak yorumlanır. Dönüşüm yalnızca koordinat aralığı kontrolünden geçen değerleri kabul eder; eksik konumlar uydurulmaz.',styles['BodyTR']),para('Kaynak ve türetilmiş alanların açıklaması, tür/birim bilgisi, dönüşüm ve kalite notları docs/data_dictionary.csv dosyasında verilmiştir. Yolcu/geçiş sayısının kaynakta hangi giriş/çıkış sayım kuralıyla üretildiği ve lisans/atıf koşulu ayrıca portal metaverisinden teyit edilmelidir.',styles['SmallTR']),make_table([
        ['Kalite kontrolü','Sonuç'],['İstasyon adı eksik kayıt',f"{audit['missing_station_name_records']:,}"],['Boylam eksik kayıt',f"{audit['missing_longitude_source_records']:,}"],['Enlem eksik kayıt',f"{audit['missing_latitude_source_records']:,}"],['Aralık kontrolünden geçen koordinat kaydı',f"{audit['normalized_valid_coordinate_records']:,}"],['Yolcu sayısı sayısal hatası',str(audit['passenger_numeric_invalid'])],['Geçiş sayısı sayısal hatası',str(audit['passage_numeric_invalid'])],['Takma ad birleştirmesi sonrası istasyon etiketleri',str(audit['canonical_station_labels'])]
    ],[85*mm,75*mm]),Spacer(1,5*mm),para('İstasyon adları yön, hol veya giriş varyantları içerebildiği için `src/common.py` dosyasında açık takma ad eşleştirmeleri bulunur. Bu eşleştirmeler araştırma varsayımıdır ve `data/processed/station_alias_review.csv` üzerinden gözden geçirilmelidir. İstasyon adlarının yanlış birleştirilmesi merkezilik sonuçlarını değiştirebilir.',styles['WarnTR']),PageBreak()]
    # Page 4 network model
    story += [para('3. Ağ modeli ve ağırlıkların anlamı',styles['H1TR']),para('Düğüm: fiziksel istasyon veya açıkça birleştirilen ortak istasyon kompleksi. Kenar: aynı hat üzerinde ardışık istasyon bağlantısı ya da resmî hat sayfasında belirtilen ayrı isimli istasyonlar arası aktarma bağlantısıdır. Paralel giriş/hol kayıtları belgelenmiş takma adlarla normalize edilir. Üç ayrı aktarma bağlantısı `topology/transfer_edges.csv` dosyasında gerekçe ve kaynak adresleriyle ayrı kenar olarak tutulur; tüm aktarma ve aliaslar yine insan kontrolü gerektirir.',styles['BodyTR']),para('Kenar ağırlığı (strength), uç istasyonların ortalama günlük passenger_count değerlerinin aritmetik ortalaması olarak hesaplanır. En kısa yol tabanlı ağırlıklı merkeziyetlerde maliyet `distance = 1 / strength` şeklinde tanımlanır. Bu seçim, yüksek yolcu aktivitesine sahip bağlantıları daha düşük maliyetli kabul eden bir model varsayımıdır.',styles['BodyTR']),para('Bu kaynakta istasyonlar arası başlangıç-varış (OD) yolculuk matrisi bulunmadığından, kenar ağırlığı gerçek iki-istasyon arası akış değildir. Kapanma senaryosundaki “yük kayması” da gerçek yolcu talebi değil, düğüm çıkarıldıktan sonra betweenness merkeziyetindeki artışla ölçülen topolojik yeniden yönelme göstergesidir.',styles['WarnTR']),make_table([
        ['Ağ özelliği','İlk hesaplama'],['Düğüm / kenar',f"{g['nodes']} / {g['edges']}"],['Bağlı bileşen sayısı',str(g['connected_components'])],['Bileşen büyüklükleri',', '.join(map(str,g['component_sizes']))],['En büyük bileşen düğüm / kenar',f"{g['largest_component_nodes']} / {g['largest_component_edges']}"],['Yoğunluk',fmt(g['density'],5)],['Ortalama en kısa yol (en büyük bileşen)',fmt(g['average_shortest_path_largest_component'],3)],['Çap (en büyük bileşen)',fmt(g['diameter_largest_component'],0)],['Ortalama kümelenme katsayısı',fmt(g['average_clustering_all_graph'],4)],['Derece assortativity',fmt(g['degree_assortativity'],4)]
    ],[95*mm,65*mm]),PageBreak()]
    # Page 5 centrality
    story += [para('4. Merkeziyet sonuçları',styles['H1TR']),para('Kod, derece, ağırlıksız betweenness, yolcu aktivitesi temelli ağırlıklı betweenness, closeness, eigenvector centrality, PageRank ve en büyük bağlı bileşen içinde current-flow betweenness ölçülerini üretir. `centrality_and_communities.csv` bütün düğümlerin değerlerini; `analysis_summary.json` ilk 10 düğüm listelerini ve Spearman korelasyonlarını içerir.',styles['BodyTR']),para(f"Current-flow betweenness durumu: {escape(str(summary['current_flow_status']))}.",styles['BodyTR'])]
    top=summary['top_centrality_tables'].get('betweenness_unweighted',[])[:10]
    rows=[['Sıra','İstasyon düğümü','Betweenness']]
    for i,r in enumerate(top,1): rows.append([str(i),str(r['label']),fmt(r['betweenness_unweighted'],5)])
    story += [make_table(rows,[16*mm,112*mm,32*mm]),Spacer(1,3*mm),para('Yorum: Ağırlıksız betweenness en kısa yol aracı olarak sık kullanılan düğümleri, ağırlıklı betweenness ise yolcu aktivitesinden türetilmiş ters maliyetleri dikkate alan modelde aracı düğümleri gösterir. İki sıralama arasındaki fark, ağırlık varsayımı ve topolojiyle birlikte yorumlanmalıdır.',styles['BodyTR'])]
    corr_items=list(summary.get('centrality_spearman_correlations',{}).items())
    corr_items=[(k,v) for k,v in corr_items if v.get('rho') is not None]
    corr_items.sort(key=lambda kv: abs(float(kv[1]['rho'])), reverse=True)
    corr_rows=[['Merkeziyet çiftleri (en yüksek |rho|)','Spearman rho']]
    for key,val in corr_items[:5]:
        a,b=key.split('__',1)
        corr_rows.append([f'{a} ↔ {b}',fmt(val.get('rho'),3)])
    if len(corr_rows)>1:
        story += [para('Merkeziyet ölçüleri arası Spearman ilişkileri (en yüksek mutlak korelasyonlar)',styles['H2TR']),make_table(corr_rows,[124*mm,36*mm]),para('Tam eşleşme listesi outputs/centrality_spearman_correlations.csv dosyasına yazılır. Bu ortamda p-değerleri hesaplanmadı; rho, ölçülerin sıralama benzerliğini gösterir.',styles['SmallTR'])]
    story += [para('İstasyon etiketleri resmî ad ve kaynak aliaslarından oluşturuldu. Hatalı/eksik hat bağlantısı kalması hâlinde merkezilik sıraları değişebilir; `docs/topology_validation.csv` ve eşleşmeyen istasyon listesi son kez kontrol edilmelidir.',styles['WarnTR']),PageBreak()]
    # Page 6 communities/null
    story += [para('5. Topluluk tespiti ve null model',styles['H1TR']),para(f"Louvain ön çalışması {comm['louvain']['community_count']} topluluk ve modülerlik Q = {fmt(comm['louvain']['modularity'],4)} üretmiştir. Topluluk büyüklükleri: {', '.join(map(str,comm['louvain']['sizes'][:10]))}{'…' if len(comm['louvain']['sizes'])>10 else ''}.",styles['BodyTR']),para(f"Louvain kararlılığı ({summary['community_detection'].get('louvain_stability',{}).get('n_seeds','?')} farklı tohum): ortalama ARI = {fmt(summary['community_detection'].get('louvain_stability',{}).get('mean_ARI_vs_seed42'),3)}, ortalama NMI = {fmt(summary['community_detection'].get('louvain_stability',{}).get('mean_NMI_vs_seed42'),3)}.",styles['BodyTR'])]
    leiden=comm.get('leiden',{})
    if leiden.get('metrics') and leiden.get('status','').lower().startswith('calculated'):
        lm=leiden['metrics']; ls=leiden.get('stability',{})
        ltxt=(f"Leiden sonucu hesaplandı: {lm.get('community_count','?')} topluluk, Q = {fmt(lm.get('modularity'),4)}. "
              f"{ls.get('n_seeds','?')} tohum için ortalama ARI = {fmt(ls.get('mean_ARI_vs_seed42'),3)} ve NMI = {fmt(ls.get('mean_NMI_vs_seed42'),3)}.")
        story.append(para(escape(ltxt),styles['BodyTR']))
    else:
        story.append(para('Leiden sonucu hesaplanmadı: '+escape(str(leiden.get('status','durum kaydı yok'))),styles['WarnTR']))
    profiles=summary.get('louvain_community_details',[])
    if profiles:
        prows=[[ 'Boyut sırası', 'Önerilen topluluk adı', 'Düğüm', 'Baskın hatlar'] ]
        for c in profiles[:5]:
            prows.append([str(c.get('rank_by_size','?')), c.get('candidate_name','Ad önerisi gözden geçirilmeli'), str(c.get('size','?')), ', '.join(c.get('dominant_lines',[])[:3])])
        story += [para('En büyük topluluklar için çalışma adları',styles['H2TR']),make_table(prows,[19*mm,72*mm,17*mm,48*mm]),para('Adlar hat üyeliklerinden üretilen analist önerileridir; topluluklar otomatik olarak gerçek semtler veya yolcu davranışı kümeleri anlamına gelmez. Sunumda topluluk içeriği ve sınırları ayrıca açıklanmalıdır.',styles['SmallTR'])]
    else:
        story += [para('Topluluk isimlendirmesi: outputs/community_profile.csv dosyası analiz çalıştırıldığında üretilir; isimler yorum amaçlı aday etiketlerdir.',styles['SmallTR'])]
    if null.get('status')=='calculated':
        nrows=[['Ölçü','Gözlenen','Null ort.','z-skoru','N']]
        for k,v in null['metrics'].items(): nrows.append([k,fmt(v.get('observed'),4),fmt(v.get('null_mean'),4),fmt(v.get('z_score'),3),str(v.get('n_valid'))])
        story += [para('Derece koruyan 100 rastgele ağ karşılaştırması',styles['H2TR']),make_table(nrows,[57*mm,27*mm,27*mm,27*mm,22*mm]),para('Null ağlar en büyük bağlı bileşen üzerinde degree-preserving double-edge swap işlemiyle üretilmiştir. Modülerlik karşılaştırması ağırlıksız tanımlıdır. z-skoru, gözlenen ölçünün null dağılım ortalamasına göre standart sapma farkıdır.',styles['SmallTR'])]
    else:
        story += [para('Null model: '+escape(str(null.get('status','hesaplanmadı')))+'. Tam teslim için en az 100 rastgele ağ üretimi ve kümelenme, ortalama yol, modülerlik için z-skorları gereklidir.',styles['WarnTR'])]
    pw=summary.get('powerlaw',{})
    if pw.get('status')=='calculated':
        pe=pw.get('power_law_vs_exponential',{}); pl=pw.get('power_law_vs_lognormal',{})
        def comparison_text(name, obj, alternative):
            r=obj.get('R'); pv=obj.get('p_value')
            if r is None or pv is None: return f"{name} karşılaştırması için yeterli sonuç yok."
            favoured='power-law' if float(r)>0 else alternative if float(r)<0 else 'belirgin tercih yok'
            return f"Power-law / {name}: R={fmt(r,3)}, p={fmt_p(pv)}; log-olabilirlik oranı {favoured} dağılımını destekliyor."
        pwtext=(f"Derece dağılımı powerlaw ile karşılaştırıldı (durum: hesaplandı; alpha={fmt(pw.get('alpha'),3)}, xmin={fmt(pw.get('xmin'),3)}, pozitif derece örneklemi={pw.get('n_positive_degree','bilinmiyor')}). "
                +comparison_text('exponential',pe,'exponential')+' '+comparison_text('lognormal',pl,'lognormal')+
                ' Sonuçlar, tek başına power-law uyumunun kanıtı olarak yorumlanmamalıdır; xmin üzerindeki örneklem büyüklüğü ve grafik de incelenmelidir.')
        story.append(para(escape(pwtext),styles['BodyTR']))
    else:
        story.append(para('Power-law / alternatif dağılım karşılaştırması hesaplanmadı: '+escape(str(pw.get('reason',pw.get('status','durum kaydı yok')))),styles['WarnTR']))
    story.append(PageBreak())
    # Page 7 closure, limits, checklist
    story += [para('6. İstasyon kapanma senaryosu ve sınırlar',styles['H1TR']),para(f"Topolojik düğüm silme senaryosunda en yüksek ağırlıksız betweenness aday düğüm: <b>{escape(str(closure.get('station','hesaplanmadı')))}</b>. Düğüm çıkarıldığında bağlı bileşen sayısı {closure.get('components_before','?')} → {closure.get('components_after','?')}; en büyük bileşen {closure.get('largest_component_nodes_before','?')} → {closure.get('largest_component_nodes_after','?')} düğüm olur. Tüm olası düğüm çiftleri içinde aynı bağlı bileşende kalabilen çiftlerin oranı {fmt(closure.get('connected_pair_fraction_before'),3)} → {fmt(closure.get('connected_pair_fraction_after'),3)}; ağırlıksız global efficiency {fmt(closure.get('global_efficiency_before'),4)} → {fmt(closure.get('global_efficiency_after'),4)} değişmiştir.",styles['BodyTR']),para('Ortalama en kısa yol, her durumda o grafiğin en büyük bağlı bileşeni üzerinde hesaplandığı için kapanma öncesi ve sonrası aynı düğüm kümesini kapsamaz; tek başına bu iki ortalamayı karşılaştırmak yanıltıcı olabilir. Global efficiency ve bağlı çift oranı tüm grafiğin erişilebilirlik kaybını daha iyi özetler.',styles['SmallTR']),para('Bu senaryo gerçek işletme kapanışı değil, düğümün ve ona bağlı tüm kenarların silindiği idealize topolojik testtir. Başlangıç-varış (OD) matrisi olmadığından yolcu sayısının hangi hatta ne kadar kayacağı tahmin edilmemektedir; betweenness artan düğümler yalnızca topolojik aracı adaylarıdır.',styles['BodyTR']),para('Teslim öncesi zorunlu doğrulamalar',styles['H2TR']),make_table([
        ['Durum','Gereken iş'],
        ['Yüksek öncelik','`docs/topology_validation.csv` ve `topology/line_stations.csv` birlikte kontrol edilmeli; işaretli resmî sayfa referansları tüm aktarma ve isim aliaslarının otomatik doğrulandığı anlamına gelmez.'],
        ['Yüksek öncelik','Genel yönergedeki en az 500 düğüm şartı, fiziksel istasyon düzeyindeki bu veriyle karşılanmıyor. Düğüm uydurma; öğretim elemanından kapsamı yazılı olarak netleştir.'],
        ['Orta öncelik','`docs/data_dictionary.csv` içindeki kaynak sütunları, ölçü birimleri, 2025 kapsamı ve lisans durumu rapordaki kaynak kayıt sayfasıyla karşılaştırılmalı.'],
        ['Yöntem durumu',f"Leiden: {escape(str(leiden.get('status','bilinmiyor')))}; bu PDF üretildiği ortamda hesaplanmayan bir yöntem varsa final bulgusu olarak yazma."],
        ['Yöntem durumu',f"Power-law: {escape(str(pw.get('status','bilinmiyor')))}; alternatif dağılım karşılaştırmalarının işaretlerini ve örneklem aralığını yorumla."],
        ['Orta öncelik','`data/processed/station_alias_review.csv` ile `outputs/unmatched_source_stations.csv` listesindeki eski/boş adları son kez gözden geçir.'],
        ['Orta öncelik','Etkileşimli HTML içinde arama, düğüm detay paneli ve topluluk filtresini test et; ardından mevcut portföy sayfana göm.'],
        ['Son adım','Topoloji ve yöntem durumu doğrulandıktan sonra rapor, poster ve 8–10 slayt sunumunu son kez üret ve sunum provası yap.']
    ],[32*mm,128*mm]),Spacer(1,4*mm),para('Yapay zekâ beyanı',styles['H2TR']),para('Bu projede kod iskeleti, veri doğrulama, rapor taslağı ve sunum taslağı oluşturmak için yapay zekâ desteği alınmıştır. Veri kaynağı, hat sıraları ve bulgular öğrenci tarafından kontrol edilmeli; sunumda açıklanamayan analizler nihai sonuç olarak sunulmamalıdır.',styles['SmallTR'])]

    def footer(canvas,doc):
        canvas.saveState(); canvas.setFont(F,7.5); canvas.setFillColor(colors.HexColor('#718096'))
        canvas.drawString(18*mm,9*mm,'Sosyal Ağ Analizi | Ön rapor - doğrulama gerekli')
        canvas.drawRightString(A4[0]-18*mm,9*mm,f'Sayfa {doc.page}')
        canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print('Report created:',output)

if __name__=='__main__': main()
