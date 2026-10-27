# Son kontrol — 27 Ekim 2026

Bu depo tekrar çalıştırılabilir bir proje taslağıdır. **Kod zincirinin çalışması ile ödevin akademik olarak tüm gereksinimleri karşıladığı aynı şey değildir.**

## Bu paket hazırlanırken yapılanlar

- [x] Kaynak CSV `;` ayıracı ile okunuyor; ham veri değiştirilmeden saklanıyor.
- [x] Kaynak denetimi, tarih/koordinat temizliği, istasyon gün özeti ve alias inceleme tablosu oluşturuluyor.
- [x] Hat sırası sayısal olarak sıralanacak şekilde düzeltildi (önceki metin sıralaması 1, 10, 11, 2 gibi hatalı sıra üretebilirdi).
- [x] T3 için halka kapanışı (son durak → ilk durak) eklendi.
- [x] İsimleri farklı olduğu için tek düğümde birleştirilmemesi gereken üç resmî aktarma bağlantısı ayrı kenarlar olarak eklendi: M2 Vezneciler–T1 Laleli, M3 Özgürlük Meydanı–Marmaray Bakırköy ve M9 Ataköy–Marmaray Ataköy. Bunlar `topology/transfer_edges.csv` içinde kaynak URL'siyle listelenir.
- [x] Bazı resmî hat sayfalarında bulunan aktarma bilgileriyle anahtarlar güncellendi; kalan route/alias kontrolleri `topology_validation.csv` içinde açık bırakıldı.
- [x] GraphML, düğüm/kenar CSV ve eşleşmeyen kaynak istasyon listesi üretildi.
- [x] Mevcut yerel Python ortamında temel merkeziyetler/current-flow, Louvain, 10 tohumlu Louvain kararlılığı, null model, kapanma senaryosu, grafikler, HTML, PDF ve PPTX zinciri çalıştırıldı.
- [x] Null model gözlenen ve rastgele ağları aynı en büyük bağlı bileşen üzerinde karşılaştıracak ve modülerliği iki tarafta da ağırlıksız hesaplayacak şekilde düzeltildi; bağlı derece-koruyan kenar takasları kullanılır.
- [x] Tam Spearman rho çifti listesi `outputs/centrality_spearman_correlations.csv` dosyasına yazılıyor.
- [x] Kaynak ve türetilmiş sütunlar, ölçü/birim varsayımları ve veri kalitesi notları `docs/data_dictionary.csv` içine eklendi; lisans metaverisi hâlâ portalda doğrulanmalı.
- [x] Topluluk raporlaması gerçek Louvain kimlikleriyle boyuta göre sıralanıyor; aday adlar yorum amaçlıdır ve insan kontrolü gerektirir.
- [x] Rapor ve sunumdaki Leiden/powerlaw metinleri artık sonuç durumuna göre dinamik yazılıyor.
- [x] Sunum için PDF dışa aktarma adımı eklendi; LibreOffice/PowerPoint otomatik dönüştürücü yoksa PowerPoint'ten elle PDF dışa aktarmak gerekir.
- [x] `outputs/submission_preflight.txt` dosya kontrollerini ve teslim öncesi akademik blokları listeler.

## Son yerel testte çıkan sayılar

Bu değerler **mevcut topology CSV'si ile bu çalışma ortamında** hesaplandı; kullanıcı Windows ortamında `python run_project.py` yeniden çalıştırılmalıdır.

- 2025 kaynak: 135.783 kayıt, 11 sütun, 23 hat; tüm 12 ay bulunuyor.
- İstasyon adı boş: 728 kayıt; boylam/ enlem alanı başına 23.858 boş kayıt.
- Son ağ: **269 düğüm, 289 kenar, 2 bağlı bileşen**; bileşen büyüklükleri 267 ve 2. Üç ayrı isimli aktarma kenarı eklendi.
- En büyük bileşen: 267 düğüm, 288 kenar; ortalama en kısa yol 16,182; çap 51; yoğunluk 0,00802; derece assortativity 0,08757.
- Louvain: 20 topluluk; ağırlıklı Q = 0,8131. 10 tohum kararlılığı: ortalama ARI = 0,9438, NMI = 0,9799.
- Null model: 100/100 benzersiz, bağlı ve derece-dizisini koruyan ağ doğrulandı. Aynı en büyük bağlı bileşende z-skorları: kümelenme −0,454; ortalama yol +3,227; ağırlıksız modülerlik +4,287. Ortalama yol ve modülerlik derece-koruyan null ağa göre daha yüksek; yorum topoloji taslağıyla sınırlıdır.
- Kapanma adayı: Sirkeci; bileşen sayısı 2→3, en büyük bileşen 267→177; bağlı düğüm çifti oranı 0,9852→0,5448 ve global efficiency 0,0925→0,0654. Bu, istasyon ve tüm incident kenarlarının silindiği idealize topolojik senaryodur; gerçek yolcu akışı değildir.
- Yerel oluşturma ortamında igraph/leidenalg/powerlaw yüklü olmadığından bu üretimde Leiden ve power-law **hesaplanmadı**. Kullanıcının Anaconda ortamında daha önce her ikisi çalışmıştı; güncel topolojiyle yeniden koşturulup `outputs/analysis_summary.json` kontrol edilmeli.

## Teslimden önce kapanması gereken akademik bloklar

- [ ] `docs/topology_validation.csv` kaynak referansları, `topology/line_stations.csv` satırları ve `topology/transfer_edges.csv` transfer kenarları tek tek gözden geçirilerek kalan istasyon sırası/transfer/alias doğrulaması tamamlandı.
- [ ] `data/processed/station_alias_review.csv` ve `outputs/unmatched_source_stations.csv` insan tarafından kontrol edildi; belirsiz eski istasyon isimleri zorla eşleştirilmedi.
- [ ] Öğretim elemanından yönergede belirtilen **500 düğüm** alt sınırının bu istasyon temelli kişisel konuya nasıl uygulanacağı yazılı olarak netleştirildi. Bu, paket içinden öğrenci/öğretim elemanı dışında tamamlanamaz. Düğüm uydurulmadı.
- [ ] Kaynağın lisansı/atıf koşulu resmî portalda doğrulanıp rapora yazıldı.
- [ ] Kullanıcı Windows ortamında güncel kodla bütün zinciri çalıştırdı; `analysis_summary.json` içinde Leiden ve powerlaw için `calculated` durumu doğrulandı (veya engel sebebi belgelenip yetkiliyle çözüldü).
- [ ] Power-law/exponential/lognormal karşılaştırmalarının işaretleri ve p-değerleri doğru yorumlandı; güç yasasının desteklendiği yönünde otomatik iddia kurulmadı.
- [ ] Etkileşimli HTML'de arama, tıklama detay paneli ve topluluk filtresi test edildi ve portföy projesine gömüldü.
- [ ] Poster/rapor/sunum son güncel çıktılarla yenilendi; 8–10 slayt/6 dakika sunum provası yapıldı.
- [ ] Öğrenci tüm metrikleri ve kısıtları kendi cümleleriyle açıklayabiliyor.

## Kapsam ve yorum notu

2025 CSV'si istasyon istatistikleri içerir; başlangıç-varış (OD) matrisi içermez. Kenar gücü iki uç düğümün ortalama günlük yolcu aktivitesinden türetilen proxy'dir. Dolayısıyla kapanma sonrası “yük kayması” iddiası kurulamaz; yalnızca betweenness, yol uzunluğu ve bağlı bileşen değişimi gibi topolojik sonuçlar raporlanabilir.
