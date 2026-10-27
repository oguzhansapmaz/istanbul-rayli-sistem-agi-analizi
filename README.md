# Sosyal Ağ Analizi — İstanbul Raylı Sistem Yolcu Ağı

**Öğrenci:** Oğuzhan Sapmaz · **Ders:** Sosyal Ağ Analizi · **Veri yılı:** 2025

Bu depo, İBB Açık Veri Portalı'ndaki “Raylı Sistemler İstasyon Bazlı Yolcu ve Yolculuk Sayıları” CSV dosyasından istasyon düzeyinde bir ağ kurar. Düğüm istasyon düğümüdür; kenar aynı hat üzerindeki ardışık istasyon bağlantısı veya ayrı isimli istasyonlar arasında resmî olarak belirtilen aktarma bağlantısıdır. Açık aktarmalar `topology/transfer_edges.csv` içinde gerekçesi ve kaynak URL'siyle tutulur. Hat sırası `station_order` sayısal olarak işlenir; T3 ringine son-durak/ilk-durak kenarı eklenir.

## Önemli: bu bir ara teslim paketi, akademik olarak kapanmış final değildir

1. **500 düğüm şartı:** Ödev yönergesinin genel bölümünde en az 500 düğüm isteniyor; gerçek istasyon temelli bu grafikte daha az fiziksel istasyon bulunuyor. Yapay düğüm ekleme. Öğretim elemanından kişisel konunun bu kuraldan muaf olup olmadığını ya da geçerli kapsam genişletmesini yazılı olarak netleştir.
2. **OD matrisi yok:** CSV'de yolculukların başlangıç ve varış istasyonları yok. Bu yüzden kenar gücü iki uç istasyonun ortalama günlük yolcu aktivitesinden türetilen bir **vekil ölçüdür**, gözlenmiş istasyonlar arası yolcu akışı değildir. Kapanma senaryosu gerçek yolcu “yük kayması”nı değil, düğüm çıkarıldıktan sonraki topolojik merkeziyet/erişilebilirlik değişimini gösterir.
3. **Topoloji/alias doğrulaması:** `topology/line_stations.csv` resmî hat sayfalarına dayalı elle yapılandırılmıştır. Sayısal sıralama hatası düzeltilmiştir; seçili hat listeleri resmî referanslarla karşılaştırılmıştır. Yine de her isim aliası ve aktarma birleşimi kesinleşmiş değildir. `docs/topology_validation.csv`, `data/processed/station_alias_review.csv` ve `outputs/unmatched_source_stations.csv` dosyalarını kontrol et.
4. **2025 verisi zaman kapsamı:** M5, 2025 kapsamını korumak için Samandıra Merkez'de sonlandırılmıştır; 2026 uzatması 2025 grafiğine eklenmez.
5. **Eşleşmeyen kayıtlar:** 2025 CSV'sinde 135.783 kaynak kaydı vardır. Yeniden üretim sırasında son topoloji değişikliklerine göre eşleşme oranı `outputs/graph_metadata.json` içinden okunmalıdır. Kaynakta boş istasyon adı olan kayıtlar, tahminle istasyonlara bağlanmaz. T1 altındaki Cami/Keresteciler gibi eski adlar güvenilir karşılığı doğrulanmadan zorla eşleştirilmez.
6. **Power-law ve Leiden:** `outputs/analysis_summary.json` dosyasında durum `calculated` değilse bu yöntemler tamamlanmış sayılmaz. Power-law karşılaştırmalarında log-olabilirlik oranının işaretini ve p-değerini doğru yorumla; bir güç yasası modelinin kurulmuş olması tek başına derece dağılımının power-law olduğunu kanıtlamaz.
7. **Kaynak lisansı:** Veri portalı kayıt sayfasından gerçek lisans/attribution bilgisini kontrol edip rapora ekle. Yalnızca portal açık diye lisans koşullarının otomatik olarak doğrulandığını varsayma.

## Kaynaklar

- İBB Açık Veri Portalı: <https://data.ibb.gov.tr/>. Veri kümesi adı: **Raylı Sistemler İstasyon Bazlı Yolcu ve Yolculuk Sayıları** — 2025 CSV.
- Metro İstanbul resmî hat listeleri ve istasyon sayfaları: <https://www.metro.istanbul/Hatlarimiz/TumHatlarimiz>
- Resmî ağ haritaları: <https://www.metro.istanbul/YolcuHizmetleri/AgHaritalari>
- Kaynak URL'leri ve her hat için kalan kontroller: `docs/topology_validation.csv`.

## Veri indirme ve Windows'ta çalıştırma

İBB'nin CKAN API'sinden 2025 CSV kaynağını otomatik bulmayı denemek için proje kökünde `python -m src.fetch_data` komutunu çalıştırabilirsin. Betik mevcut CSV'nin üzerine yazmaz; üzerine yazma istenirse `python -m src.fetch_data --overwrite` gerekir. API 2025 kaynağını tekil olarak belirleyemezse kaynak korunur ve portaldan elle indirme yönergesi verir. İndirilen kaynak metaverisi `data/source_metadata_2025.json` içine yazılır; lisans ve atıf koşulları yine gözden geçirilmelidir.

Anaconda Prompt'ta mevcut `rayli-agi` ortamı varsa onu etkinleştir. Sonra proje klasörüne geç (yeni bir klasöre çıkardıysan yolu kendi klasörüne göre değiştir):

```bat
conda activate rayli-agi
cd /d "C:\Users\Oguzhan Sapmaz\Desktop\rayli-sistem-agi-proje-guncel"
python run_project.py
```

Bu zincir CSV denetimi, temizleme, ağ/GraphML, temel metrikler, merkeziyetler, Louvain ve Leiden (paket kuruluysa), 10 tohumlu kararlılık, 100 derece-koruyan null ağ, power-law/alternatif dağılım karşılaştırması, kapanma senaryosu, grafikler, HTML, PDF rapor ve PowerPoint'i üretir. Sunumdan sonra `src.export_presentation_pdf` çalışarak `outputs/sunum_TASLAK.pdf` dosyasını LibreOffice/PowerPoint üzerinden güncellemeyi dener; dönüştürücü yoksa PowerPoint içinden PDF dışa aktarmak gerekir. Son adımlar `outputs/submission_preflight.txt` ve `outputs/quality_check.txt` kontrol raporlarını üretir. Komutun sonunda `outputs/analysis_summary.json` içinde Leiden ve powerlaw durumlarını kontrol et. Kod zincirinin çalışması öğretim elemanının 500 düğüm şartını çözmez; bu ayrı bir akademik kapsam sorusudur.

Yeni bir ortam gerekiyorsa proje kökünde:

```bat
conda env create -f environment.yml
conda activate rayli-agi
python run_project.py
```

`environment.yml` içinde `powerlaw` pip üzerinden kurulur. Windows Uygulama Denetimi bir `.pyd`/DLL bileşenini engellerse güvenlik ayarını kapatma veya rasgele DLL indirme; raporda yöntemin çalışmadığını belirt ve kurumun IT/yetkili yönergelerini izle.

## Üretilen temel dosyalar

- `topology/transfer_edges.csv` — açık aktarma bağlantıları, gerekçe ve resmî kaynak URL'si
- `outputs/istanbul_rail_2025.graphml` — GraphML ağı
- `outputs/nodes.csv`, `outputs/edges.csv` — düğüm/kenar tabloları
- `outputs/centrality_and_communities.csv` — merkeziyetler ve topluluklar
- `outputs/centrality_spearman_correlations.csv` — merkeziyet ölçüleri arası Spearman rho
- `outputs/community_profile.csv` — topluluk boyutu, baskın hatları ve yorum amaçlı aday isimleri (insan tarafından gözden geçirilmeli)
- `notebooks/01_network_analysis.ipynb` — çıktı tablolarını, ağ metriklerini ve yöntem durumlarını inceleyen Jupyter defteri
- `src/fetch_data.py` — İBB CKAN API üzerinden 2025 CSV kaynağını arayıp indirmeyi deneyen betik
- `docs/data_dictionary.csv` — kaynak ve türetilmiş alanların sözlüğü, dönüşüm ve veri kalitesi notları
- `outputs/community_stability_louvain.csv` ve `outputs/community_stability_leiden.csv` — 10 tohumlu kararlılık (Leiden dosyası yalnızca paket yüklüyse)
- `outputs/null_model_results.csv` — null model tekrarları
- `outputs/analysis_summary.json` — tüm önemli yöntem durumları, bulgular ve sınırlılıklar
- `outputs/rapor_TASLAK.pdf` — 6–10 sayfalık rapor taslağı
- `outputs/ag_posteri_A3_TASLAK.pdf` — A3 poster taslağı
- `outputs/sunum_TASLAK.pptx` — 8–10 slaytlık sunum taslağı
- `outputs/sunum_TASLAK.pdf` — sunumun PDF çıktısı (yönergedeki PDF teslimine uygun; son PPTX yeniden üretilirse PDF'yi de güncelle)
- `outputs/submission_preflight.txt` — dosya varlığı ve teslim öncesi akademik/manuel kontroller
- `outputs/quality_check.txt` ve `outputs/quality_check.json` — GraphML/CSV tutarlılığı, null model bütünlüğü, PDF/PPTX boyutları ve açık riskler için otomatik kalite kontrolü
- `web/interactive_network.html` — arama, düğüm detay paneli ve topluluk filtresi olan ağ

Etkileşimli ağ Cytoscape.js'i CDN'den yüklediğinden tarayıcıda internet bağlantısı ister. Portföye eklemeden önce arama, düğüme tıklama ve topluluk filtresini test et.

## CV için tek cümlelik proje özeti

2025 İBB istasyon bazlı yolcu verisini temizleyip İstanbul raylı sistemleri için tekrarlanabilir bir ağ modeli oluşturdum; merkeziyet, topluluk, derece-koruyan null model ve istasyon düğümü çıkarma senaryolarını hesaplayarak bulguları sınırlılıklarıyla raporladım.

## Akademik dürüstlük ve AI beyanı

Kod iskeleti, veri denetimi, yöntem akışı ve rapor/sunum taslaklarının hazırlanmasında yapay zekâ desteği kullanılmıştır. Öğrenci; veri kaynağını, topolojiyi, istasyon aliaslarını, hesaplanan çıktıları ve yöntemlerin anlamını doğrulamalı; açıklayamadığı veya hesaplanmamış analizleri tamamlanmış gibi sunmamalıdır.
