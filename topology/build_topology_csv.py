import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'topology' / 'line_stations.csv'

# Ordered station sequences manually transcribed from the published Metro Istanbul network map.
# Branches are represented as separate route_id values. Verify each sequence against the source map before final submission.
ROUTES = [
('M1A','M1','M1-YENIKAPI-HAVALIMANI',['Yenikapı','Aksaray','Emniyet-Fatih','Topkapı-Ulubatlı','Bayrampaşa-Maltepe','Sağmalcılar','Kartaltepe-Kocatepe','Otogar','Terazidere','Davutpaşa-YTÜ','Merter','Zeytinburnu','Bakırköy-İncirli','Bahçelievler','Ataköy-Şirinevler (M1)','Yenibosna','DTM-İstanbul Fuar Merkezi','Atatürk Havalimanı']),
('M1B','M1','M1-YENIKAPI-HAVALIMANI',['Otogar','Esenler','Menderes','Üçyüzlü','Bağcılar Meydan','Kirazlı']),
('M2_MAIN','M2','M2-YENIKAPI-HACIOSMAN',['Yenikapı','Vezneciler-İstanbul Üniversitesi','Haliç','Şişhane','Taksim','Osmanbey','Şişli-Mecidiyeköy','Gayrettepe','Levent','4. Levent','Sanayi Mahallesi','İTÜ-Ayazağa','Atatürk Oto Sanayi','Darüşşafaka','Hacıosman']),
('M2_BRANCH','M2','M2-YENIKAPI-HACIOSMAN',['Sanayi Mahallesi','Seyrantepe']),
('M3','M3','M3-BASAKSEHIR-OLIMPIYATKOY',['Bakırköy Sahil','Özgürlük Meydanı','İncirli','Haznedar','İlkyuva','Yıldıztepe','Molla Gürani','Kirazlı-Bağcılar','Yenimahalle','Mahmutbey','İSTOÇ','İkitelli Sanayi','Turgut Özal','Siteler','Başak Konutları','Başakşehir-Metrokent','Onurkent','Şehir Hastanesi','Toplu Konutlar','Kayaşehir Merkez']),
('M4','M4','M4-KADIKOY-TAVSANTEPE',['Kadıköy','Ayrılık Çeşmesi','Acıbadem','Ünalan','Göztepe','Yenisahra','Kozyatağı','Bostancı','Küçükyalı','Maltepe','Huzurevi','Gülsuyu','Esenkent','Hastane-Adliye','Soğanlık','Kartal','Yakacık-Adnan Kahveci','Pendik','Tavşantepe','Fevzi Çakmak','Yayalar','Kurtköy','Sabiha Gökçen Havalimanı']),
('M5','M5','M5-USKUDAR CEKMEKOY METROSU',['Üsküdar','Fıstıkağacı','Bağlarbaşı','Altunizade','Kısıklı','Bulgurlu','Ümraniye','Çarşı','Yamanevler','Çakmak','Ihlamurkuyu','Altınşehir','İmam Hatip Lisesi','Dudullu','Necip Fazıl','Çekmeköy','Meclis','Sarıgazi','Sancaktepe','Samandıra Merkez']),
('M6','M6','M6-LEVENT - RUMELI HISARUSTU',['Levent','Nispetiye','Etiler','Boğaziçi Üniversitesi/Hisarüstü']),
('M7','M7','M7-KABATAS-MAHMUTBEY',['Yıldız','Fulya','Şişli-Mecidiyeköy','Çağlayan','Kağıthane','Nurtepe','Alibeyköy Metro','Çırçır','Veysel Karani-Akşemsettin','Yeşilpınar','Kazım Karabekir','Yenimahalle','Karadeniz Mahallesi','Tekstilkent-Giyimkent','Oruç Reis','Göztepe (M7)','Mahmutbey']),
('M8','M8','M8 DUDULLU - BOSTANCI',['Bostancı','Emin Ali Paşa','Ayşekadın','Kozyatağı','Küçükbakkalköy','İçerenköy','Kayışdağı','Mevlana','İMES','MODOKO-KEYAP','Dudullu','Huzur (M8)','Parseller']),
('M9','M9','M9 ATAKOY-IKITELLI METRO',['Ataköy (M9)','Yenibosna','Çobançeşme','29 Ekim Cumhuriyet','Doğu Sanayi','Mimar Sinan','15 Temmuz','Halkalı Caddesi','Atatürk Mahallesi','Bahariye','Masko','İkitelli Sanayi','Ziya Gökalp Mahallesi','Olimpiyat']),
('T1','T1','T1-KABATAS-BAGCILAR',['Kabataş','Fındıklı-Mimar Sinan Ü.','Tophane','Karaköy','Eminönü','Sirkeci','Gülhane','Sultanahmet','Çemberlitaş','Beyazıt-Kapalıçarşı','Laleli-İstanbul Ü.','Aksaray','Yusufpaşa','Haseki','Fındıkzade','Çapa-Şehremini','Pazartekke','Topkapı','Cevizlibağ-AÖY','Merkezefendi','Seyitnizam-Akşemsettin','Mithatpaşa','Zeytinburnu','Mehmet Akif','Merter Tekstil Merkezi','Güngören','Akıncılar','Soğanlı','Yavuzselim','Güneştepe','Bağcılar']),
('T3','T3','T3-KADIKOY-MODA',['Kadıköy İDO','İskele Camii','Çarşı','Altıyol','Bahariye','Kilise','Moda İlkokulu','Moda','Rızapaşa','Mühürdar','Damga Sokak']),
('T2','T2','IETT NOSTALJIK TRAMVAY',['Taksim Meydan','Hüseyin Ağa Camii','Galatasaray Lisesi','Odakule','Beyoğlu Tünel']),
('F3','F3','F3 SEYRANTEPE-VADISTANBUL FUNIKILER HATTI',['Seyrantepe','Vadistanbul']),
('T4','T4','T4-TOPKAPI-MESCID-I SELAM',['Topkapı','Fetihkapı','Vatan','Edirnekapı','Şehitlik','Demirkapı','Topçular','Rami','Bereç','Sağmalcılar','Çukurçeşme','Ali Fuat Başgil','Taşköprü','Karadeniz Mahallesi','Kiptaş Venezia','Cumhuriyet','Baştabya','Hacı Şükrü','Yenimahalle','Sultançiftliği','Cebeci','Mescidi Selam']),
('T5','T5','T5 EMINONU-ALIBEYKOY',['Eminönü','Küçükpazar','Cibali','Fener','Balat','Ayvansaray','Feshane','Eyüp Teleferik','Eyüp Devlet Hastanesi','Silahtarağa','Üniversite','Alibeyköy','Alibeyköy Metro','Cep Otogar']),
('M11','M11','TCDD - GAYRETTEPE-ISTANBUL YENI HAVALIMANI',['Gayrettepe','Kağıthane','Hasdal','Kemerburgaz','Göktürk','İhsaniye','İstanbul Havalimanı','Kargo Terminali','Taşoluk','Arnavutköy']),
('MARMARAY','MAR','TCDD TASIMACILIK A.S.',['Gebze','Darıca','Osmangazi','Çayırova','Fatih','Tuzla','İçmeler','Aydıntepe','Güzelyalı','Tersane','Kaynarca','Pendik (Marmaray)','Yunus','Kartal (Marmaray)','Atalar','Başak','Cevizli (Marmaray)','Maltepe','İdealtepe','Süreyya Plajı','Küçükyalı (Marmaray)','Bostancı (Marmaray)','Suadiye','Erenköy','Göztepe (Marmaray)','Feneryolu','Söğütlüçeşme','Ayrılık Çeşmesi','Üsküdar','Sirkeci','Yenikapı','Kazlıçeşme','Zeytinburnu','Yenimahalle (Marmaray)','Ataköy','Bakırköy (Marmaray)','Yeşilyurt','Yeşilköy','Florya Akvaryum','Florya','Küçükçekmece','Mustafa Kemal','Halkalı (Marmaray)']),
('SIRKECI_KAZLICESME','SIRKECI','TCDD SIRKECI-KAZLICESME',['Sirkeci','Cankurtaran','Kumkapı','Yenikapı','Cerrahpaşa','Kocamustafapaşa','Yedikule','Kazlıçeşme']),
('HALKALI_BAHCESEHIR','HB','TCDD - HALKALI-BASAKSEHIR',['Halkalı (Bahçeşehir treni)','Ispartakule','Bahçeşehir']),
('F1','F1','F1-TAKSIM-KABATAS FUNIKILER HATTI',['Taksim','Kabataş']),
('F4','F4','F4 RUMELI HISARUSTU -ASIYAN',['Boğaziçi Üniversitesi/Hisarüstü','Aşiyan']),
('TF1','TF1','TF1-TELEFERIK MACKA - TASKISLA',['Maçka','Taşkışla']),
('TF2','TF2','TF2-TELEFERIK EYUP PIYERLOTI',['Eyüp Teleferik','Pierloti']),
('TUNEL','TUNEL','IETT TUNEL',['Karaköy','Beyoğlu']),
]

# Explicit cross-line interchange keys only; all other stations remain line-specific to avoid false merges.
TRANSFER_KEYS = {
    ('M1','yenikapı'):'X:Yenikapı', ('M2','yenikapı'):'X:Yenikapı', ('MAR','yenikapı'):'X:Yenikapı', ('SIRKECI','yenikapı'):'X:Yenikapı',
    ('M1','aksaray'):'X:Aksaray', ('T1','aksaray'):'X:Aksaray',
    ('M1','bakırköy-incirli'):'X:İncirli', ('M3','incirli'):'X:İncirli',
    ('M1','topkapı-ulubatlı'):'X:Vatan-M1', ('T4','vatan'):'X:Vatan-M1', ('T1','topkapı'):'X:Topkapı', ('T4','topkapı'):'X:Topkapı',
    ('M1','zeytinburnu'):'X:Zeytinburnu', ('T1','zeytinburnu'):'X:Zeytinburnu', ('MAR','zeytinburnu'):'X:Zeytinburnu',
    ('M1','yenibosna'):'X:Yenibosna', ('M9','yenibosna'):'X:Yenibosna',
    ('M1','bağcılar meydan'):'X:Bağcılar', ('T1','bağcılar'):'X:Bağcılar',
    ('M1','kirazlı'):'X:Kirazlı', ('M3','kirazlı-bağcılar'):'X:Kirazlı', ('M3','kirazlı'):'X:Kirazlı',
    ('M3','mahmutbey'):'X:Mahmutbey', ('M7','mahmutbey'):'X:Mahmutbey',
    ('M3','ikitelli sanayi'):'X:İkitelli Sanayi', ('M9','ikitelli sanayi'):'X:İkitelli Sanayi',
    ('M2','şişli-mecidiyeköy'):'X:Mecidiyeköy', ('M7','şişli-mecidiyeköy'):'X:Mecidiyeköy',
    ('M7','kağıthane'):'X:Kağıthane', ('M11','kağıthane'):'X:Kağıthane',
    ('M7','karadeniz mahallesi'):'X:Kiptaş-Venezia', ('T4','kiptaş venezia'):'X:Kiptaş-Venezia',
    ('M2','gayrettepe'):'X:Gayrettepe', ('M11','gayrettepe'):'X:Gayrettepe',
    ('M2','levent'):'X:Levent', ('M6','levent'):'X:Levent',
    ('M6','boğaziçi üniversitesi/hisarüstü'):'X:Hisarüstü', ('F4','boğaziçi üniversitesi/hisarüstü'):'X:Hisarüstü',
    ('M2','taksim'):'X:Taksim', ('F1','taksim'):'X:Taksim', ('T2','taksim meydan'):'X:Taksim',
    ('T1','kabataş'):'X:Kabataş', ('F1','kabataş'):'X:Kabataş',
    ('M5','üsküdar'):'X:Üsküdar', ('MAR','üsküdar'):'X:Üsküdar',
    ('M4','kadıköy'):'X:Kadıköy', ('T3','kadıköy ido'):'X:Kadıköy',
    ('MAR','halkalı (marmaray)'):'X:Halkalı', ('HB','halkalı (bahçeşehir treni)'):'X:Halkalı',
    ('M4','ayrılık çeşmesi'):'X:Ayrılık Çeşmesi', ('MAR','ayrılık çeşmesi'):'X:Ayrılık Çeşmesi',
    ('M4','kozyatağı'):'X:Kozyatağı', ('M8','kozyatağı'):'X:Kozyatağı',
    ('M4','bostancı'):'X:Bostancı', ('M8','bostancı'):'X:Bostancı', ('MAR','bostancı (marmaray)'):'X:Bostancı',
    ('M4','bostancı'):'X:Bostancı', ('M8','bostancı'):'X:Bostancı', ('MAR','bostancı (marmaray)'):'X:Bostancı',
    ('M5','dudullu'):'X:Dudullu', ('M8','dudullu'):'X:Dudullu',
    ('M7','alibeyköy metro'):'X:Alibeyköy', ('T5','alibeyköy metro'):'X:Alibeyköy',
    ('T1','eminönü'):'X:Eminönü', ('T5','eminönü'):'X:Eminönü',
    ('T1','karaköy'):'X:Karaköy', ('TUNEL','karaköy'):'X:Karaköy',
    ('T1','sirkeci'):'X:Sirkeci', ('MAR','sirkeci'):'X:Sirkeci', ('SIRKECI','sirkeci'):'X:Sirkeci',
    ('M2','şişhane'):'X:Şişhane-Tünel', ('TUNEL','beyoğlu'):'X:Şişhane-Tünel', ('T2','beyoğlu tünel'):'X:Şişhane-Tünel',
    ('M2','seyrantepe'):'X:Seyrantepe', ('F3','seyrantepe'):'X:Seyrantepe',
    ('M6','boğaziçi üniversitesi/hisarüstü'):'X:Hisarüstü',
    ('TF2','eyüp teleferik'):'X:Eyüp Teleferik', ('T5','eyüp teleferik'):'X:Eyüp Teleferik',
}

# Canonical station-name cleanup before generating interchange IDs.
def norm(s):
    return ' '.join(str(s).strip().replace('I','ı').replace('İ','i').casefold().split())

rows=[]
CIRCULAR_ROUTES = {'T3'}
ROUTE_NOTES = {
    'M2': 'M2 ana hat sırası resmî Metro İstanbul istasyon listesine göre; Seyrantepe kolu ayrı route_id olarak modellenmiştir.',
    'M5': '2025 verisiyle zaman tutarlılığı için M5, 2025 sonunda hizmette olan Samandıra Merkez istasyonunda sonlandırılmıştır; 2026 Sultanbeyli uzatması dahil değildir.',
    'M3': 'M3 resmî hat sayfası: Bakırköy Sahil -> Kayaşehir Merkez; sıra ve istasyon adları resmî listeyle güncellendi.',
    'M9': 'M9 sırası resmî Metro İstanbul istasyon listesiyle güncellendi; Halkalı Caddesi 2025 verisindeki Halkalı (M9) kaydına eşleştirildi.',
    'T1': 'T1 istasyon sırası güncel resmî Metro İstanbul listesine göre; 2025 verisindeki Cami ve Keresteciler etiketleri eşleştirilmemiştir çünkü güncel resmî listede birebir karşılığı doğrulanamamıştır.',
    'T4': 'T4 istasyon sırası resmî Metro İstanbul istasyon listesine göre; 2025 veri adları eşleştirme için korunmuştur.',
    'T5': 'T5 istasyon sırası resmî Metro İstanbul listesine göre; 2025 veri adları eşleştirme için korunmuştur.',
    'T3': 'Metro İstanbul resmî listesi: 11 durak; ring hattı olarak son durak ilk durağa bağlanır.',
    'T2': 'İETT resmî T2 durak listesi; supplied passenger CSV has blank station names for this line, so no station passenger counts are mapped.',
    'F3': '2025 network map route represented topologically; supplied station-level CSV has no matching F3 line rows, so no passenger counts are mapped.'
}
for route_id,line_group,source_line,stations in ROUTES:
    for i,name in enumerate(stations,1):
        k=(line_group,norm(name))
        node_key=TRANSFER_KEYS.get(k, f'{line_group}:{norm(name)}')
        match_name = name
        # Preserve source-dataset aliases while using official public display labels.
        if (line_group, name) == ('M1','Bakırköy-İncirli'): match_name = 'Bakırköy'
        # Modern official labels are matched to equivalent labels in the 2025 station dataset where unambiguous.
        if (line_group, name) == ('T1','Fındıklı-Mimar Sinan Ü.'): match_name = 'Fındıklı'
        if (line_group, name) == ('T1','Beyazıt-Kapalıçarşı'): match_name = 'Beyazıt'
        if (line_group, name) == ('T1','Laleli-İstanbul Ü.'): match_name = 'Laleli'
        if (line_group, name) == ('T1','Çapa-Şehremini'): match_name = 'Çapa'
        if (line_group, name) == ('T1','Cevizlibağ-AÖY'): match_name = 'Atatürk Öğrenci Yurdu'
        if (line_group, name) == ('T1','Seyitnizam-Akşemsettin'): match_name = 'Akşemsettin'
        if (line_group, name) == ('M9','Halkalı Caddesi'): match_name = 'Halkalı (M9)'
        if (line_group, name) == ('M3','Bakırköy Sahil'): match_name = 'Bakırköy İDO'
        if (line_group, name) in {('M1','Ataköy-Şirinevler (M1)'), ('M9','Ataköy (M9)')}: match_name = 'Ataköy'
        if (line_group, name) in {('M4','Göztepe'), ('MAR','Göztepe (Marmaray)')}: match_name = 'Göztepe'
        if (line_group, name) in {('MAR','Pendik (Marmaray)'), ('M4','Pendik')}: match_name = 'Pendik'
        if (line_group, name) == ('MAR','Kartal (Marmaray)'): match_name = 'Kartal'
        if (line_group, name) == ('MAR','Halkalı (Marmaray)'): match_name = 'Halkalı'
        if (line_group, name) == ('HB','Halkalı (Bahçeşehir treni)'): match_name = 'Halkalı'
        if (line_group, name) == ('MAR','Yenimahalle (Marmaray)'): match_name = 'Yenimahalle'
        if (line_group, name) == ('MAR','Zeytinburnu'): match_name = 'Zeytinburnu'
        if (line_group, name) == ('M9','Ataköy (M9)'): match_name = 'Ataköy'
        if (line_group, name) == ('M8','Huzur (M8)'): match_name = 'Huzur'
        if (line_group, name) == ('MAR','Mustafa Kemal'): match_name = 'Mustafa Kemal'
        if (line_group, name) == ('M3','Kirazlı-Bağcılar'): match_name = 'Kirazlı'
        if (line_group, name) == ('M3','Başakşehir-Metrokent'): match_name = 'Metrokent'
        rows.append({'route_id':route_id,'line_group':line_group,'source_line':source_line,'station_order':i,'station_name':name,'match_station':match_name,'node_key':node_key,'is_circular':str(route_id in CIRCULAR_ROUTES).lower(),'route_note':ROUTE_NOTES.get(route_id,''),'topology_source':'Metro İstanbul resmî hat sayfaları / resmî ağ haritası; kaynak URL ve doğrulama notları docs/topology_validation.csv dosyasında','validation_status': ('OFFICIAL_ROUTE_REFERENCE_ALIAS_REVIEW_REQUIRED' if route_id in {'M1A','M1B','M2_MAIN','M2_BRANCH','M3','M4','M5','M6','M7','M8','M9','T1','T3','T4','T5','F1','F4','TF1','TF2'} else ('TOPOLOGY_ONLY_NO_PASSENGER_DATA' if route_id in {'F3','T2'} else 'MANUAL_ROUTE_REVIEW_REQUIRED'))})
with OUT.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# Explicit transfer links between separately named stations. These are edges, not
# merged nodes, because the two operator labels represent distinct station nodes.
TRANSFER_EDGES = [
    ('M2_MAIN', 'Vezneciler-İstanbul Üniversitesi', 'T1', 'Laleli-İstanbul Ü.',
     'M2–T1 walking interchange referenced by Metro Istanbul route information',
     'https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=T1'),
    ('M3', 'Özgürlük Meydanı', 'MARMARAY', 'Bakırköy (Marmaray)',
     'M3 official route information lists Marmaray transfer at Özgürlük Meydanı; represented as an explicit inter-station transfer edge',
     'https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=M3'),
    ('M9', 'Ataköy (M9)', 'MARMARAY', 'Ataköy',
     'M9 Ataköy and Marmaray Ataköy interchange represented as an explicit transfer edge',
     'https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=M9'),
]
lookup = {(r['route_id'], norm(r['station_name'])): r for r in rows}
transfer_rows = []
for route_a, station_a, route_b, station_b, reason, source_url in TRANSFER_EDGES:
    a = lookup.get((route_a, norm(station_a)))
    b = lookup.get((route_b, norm(station_b)))
    if not a or not b:
        raise ValueError(f'Transfer endpoint not found: {route_a}:{station_a} / {route_b}:{station_b}')
    if a['node_key'] == b['node_key']:
        raise ValueError(f'Transfer endpoints unexpectedly merged: {route_a}:{station_a} / {route_b}:{station_b}')
    transfer_rows.append({
        'node_u': a['node_key'], 'station_u': a['station_name'], 'route_u': route_a,
        'node_v': b['node_key'], 'station_v': b['station_name'], 'route_v': route_b,
        'edge_type': 'transfer', 'reason': reason, 'source_url': source_url,
    })
TRANSFER_OUT = ROOT / 'topology' / 'transfer_edges.csv'
with TRANSFER_OUT.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(transfer_rows[0].keys())); w.writeheader(); w.writerows(transfer_rows)
print(f'Wrote {len(rows)} topology station rows to {OUT}')
print(f'Wrote {len(transfer_rows)} explicit transfer edges to {TRANSFER_OUT}')
