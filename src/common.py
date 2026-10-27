from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / 'data' / 'raw'
PROCESSED_DIR = ROOT / 'data' / 'processed'
OUTPUT_DIR = ROOT / 'outputs'
TOPOLOGY_FILE = ROOT / 'topology' / 'line_stations.csv'

# Explicit aliases to collapse directional platforms/entrances into physical station labels.
# This mapping must be reviewed against the official network map before final submission.
ALIASES = {
    'Aksaray 1': 'Aksaray', 'Otogar 1': 'Otogar',
    'Ulubatlı': 'Topkapı-Ulubatlı', 'Bayrampaşa': 'Bayrampaşa-Maltepe',
    'Kartaltepe': 'Kartaltepe-Kocatepe', 'Davutpaşa': 'Davutpaşa-YTÜ',
    'Emniyet': 'Emniyet-Fatih', 'Havaalanı': 'Atatürk Havalimanı', 'İdtm': 'DTM-İstanbul Fuar Merkezi',
    
    '4 Levent 2 Güney': '4. Levent', '4 Levent Kuzey': '4. Levent',
    'Atatürk Oto Sanayi Güney': 'Atatürk Oto Sanayi', 'Atatürk Oto Sanayi Kuzey': 'Atatürk Oto Sanayi',
    'İTÜ Güney': 'İTÜ-Ayazağa', 'İTÜ kuzey': 'İTÜ-Ayazağa',
    'Levent 2 Kuzey': 'Levent', 'Levent Güney': 'Levent',
    'Levent Batı konkors': 'Levent', 'Levent Doğu konkors': 'Levent',
    'Osmanbey 2 Güney': 'Osmanbey', 'Osmanbey Kuzey': 'Osmanbey',
    'Sanayi Mah. Güney': 'Sanayi Mahallesi', 'Sanayi Mah. Kuzey': 'Sanayi Mahallesi',
    'Seyrantepe 1 Batı': 'Seyrantepe', 'Seyrantepe 2 Doğu': 'Seyrantepe', 'Seyrantepe 3 Stad Girişi': 'Seyrantepe',
    'Taksim Güney': 'Taksim', 'Vezneciler Güney': 'Vezneciler-İstanbul Üniversitesi', 'Vezneciler Kuzey': 'Vezneciler-İstanbul Üniversitesi',
    'Yenikapı Güney': 'Yenikapı', 'Yenikapı Kuzey': 'Yenikapı',
    'Şişhane Güney': 'Şişhane', 'Şişhane Kuzey': 'Şişhane',
    'Şişli 2 Kuzey': 'Şişli-Mecidiyeköy', 'Şişli Güney': 'Şişli-Mecidiyeköy',
    'Mahmutbey M7 Hol 1': 'Mahmutbey', 'Mahmutbey M7 Hol 2': 'Mahmutbey', 'Mahmutbey M7 Hol 3': 'Mahmutbey', 'Mahmutbey M7 Hol 4': 'Mahmutbey',
    'MAHMUTBEY M7 HOL 1': 'Mahmutbey', 'MAHMUTBEY M7 HOL 2': 'Mahmutbey',
    'MAHMUTBEY M3 HOL 3': 'Mahmutbey', 'MAHMUTBEY M3 HOL 4': 'Mahmutbey',
    'Acıbadem (Batı)': 'Acıbadem', 'Acıbadem (Doğu)': 'Acıbadem',
    'Bostancı (Batı)': 'Bostancı', 'Bostancı (Doğu)': 'Bostancı',
    'Kadıköy (Batı)': 'Kadıköy', 'Kadıköy (Doğu)': 'Kadıköy',
    'Kartal (Batı)': 'Kartal', 'Kartal (Doğu)': 'Kartal',
    'Pendik (Batı)': 'Pendik', 'Pendik (Doğu)': 'Pendik',
    'Tavşantepe (Batı)': 'Tavşantepe', 'Tavşantepe (Doğu)': 'Tavşantepe',
    'Yakacık (Batı)': 'Yakacık-Adnan Kahveci', 'Yakacık (Doğu)': 'Yakacık-Adnan Kahveci',
    'Hastane (Batı)': 'Hastane-Adliye', 'Hastane (Doğu/Adliye)': 'Hastane-Adliye',
    'Altunizade 1': 'Altunizade', 'Altunizade 2': 'Altunizade',
    'Üsküdar 1': 'Üsküdar', 'Üsküdar 2': 'Üsküdar',
    'Çekmeköy 1': 'Çekmeköy', 'Çekmeköy 2': 'Çekmeköy',
    'ALİBEYKÖY BATI': 'Alibeyköy Metro', 'ALİBEYKÖY DOĞU': 'Alibeyköy Metro',
    'GÖZTEPE BATI': 'Göztepe (M7)', 'GÖZTEPE DOĞU': 'Göztepe (M7)',
    'KARADENİZ MAH. BATI': 'Karadeniz Mahallesi', 'KARADENİZ MAH. DOĞU': 'Karadeniz Mahallesi',
    'KAĞITHANE BATI': 'Kağıthane', 'KAĞITHANE DOGU': 'Kağıthane',
    'M7 FULYA': 'Fulya', 'M7 YILDIZ 1': 'Yıldız', 'M7 YILDIZ 2': 'Yıldız',
    'MECİDİYEKÖY BATI': 'Şişli-Mecidiyeköy', 'MECİDİYEKÖY DOĞU': 'Şişli-Mecidiyeköy',
    'NURTEPE BATI': 'Nurtepe', 'NURTEPE DOĞU': 'Nurtepe',
    'ORUÇREİS BATI': 'Oruç Reis', 'ORUÇREİS DOĞU': 'Oruç Reis',
    'VEYSELKARANİ BATI': 'Veysel Karani-Akşemsettin', 'VEYSELKARANİ DOĞU': 'Veysel Karani-Akşemsettin',
    'ÇAĞLAYAN BATI': 'Çağlayan', 'ÇAĞLAYAN DOĞU': 'Çağlayan',
    'ÇIRÇIR BATI': 'Çırçır', 'ÇIRÇIR DOĞU': 'Çırçır',
    'MAHMUTBEY M3 HOL 3': 'Mahmutbey', 'MAHMUTBEY M3 HOL 4': 'Mahmutbey',
    '15.Tem': '15 Temmuz', '29 EKİM CUMHURİYET-İHLAS YUVA': '29 Ekim Cumhuriyet',
     'HALKALI GÜNEY': 'Halkalı (M9)', 'HALKALI KUZEY': 'Halkalı (M9)',
    'İKİTELLİ SANAYİ': 'İkitelli Sanayi', 'OLİMPİYAT BATI': 'Olimpiyat', 'OLİMPİYAT DOĞU': 'Olimpiyat',
    'Eminönü 2': 'Eminönü', 'Kabataş 2': 'Kabataş', 'Zeytinburnu 2': 'Zeytinburnu',
    'Haliç güney': 'Haliç', 'Haliç kuzey': 'Haliç',
    'AYŞE KADIN': 'Ayşekadın', 'MODOKO KEYAP': 'MODOKO-KEYAP',
    'ZİYA GÖKALP MAH': 'Ziya Gökalp Mahallesi', 'ATATÜRK MAHALLESİ': 'Atatürk Mahallesi',
    'KAZIMKARABEKİR': 'Kazım Karabekir', 'TEKSTİLKENT': 'Tekstilkent-Giyimkent',
    'T4 KİPTAŞ VENEZİA': 'Kiptaş Venezia',
    'M.kemal': 'Mustafa Kemal',
    'Bakırköy-1': 'Bakırköy (Marmaray)', 'Bakırköy-2': 'Bakırköy (Marmaray)',
    'Bostancı-1': 'Bostancı (Marmaray)', 'Bostancı-2': 'Bostancı (Marmaray)',
    'Cevizli-1': 'Cevizli (Marmaray)', 'Cevizli-2': 'Cevizli (Marmaray)',
    'Gebze-1': 'Gebze', 'Gebze-2': 'Gebze',
    'Küçükyalı-1': 'Küçükyalı (Marmaray)', 'Küçükyalı-2': 'Küçükyalı (Marmaray)',
    'Sirkeci-1': 'Sirkeci', 'Sirkeci-2': 'Sirkeci', 'Sirkeci-3': 'Sirkeci', 'Sirkeci-4': 'Sirkeci',
    'Tersane-1': 'Tersane', 'Tersane-2': 'Tersane',
    'Yenikapı-1': 'Yenikapı', 'Yenikapı-2': 'Yenikapı', 'Yenikapı-3': 'Yenikapı',
    'Üsküdar-1': 'Üsküdar', 'Üsküdar-2': 'Üsküdar', 'Üsküdar-3': 'Üsküdar',
    'Ayrılıkçeşmesi': 'Ayrılık Çeşmesi', 'Ayrılıkçeşme': 'Ayrılık Çeşmesi', 'Florya aqua': 'Florya Akvaryum',
    'Sarıgazı': 'Sarıgazi', 'MehmetAkif': 'Mehmet Akif',
    'KAZLIÇEŞME': 'Kazlıçeşme', 'SİRKECİ': 'Sirkeci', 'CANKURTARAN': 'Cankurtaran',
    'KOCA MUSTAFA PAŞA': 'Kocamustafapaşa', 'YEDİKULE': 'Yedikule', 'CERRAHPAŞA': 'Cerrahpaşa',
    'ARNAVUTKÖY  GUNEY': 'Arnavutköy', 'ARNAVUTKÖY  KUZEY': 'Arnavutköy',
    'TAŞOLUK   GUNEY': 'Taşoluk', 'TAŞOLUK   KUZEY': 'Taşoluk',
    'HAVALİMANI (TERMİNAL 1)': 'İstanbul Havalimanı',
    'HAVALİMANI (KARGO TERMİNALİ )': 'Kargo Terminali',
    'Esenkent Cevizli': 'Esenkent',
    'Özgürlük Meydan Kuzey': 'Özgürlük Meydanı', 'Özgürlük Meydanı Güney': 'Özgürlük Meydanı',
    'Yeni Mahalle': 'Yenimahalle', 'Boğaziçi': 'Boğaziçi Üniversitesi/Hisarüstü',
    'Rumeli Hisarüstü': 'Boğaziçi Üniversitesi/Hisarüstü',
    'Eyüp': 'Eyüp Teleferik',
    'Zeytinburnu 2': 'Zeytinburnu',
    'Haliç güney': 'Haliç', 'Haliç kuzey': 'Haliç',
    'AYŞE KADIN': 'Ayşekadın', 'MODOKO KEYAP': 'MODOKO-KEYAP',
    'ZİYA GÖKALP MAH': 'Ziya Gökalp Mahallesi', 'ATATÜRK MAHALLESİ': 'Atatürk Mahallesi',
    'KAZIMKARABEKİR': 'Kazım Karabekir', 'TEKSTİLKENT': 'Tekstilkent-Giyimkent',
    'T4 KİPTAŞ VENEZİA': 'Kiptaş Venezia',
    'M.kemal': 'Mustafa Kemal',
    'Sağmalcılar': 'Sağmalcılar', 'Üniversite': 'Üniversite', 'Universite': 'Üniversite',
}

def _norm_key(value: str) -> str:
    value = unicodedata.normalize('NFKC', str(value or '')).strip().replace('I', 'ı').replace('İ', 'i').casefold()
    value = re.sub(r'\s+', ' ', value)
    return value

_ALIAS_BY_KEY = {_norm_key(k): v for k, v in ALIASES.items()}

def canonical_station(value: str) -> str:
    if pd.isna(value) or not str(value).strip():
        return ''
    s = re.sub(r'\s+', ' ', str(value).strip())
    return _ALIAS_BY_KEY.get(_norm_key(s), s)

def parse_istanbul_coordinate(value, kind: str):
    """Parse source coordinates like 289.335.555.555.556 -> 28.9335555555556.

    The source CSV groups digits with periods incorrectly. For Istanbul, both axes
    have two integer degree digits; use first two digits as degrees and the rest
    as the fractional part. Missing/invalid values return NaN.
    """
    import math
    if pd.isna(value) or not str(value).strip():
        return math.nan
    s = str(value).strip()
    sign = -1 if s.startswith('-') else 1
    digits = re.sub(r'\D', '', s)
    if len(digits) < 3:
        return math.nan
    deg = int(digits[:2])
    frac = int(digits[2:]) / (10 ** (len(digits)-2))
    x = sign * (deg + frac)
    lo, hi = (27.0, 30.0) if kind == 'longitude' else (40.0, 42.0)
    if not lo <= x <= hi:
        return math.nan
    return x

def locate_raw_csv() -> Path:
    files = sorted(RAW_DIR.glob('*.csv'))
    if not files:
        raise FileNotFoundError(f'CSV bulunamadı: {RAW_DIR}')
    preferred = [p for p in files if '2025' in p.name.lower()]
    return preferred[0] if preferred else files[0]

def load_raw() -> pd.DataFrame:
    path = locate_raw_csv()
    df = pd.read_csv(path, sep=';', dtype=str, encoding='utf-8-sig', low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    required = {'transaction_year','transaction_month','transaction_day','line','station_name','station_number','town','longitude','latitude','passage_cnt','passanger_cnt'}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f'Beklenen sütunlar eksik: {sorted(missing)}')
    return df

def ensure_dirs():
    for p in (PROCESSED_DIR, OUTPUT_DIR, ROOT / 'web', ROOT / 'docs'):
        p.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
