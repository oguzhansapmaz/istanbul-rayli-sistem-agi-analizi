from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    ([sys.executable, str(ROOT / 'topology' / 'build_topology_csv.py')], 'Hat sıraları CSV taslağı'),
    ([sys.executable, '-m', 'src.prepare_data'], 'Ham veriyi doğrula ve hazırla'),
    ([sys.executable, '-m', 'src.build_network'], 'GraphML ağı oluştur'),
    ([sys.executable, '-m', 'src.analyze_network', '--null-models', '100', '--stability-seeds', '10'], 'Ağ analizleri, 100 null ağ ve Louvain kararlılığı'),
    ([sys.executable, '-m', 'src.make_visuals'], 'Grafikler ve A3 poster taslağı'),
    ([sys.executable, '-m', 'src.build_interactive'], 'Etkileşimli HTML'),
    ([sys.executable, '-m', 'src.make_report'], 'Rapor PDF taslağı'),
    ([sys.executable, '-m', 'src.make_presentation'], 'Sunum PPTX taslağı'),
    ([sys.executable, '-m', 'src.export_presentation_pdf'], 'Sunumu PDF biçiminde dışa aktar'),
    ([sys.executable, '-m', 'src.preflight_submission'], 'Teslim ön kontrol listesi'),
    ([sys.executable, '-m', 'src.quality_check'], 'Bilimsel ve dosya bütünlüğü kontrolü'),
]

def main() -> int:
    if not (ROOT / 'data' / 'raw').exists() or not list((ROOT / 'data' / 'raw').glob('*.csv')):
        print('HATA: data/raw altında kaynak CSV bulunamadı.')
        return 2
    for command, label in STEPS:
        print('\n' + '=' * 78 + f'\nBAŞLIYOR: {label}\n' + '=' * 78, flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode != 0:
            print(f'\nHATA: {label} başarısız oldu (kod {result.returncode}).')
            print('Komut çıktısını kopyalayıp hata ayıklama için sakla; çalıştırma otomatik durduruldu.')
            return result.returncode
    print('\nTamamlandı: çıktı taslakları outputs/ klasöründe üretildi.')
    print('UYARI: README.md içindeki topoloji, 500 düğüm şartı, Leiden ve powerlaw notlarını okuyun.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
