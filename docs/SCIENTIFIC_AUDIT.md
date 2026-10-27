# Bilimsel ve teknik son kontrol — 27 Ekim 2026

## Kısa karar

**Teknik bütünlük testleri geçti; akademik teslim için uyarılar sürüyor.** Bu rapor, dosya ve kod testlerini bilimsel/topoloji onayıyla karıştırmaz. `outputs/quality_check.txt` otomatik testlerin güncel özetidir.

## Veri denetimi

- Kaynak: İBB Açık Veri Portalı, “Raylı Sistemler İstasyon Bazlı Yolcu ve Yolculuk Sayıları”, 2025 CSV.
- 135.783 satır, 11 kaynak sütun, 23 kaynak hat değeri; 2025'in 12 ayı mevcut.
- 728 kayıt istasyon adı olmadan; longitude ve latitude sütunlarının her birinde 23.858 eksik kayıt var.
- Sayısal yolcu/geçiş alanlarında ayrıştırma hatası ve tam yinelenen satır tespit edilmedi.
- Ağ eşleştirmesi: 134.323/135.783 kayıt (%98,92). 1.460 kayıt eşleşmedi: boş istasyon adları, 2025 T1 verisindeki Cami/Keresteciler adları ve iki ayrı istasyon alias kaydı. Bu adlar tahminle eşleştirilmedi.
- Kaynakta başlangıç-varış (OD) yolculuk matrisi yok. Kenar gücü, uç istasyonların ortalama günlük yolcu aktivitesinden türetilen bir vekildir; istasyonlar arası ölçülmüş akış değildir. Olası giriş/çıkış veya hatlar arası çift sayım da kaynak metadata'sıyla doğrulanmalı.

## Ağ ve topoloji

- Ağ: 269 düğüm, 289 kenar; bileşen boyutları 267 ve 2. En büyük bileşende 267 düğüm ve 288 kenar.
- Yoğunluk 0,00802; en büyük bağlı bileşende ortalama en kısa yol 16,182 ve çap 51; tüm ağ için ortalama kümelenme 0; derece assortativity 0,08757.
- Hat sıraları sayısal olarak sıralanır ve her route için benzersizdir. T3 ringinin kapanış kenarı vardır.
- Üç ayrı isimli transfer bağlantısı açık kenar olarak modellendi: M2 Vezneciler–T1 Laleli, M3 Özgürlük Meydanı–Marmaray Bakırköy ve M9 Ataköy–Marmaray Ataköy. Kaynak sayfaları: [M2](https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=M2), [T1](https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=T1), [M3](https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=M3), [M9](https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=M9).
- Spot-check: M1A resmî sayfasındaki 18 duraklı sıra ile M3 resmî sayfasındaki 20 duraklı sıra proje topolojisiyle karşılaştırıldı. M3 sayfası Yıldıztepe'nin 8 Ekim 2025'te açıldığını belirtiyor; bu nedenle grafiğin yıl sonu topolojisi olarak yorumlanması gerekir. M5, 2025 verisi için Samandıra Merkez'de bitirilmiştir; Sultanbeyli uzatması 22 Mayıs 2026'da açılmıştır ([M1A](https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=M1A), [M3](https://www.metro.istanbul/Hatlarimiz/HatDetay?hat=M3), [M5 2026 uzatma duyurusu](https://www.metro.istanbul/duyuru/detay/m5-uskudar-samandira-metro-hattinin-sultanbeyli-etabi-hizmete-aciliyor-210526)).
- Bu spot-check tam bir tüm-hat doğrulaması değildir. `docs/topology_validation.csv`, `topology/line_stations.csv`, `topology/transfer_edges.csv`, `data/processed/station_alias_review.csv` ve `outputs/unmatched_source_stations.csv` insan tarafından son kez gözden geçirilmelidir.

## Merkeziyet, topluluk ve null model

- Ağırlıksız/ağırlıklı betweenness, degree, closeness, eigenvector, PageRank, en büyük bağlı bileşen üzerinde current-flow betweenness ve Spearman rho hesaplandı. Spearman p-değerleri bu sürümde üretilmiyor; rho sıralama ilişkisini özetliyor.
- Louvain: 20 topluluk; ağırlıklı modülerlik Q=0,8131. 10 farklı tohumda ortalama ARI=0,9438, NMI=0,9799.
- Null model: aynı en büyük bağlı bileşen üzerinde 100 benzersiz, bağlı ve derece dizisini koruyan random graph doğrulandı. Gözlenen ve null metrikleri aynı düğüm kümesiyle karşılaştırılır; modülerlik iki tarafta da ağırlıksızdır.
  - Kümelenme: gözlenen 0,0000; null ortalaması 0,0015; z=−0,454.
  - Ortalama en kısa yol: gözlenen 16,1821; null ortalaması 13,3655; z=+3,227; üst-kuyruk ampirik p≈0,0198.
  - Ağırlıksız Louvain modülerliği: gözlenen 0,8436; null ortalaması 0,8204; z=+4,287; üst-kuyruk ampirik p≈0,0099.
- Bu z-skorları mevcut elle derlenmiş topolojiye bağlıdır; tam transfer doğrulaması yapılmadan şehir sistemi hakkında kesin çıkarım olarak genellenmemelidir.
- **Leiden ve power-law bu çalışma ortamında hesaplanmadı** (`igraph` ve `powerlaw` paketleri bulunmuyor). Güncel Windows çalıştırmasında `outputs/analysis_summary.json` içinde `calculated` görünmeden bu iki yöntemi tamamlandı diye sunma. Güvenlik yazılımı bir DLL/.pyd dosyasını engellerse güvenlik ayarını kapatma; kurum/IT yönergesini izle.

## Kapanma senaryosu — doğru yorum

- En yüksek ağırlıksız betweenness adayı Sirkeci.
- Düğüm ve ona bağlı tüm kenarlar silindiğinde bileşen sayısı 2→3; en büyük bileşen 267→177 düğüm.
- Aynı bağlı bileşende kalabilen düğüm çifti oranı 0,9852→0,5448; ağırlıksız global efficiency 0,0925→0,0654.
- Bu, **istasyon düğümünün ve bütün incident kenarlarının silindiği idealize topolojik testtir**. Gerçek işletmede trenler istasyonda durmadan geçebilir; bu model bunu temsil etmez. OD matrisi olmadığından gerçek yolcu talebinin hangi hatta ne kadar kayacağı hesaplanamaz.

## Otomatik bütünlük testleri

`outputs/quality_check.txt` son çalıştırmada `PASS_WITH_WARNINGS` verdi:

- GraphML, düğüm CSV, kenar CSV ve analiz özeti sayımları tutarlı.
- Self-loop yok; bütün kenar uçları grafikte mevcut.
- Hat sıraları sayısal/sıralı/benzersiz; 3 transfer kenarı GraphML'de var.
- Merkeziyet tablosu düğüm sayısıyla eşleşiyor ve temel değerlerde boş hücre yok.
- 100 null model örneği tamam; her biri bağlı, derece dizisi korunmuş ve edge-set hash'leri benzersiz.
- Jupyter defteri parse oluyor ve kod hücreleri derleniyor.
- Rapor 7 sayfa, poster gerçek A3 landscape boyutunda, sunum 9 slayt ve sunum PDF'si 9 sayfa.

## Teslimden önce hâlâ gerekli olanlar

1. Yönergedeki **en az 500 düğüm** şartı genel kurala göre geçerli; kişisel kartta açık istisna yazmıyor. Gerçek istasyon grafiği 269 düğüm. Yapay düğüm eklenmemeli; öğretim elemanından kapsam/istisna yazılı netleştirilmeli.
2. Leiden ve power-law'ın kullanıcının Windows ortamında güncel topolojiyle hesaplanması veya hesaplanamama sebebinin belgelenmesi.
3. İBB lisans/atıf metaverisinin portal kaydından ve `https://data.ibb.gov.tr/license` adresinden okunup rapora yazılması. Bu kontrol sırasında portal sayfası zaman aşımına uğradığı için lisansın tam koşulları bağımsız olarak doğrulanmadı.
4. HTML'nin tarayıcıda arama, düğüm tıklama ve topluluk filtresiyle test edilmesi; sonra öğrenci portföyüne gömülmesi.
5. Öğrencinin tüm metrikleri, model varsayımlarını ve sınırlılıkları kendi cümleleriyle açıklayabilmesi.

**Son karar:** Teknik üretim ve otomatik dosya kontrolleri başarılı; bu hâliyle “%100 akademik olarak tamamlandı” denemez. Başlıca açık bloklar 500 düğüm şartı, tam topoloji/alias doğrulaması, lisans doğrulaması ve Leiden/power-law hesap durumudur.
