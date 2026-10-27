from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / 'data' / 'raw'
DATASET_TITLE = 'Raylı Sistemler İstasyon Bazlı Yolcu ve Yolculuk Sayıları'
API_BASE = 'https://data.ibb.gov.tr/api/3/action'


def api_get(action: str, params: dict) -> dict:
    url = f'{API_BASE}/{action}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'rayli-sistem-agi-student-project/1.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode('utf-8'))
    if not payload.get('success'):
        raise RuntimeError(f'CKAN API {action} isteği başarısız oldu.')
    return payload['result']


def safe_filename(name: str) -> str:
    name = name.strip() or '2025-rail-passenger-data.csv'
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '-', name)
    if not name.lower().endswith('.csv'):
        name += '.csv'
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description='İBB CKAN API üzerinden 2025 raylı sistem istasyon verisini bulup indirmeyi dener.')
    parser.add_argument('--overwrite', action='store_true', help='aynı adlı mevcut CSV dosyasının üzerine yazmaya izin ver')
    args = parser.parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    try:
        result = api_get('package_search', {'q': DATASET_TITLE, 'rows': 50})
    except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        print(f'İBB CKAN API sorgulanamadı: {exc}')
        print('Mevcut kaynak dosyanız korunmuştur. CSV dosyasını portal sayfasından elle indirin: https://data.ibb.gov.tr/')
        return 2

    packages = result.get('results', [])
    scored = []
    for pkg in packages:
        title = str(pkg.get('title', ''))
        search_blob = (title + ' ' + str(pkg.get('name', '')) + ' ' + str(pkg.get('notes', ''))).casefold()
        if ('istasyon bazlı yolcu' in search_blob or 'istasyon-bazli-yolcu' in search_blob) and 'raylı sistem' in search_blob:
            scored.append(pkg)
    if not scored:
        print('Arama sonucu içinde kaynak başlığıyla yeterince eşleşen bir veri kümesi bulunamadı.')
        print('Mevcut kaynak dosyanız korunmuştur. Portalda “Raylı Sistemler İstasyon Bazlı Yolcu ve Yolculuk Sayıları” kaydını açıp 2025 CSV dosyasını elle indirin.')
        return 2

    candidates = []
    for pkg in scored:
        for resource in pkg.get('resources', []) or []:
            fmt = str(resource.get('format', '')).lower()
            res_text = ' '.join(str(resource.get(k, '')) for k in ('name', 'description', 'url', 'id')).casefold()
            if fmt == 'csv' and ('2025' in res_text or '2025' in str(pkg.get('title', ''))):
                candidates.append((pkg, resource))
    if len(candidates) != 1:
        print(f'2025 CSV kaynağı tekil olarak belirlenemedi (aday sayısı: {len(candidates)}). Otomatik indirme yapılmadı.')
        for pkg, res in candidates[:20]:
            print(f"- {pkg.get('title','')} | {res.get('name','')} | {res.get('url','')}")
        if not candidates:
            for pkg in scored[:10]:
                print(f"Veri kümesi: {pkg.get('title','')}")
                for res in pkg.get('resources', []) or []:
                    print(f"  kaynak: {res.get('name','')} ({res.get('format','')}) {res.get('url','')}")
        print('Mevcut kaynak dosyanız korunmuştur. Portal sayfasından 2025 CSV dosyasını elle indirin.')
        return 2

    pkg, resource = candidates[0]
    url = str(resource.get('url', '')).strip()
    name = safe_filename(str(resource.get('name') or resource.get('url') or '2025-rail-passenger-data.csv'))
    if '2025' not in name:
        name = '2025-' + name
    target = RAW_DIR / name
    if target.exists() and not args.overwrite:
        print(f'Hedef dosya zaten mevcut; üzerine yazılmadı: {target}')
        print('Kaynağı gerçekten yenilemek istersen --overwrite bayrağını kullan.')
        return 0
    if not url:
        print('Kaynak kaydında URL bulunamadı; otomatik indirme yapılmadı.')
        return 2

    metadata = {
        'dataset_title': pkg.get('title'),
        'dataset_id': pkg.get('id'),
        'dataset_url': f"https://data.ibb.gov.tr/dataset/{pkg.get('name','')}",
        'resource_name': resource.get('name'),
        'resource_id': resource.get('id'),
        'resource_url': url,
        'format': resource.get('format'),
        'license_title': pkg.get('license_title'),
        'license_url': (pkg.get('license_url') or ''),
        'retrieved_by': 'src/fetch_data.py; verify attribution and license terms manually',
    }
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'rayli-sistem-agi-student-project/1.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        if not data or b'\n' not in data[:1000]:
            raise RuntimeError('İndirilen içerik CSV gibi görünmüyor.')
        target.write_bytes(data)
        (ROOT / 'data' / 'source_metadata_2025.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'İndirildi: {target} ({len(data):,} bayt)')
        print('Kaynak metaverisi: data/source_metadata_2025.json')
        print('Lisans ve atıf alanları rapora yazılmadan önce portal kaydında insan tarafından doğrulanmalıdır.')
        return 0
    except Exception as exc:
        if target.exists() and target.stat().st_size == 0:
            target.unlink(missing_ok=True)
        print(f'CSV indirme başarısız oldu: {exc}')
        print('Mevcut kaynak dosyanız korunmuştur. Portal sayfasından 2025 CSV dosyasını elle indirin.')
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
