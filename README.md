# Sosyal Ağ Analizi — İstanbul Raylı Sistem Yolcu Ağı

**Veri yılı:** 2025  
**Proje alanı:** Ağ Bilimi, Veri Analitiği ve Graf Teorisi

Bu proje, İstanbul Büyükşehir Belediyesi Açık Veri Portalı'nda yayımlanan **Raylı Sistemler İstasyon Bazlı Yolcu ve Yolculuk Sayıları** veri setini kullanarak İstanbul raylı sistemlerinin istasyon düzeyinde bir ağ modelini oluşturur.

Ağda her düğüm bir istasyonu temsil eder. Kenarlar, aynı hat üzerindeki ardışık istasyon bağlantılarını veya resmî kaynaklarla doğrulanan aktarma bağlantılarını ifade eder. Açık aktarma bağlantıları, gerekçeleri ve kaynak URL'leriyle `topology/transfer_edges.csv` dosyasında tutulur. İstasyon sıralamaları sayısal olarak işlenir ve T3 ring hattının döngüsel yapısı modele dahil edilir.

## Proje kapsamı ve metodolojik sınırlılıklar

### 1. Ağın kapsamı

Model, gerçek istasyonlar ve doğrulanabilir bağlantılar üzerinden oluşturulmuştur. Bu nedenle ağın düğüm sayısı, veri setinde temsil edilen ve topolojiyle eşleştirilebilen istasyonlarla sınırlıdır. Yapay düğümler eklenmemiştir. Ağın kapsamı genişletilecekse yalnızca doğrulanabilir yeni istasyonlar ve bağlantılar kullanılmalıdır.

### 2. Yolcu akışı ve kenar ağırlıkları

Kaynak CSV dosyasında yolculukların başlangıç ve varış istasyonlarını gösteren bir OD (Origin–Destination) matrisi bulunmamaktadır. Bu nedenle kenar ağırlıkları, bağlantının iki ucundaki istasyonların ortalama günlük yolcu aktivitesinden türetilen bir vekil ölçü olarak hesaplanır.

Bu değerler, istasyonlar arasındaki gözlenmiş yolcu akışları olarak yorumlanmamalıdır. İstasyon kapatma senaryoları da gerçek yolcu yükünün alternatif hatlara dağılımını değil, düğüm çıkarılmasının ağın topolojik özellikleri, merkeziyet ölçüleri ve erişilebilirliği üzerindeki etkilerini inceler.

### 3. Topoloji ve istasyon adı eşleştirmeleri

`topology/line_stations.csv` dosyası, resmî hat bilgileri temel alınarak hazırlanmıştır. İstasyon sıralamaları sayısal olarak işlenmiş ve seçili hat listeleri resmî referanslarla karşılaştırılmıştır.

Bununla birlikte, bütün istasyon adı varyasyonları ve aktarma eşleştirmeleri kesin olarak doğrulanmış kabul edilmemelidir. İlgili kontroller için şu dosyalar kullanılmalıdır:

- `docs/topology_validation.csv`
- `data/processed/station_alias_review.csv`
- `outputs/unmatched_source_stations.csv`

Belirsiz istasyon adları, yeterli kanıt olmadan başka istasyonlarla eşleştirilmez.

### 4. Veri yılı ve kapsamı

Analiz, 2025 veri kapsamını esas alır. M5 hattı, ilgili dönemin kapsamını korumak amacıyla Samandıra Merkez istasyonunda sonlandırılır; 2026 yılında gerçekleşen uzatmalar 2025 ağına dahil edilmez.

### 5. Veri kalitesi ve eşleşme oranı

2025 kaynak CSV dosyasında 135.783 kayıt bulunmaktadır. İşleme aşamalarında eşleşen ve eşleşmeyen kayıtların oranı, son topoloji yapılandırmasına göre `outputs/graph_metadata.json` dosyasından kontrol edilmelidir.

İstasyon adı boş olan kayıtlar tahmin yoluyla istasyonlara bağlanmaz. T1 hattındaki Cami ve Keresteciler gibi eski adlar da güvenilir bir karşılık doğrulanmadan zorla eşleştirilmez.

### 6. İstatistiksel analiz ve topluluk tespiti

Proje kapsamında merkeziyet ölçüleri, topluluk tespiti, derece-koruyan null modeller ve derece dağılımı analizleri ele alınır.

Power-law ve Leiden analizlerinin tamamlanma durumu `outputs/analysis_summary.json` dosyasından kontrol edilmelidir. Bir güç yasası modelinin kurulması, derece dağılımının kesin olarak güç yasasına uyduğunu tek başına göstermez. Alternatif dağılımlarla karşılaştırmalar, log-olabilirlik oranları ve p-değerleri birlikte değerlendirilmelidir.

### 7. Veri lisansı ve atıf

Veri setinin lisans ve atıf koşulları, İBB Açık Veri Portalı'ndaki ilgili kayıt sayfasından doğrulanmalıdır. Verinin açık erişimli olması, kullanım koşullarının otomatik olarak doğrulandığı anlamına gelmez.

## Veri kaynakları

- **İBB Açık Veri Portalı:** https://data.ibb.gov.tr/
  - Veri seti: *Raylı Sistemler İstasyon Bazlı Yolcu ve Yolculuk Sayıları*
  - Kullanılan dönem: 2025
- **Metro İstanbul — Hatlar:** https://www.metro.istanbul/Hatlarimiz/TumHatlarimiz
- **Metro İstanbul — Ağ Haritaları:** https://www.metro.istanbul/YolcuHizmetleri/AgHaritalari
- Hat bazlı doğrulama kaynakları ve kontroller: `docs/topology_validation.csv`

## Kurulum ve çalıştırma

Proje, Python ve Conda tabanlı bir ortamda çalıştırılabilir. Windows üzerinde aşağıdaki adımlar izlenebilir.

### Mevcut ortamı kullanma

Proje dizininde terminal açın ve mevcut `rayli-agi` ortamını etkinleştirin:

```bat
conda activate rayli-agi
cd /d "PROJE_DIZINI"
python run_project.py
```

`PROJE_DIZINI` ifadesini projenin bulunduğu yerel klasörün yolu ile değiştirin.

### Yeni ortam oluşturma

Proje kök dizininde aşağıdaki komutlar çalıştırılabilir:

```bat
conda env create -f environment.yml
conda activate rayli-agi
python run_project.py
```

Bağımlılıklar arasında `powerlaw` paketi de bulunmaktadır ve bu paket `environment.yml` üzerinden pip kullanılarak kurulur.

### Veri indirme

İBB CKAN API üzerinden 2025 CSV kaynağını otomatik bulmayı denemek için:

```bat
python -m src.fetch_data
```

Mevcut kaynak dosyasının üzerine yazılması gerekiyorsa:

```bat
python -m src.fetch_data --overwrite
```

Betik, 2025 kaynağını API üzerinden tekil olarak belirleyemezse mevcut veriyi korur ve manuel indirme yönergesi verir. Kaynak metaverisi `data/source_metadata_2025.json` dosyasına yazılır. Lisans ve atıf koşulları ayrıca kontrol edilmelidir.

## Analiz işlem hattı

`python run_project.py` komutu, yapılandırmaya ve kurulu bağımlılıklara bağlı olarak aşağıdaki işlemleri yürütür:

1. Kaynak CSV dosyasının denetlenmesi ve temizlenmesi
2. İstasyonların ve bağlantıların ağ modeline dönüştürülmesi
3. GraphML, düğüm ve kenar dosyalarının oluşturulması
4. Temel ağ metrikleri ve merkeziyet ölçülerinin hesaplanması
5. Louvain ve uygun bağımlılıklar mevcutsa Leiden topluluk tespiti
6. On farklı tohumla topluluk kararlılığı analizi
7. Yüz tekrar içeren derece-koruyan null model analizi
8. Power-law ve alternatif derece dağılımlarının karşılaştırılması
9. İstasyon düğümü çıkarma senaryosunun değerlendirilmesi
10. Grafiklerin, etkileşimli ağın, PDF raporunun ve PowerPoint sunumunun oluşturulması
11. Otomatik kalite kontrollerinin ve son kontrol raporlarının hazırlanması

İşlem hattının çalışması, bütün analizlerin başarıyla tamamlandığını veya bütün metodolojik sınırlılıkların giderildiğini tek başına garanti etmez. Yöntem durumları ve kalite kontrol çıktıları ayrıca incelenmelidir.

### Sunumun PDF çıktısı

İşlem hattı, `src.export_presentation_pdf` üzerinden `outputs/sunum_TASLAK.pdf` dosyasını LibreOffice veya PowerPoint kullanarak güncellemeyi deneyebilir. Uygun bir dönüştürücü yoksa sunum, PowerPoint üzerinden PDF biçiminde dışa aktarılmalıdır. PPTX dosyası yeniden üretildiğinde PDF çıktısı da güncellenmelidir.

Windows Uygulama Denetimi bir `.pyd` veya DLL bileşenini engellerse güvenlik ayarlarını devre dışı bırakmak ya da bilinmeyen kaynaklardan DLL indirmek yerine yetkili teknik destek yönergeleri izlenmelidir.

## Üretilen dosyalar

### Ağ modeli ve veri tabloları

| Dosya | Açıklama |
|---|---|
| `topology/transfer_edges.csv` | Aktarma bağlantıları, gerekçeler ve resmî kaynaklar |
| `outputs/istanbul_rail_2025.graphml` | GraphML ağ modeli |
| `outputs/nodes.csv` | Düğüm tablosu |
| `outputs/edges.csv` | Kenar tablosu |
| `docs/data_dictionary.csv` | Alan tanımları, dönüşümler ve veri kalitesi notları |
| `outputs/graph_metadata.json` | Ağ metaverisi ve eşleşme bilgileri |

### Ağ analizi ve doğrulama

| Dosya | Açıklama |
|---|---|
| `outputs/centrality_and_communities.csv` | Merkeziyet ölçüleri ve topluluk atamaları |
| `outputs/centrality_spearman_correlations.csv` | Merkeziyet ölçüleri arasındaki Spearman korelasyonları |
| `outputs/community_profile.csv` | Topluluk boyutları, baskın hatlar ve incelenmesi gereken aday adlar |
| `outputs/community_stability_louvain.csv` | Louvain için on tohumlu kararlılık analizi |
| `outputs/community_stability_leiden.csv` | Leiden için kararlılık analizi; bağımlılığın kullanılabilirliğine bağlıdır |
| `outputs/null_model_results.csv` | Null model tekrarlarının sonuçları |
| `outputs/analysis_summary.json` | Yöntem durumları, bulgular ve sınırlılıklar |
| `outputs/unmatched_source_stations.csv` | Eşleşmeyen kaynak istasyon kayıtları |
| `data/processed/station_alias_review.csv` | İstasyon adı eşleştirmelerinin incelenmesi |
| `docs/topology_validation.csv` | Topoloji doğrulama kontrolleri |

### Raporlama ve görselleştirme

| Dosya | Açıklama |
|---|---|
| `notebooks/01_network_analysis.ipynb` | Çıktı tablolarını ve ağ analizlerini inceleyen Jupyter defteri |
| `outputs/rapor_TASLAK.pdf` | 6–10 sayfalık rapor taslağı |
| `outputs/ag_posteri_A3_TASLAK.pdf` | A3 poster taslağı |
| `outputs/sunum_TASLAK.pptx` | 8–10 slaytlık sunum taslağı |
| `outputs/sunum_TASLAK.pdf` | Sunumun PDF çıktısı |
| `outputs/submission_preflight.txt` | Dosya varlığı ve son kontroller |
| `outputs/quality_check.txt` | Otomatik kalite kontrol raporu |
| `outputs/quality_check.json` | Yapısal kalite kontrollerinin makinece okunabilir çıktısı |
| `web/interactive_network.html` | Etkileşimli ağ görselleştirmesi |

Etkileşimli ağ, Cytoscape.js kütüphanesini CDN üzerinden yüklediği için tarayıcıda internet bağlantısı gerektirir. Ağ araması, düğüm detay paneli ve topluluk filtresi kullanılmadan önce test edilmelidir.

## Proje özeti

2025 yılı İstanbul raylı sistem istasyon verileri temizlenerek tekrarlanabilir bir ağ modeli oluşturulmuş; merkeziyet ölçüleri, topluluk yapıları, derece-koruyan null modeller ve istasyon çıkarma senaryoları analiz edilmiştir. Bulgular, veri kapsamı ve yöntemsel sınırlılıklar dikkate alınarak değerlendirilmiştir.

## Yapay zekâ desteği ve doğrulama yaklaşımı

Kod iskeletinin, veri denetiminin, analiz işlem hattının ve raporlama taslaklarının hazırlanmasında yapay zekâ desteğinden yararlanılmıştır. Üretilen sonuçlar, kaynak veriler ve topoloji eşleştirmeleri üzerinden doğrulanmalıdır. Hesaplanmamış analizler tamamlanmış gibi sunulmamalı; yöntemlerin varsayımları ve sınırlılıkları açıkça belirtilmelidir.
