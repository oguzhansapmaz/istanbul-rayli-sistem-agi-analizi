from __future__ import annotations
import json
import pandas as pd
from .common import ROOT, RAW_DIR, PROCESSED_DIR, OUTPUT_DIR, load_raw, canonical_station, parse_istanbul_coordinate, ensure_dirs, write_json


def main():
    ensure_dirs()
    df = load_raw()
    source_rows = len(df)
    original_columns = list(df.columns)
    missing_station_source = int(df['station_name'].fillna('').astype(str).str.strip().eq('').sum())
    missing_lon_source = int(df['longitude'].fillna('').astype(str).str.strip().eq('').sum())
    missing_lat_source = int(df['latitude'].fillna('').astype(str).str.strip().eq('').sum())
    df['source_station_name'] = df['station_name'].fillna('').astype(str).str.strip()
    df['station_canonical'] = df['source_station_name'].map(canonical_station)
    df['line'] = df['line'].fillna('').astype(str).str.strip()
    df['date'] = pd.to_datetime(
        dict(year=pd.to_numeric(df['transaction_year'], errors='coerce'),
             month=pd.to_numeric(df['transaction_month'], errors='coerce'),
             day=pd.to_numeric(df['transaction_day'], errors='coerce')),
        errors='coerce')
    df['passenger_count'] = pd.to_numeric(df['passanger_cnt'], errors='coerce')
    df['passage_count'] = pd.to_numeric(df['passage_cnt'], errors='coerce')
    df['longitude_clean'] = df['longitude'].map(lambda x: parse_istanbul_coordinate(x, 'longitude'))
    df['latitude_clean'] = df['latitude'].map(lambda x: parse_istanbul_coordinate(x, 'latitude'))
    df['has_station'] = df['station_canonical'].astype(str).str.strip().ne('')
    df['has_coords'] = df['longitude_clean'].notna() & df['latitude_clean'].notna()

    keep = ['date','transaction_year','transaction_month','transaction_day','line','source_station_name','station_canonical','station_number','town','longitude_clean','latitude_clean','passage_count','passenger_count','has_station','has_coords']
    df[keep].to_csv(PROCESSED_DIR / 'clean_station_daily.csv', index=False, encoding='utf-8-sig')

    station_rows = df[df['has_station'] & df['date'].notna() & df['passenger_count'].notna()].copy()
    # Sum source records within the same physical station/date; direction/entrance aliasing is documented as a limitation.
    station_day = station_rows.groupby(['station_canonical','date'], as_index=False).agg(
        passenger_count=('passenger_count','sum'), passage_count=('passage_count','sum'),
        source_record_count=('station_canonical','size'), line_count=('line','nunique'),
        longitude=('longitude_clean','mean'), latitude=('latitude_clean','mean'),
        towns=('town', lambda x: ' | '.join(sorted(set(str(v).strip() for v in x.dropna() if str(v).strip()))))
    )
    station_day.to_csv(PROCESSED_DIR / 'station_day_2025.csv', index=False, encoding='utf-8-sig')
    station_summary = station_day.groupby('station_canonical', as_index=False).agg(
        observed_days=('date','nunique'), passenger_total_source_sum=('passenger_count','sum'),
        passenger_mean_per_observed_day=('passenger_count','mean'), passenger_median_per_observed_day=('passenger_count','median'),
        passenger_max_daily=('passenger_count','max'), passage_total_source_sum=('passage_count','sum'),
        line_count=('line_count','max'), longitude=('longitude','mean'), latitude=('latitude','mean'), towns=('towns', lambda x:' | '.join(sorted(set(y for item in x for y in item.split(' | ') if y))))
    )
    station_summary.to_csv(PROCESSED_DIR / 'station_summary_2025.csv', index=False, encoding='utf-8-sig')

    line_summary = df.groupby('line', as_index=False).agg(
        records=('line','size'), named_records=('has_station','sum'), source_station_names=('station_canonical','nunique'),
        passenger_count_sum=('passenger_count', lambda x: pd.to_numeric(x, errors='coerce').sum()),
        missing_station_records=('has_station', lambda x: int((~x).sum())),
        missing_coord_records=('has_coords', lambda x: int((~x).sum()))
    ).sort_values('records', ascending=False)
    line_summary.to_csv(PROCESSED_DIR / 'line_data_summary.csv', index=False, encoding='utf-8-sig')

    aliases = df[['line','source_station_name','station_canonical']].drop_duplicates().sort_values(['line','source_station_name'])
    aliases.to_csv(PROCESSED_DIR / 'station_alias_review.csv', index=False, encoding='utf-8-sig')

    audit = {
        'source_file': str(next(iter(RAW_DIR.glob('*.csv'))).name),
        'rows': int(source_rows), 'columns': int(len(original_columns)), 'source_columns': original_columns,
        'years': sorted(df['transaction_year'].dropna().astype(str).unique().tolist()),
        'months_covered': sorted(pd.to_numeric(df['transaction_month'], errors='coerce').dropna().astype(int).unique().tolist()),
        'distinct_lines': int(df['line'].nunique(dropna=True)),
        'distinct_source_station_names_including_blank': int(df['station_name'].nunique(dropna=True)),
        'distinct_station_numbers': int(df['station_number'].nunique(dropna=True)),
        'missing_station_name_records': int(missing_station_source),
        'missing_longitude_source_records': int(missing_lon_source),
        'missing_latitude_source_records': int(missing_lat_source),
        'normalized_valid_coordinate_records': int(df['has_coords'].sum()),
        'coordinate_min_max': {
            'longitude_min': float(df['longitude_clean'].min()) if df['longitude_clean'].notna().any() else None,
            'longitude_max': float(df['longitude_clean'].max()) if df['longitude_clean'].notna().any() else None,
            'latitude_min': float(df['latitude_clean'].min()) if df['latitude_clean'].notna().any() else None,
            'latitude_max': float(df['latitude_clean'].max()) if df['latitude_clean'].notna().any() else None,
        },
        'passenger_numeric_invalid': int(pd.to_numeric(df['passanger_cnt'], errors='coerce').isna().sum()),
        'passage_numeric_invalid': int(pd.to_numeric(df['passage_cnt'], errors='coerce').isna().sum()),
        'duplicate_full_source_rows': int(df.duplicated().sum()),
        'station_day_rows_after_canonicalization': int(len(station_day)),
        'canonical_station_labels': int(station_summary['station_canonical'].nunique()),
        'method_note': 'station-level sums aggregate source rows after manually curated alias canonicalization; possible double counting across entrances/directions/interchanges must be checked against source metadata.'
    }
    write_json(OUTPUT_DIR / 'data_audit.json', audit)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    print('\nCreated: data/processed/clean_station_daily.csv, station_day_2025.csv, station_summary_2025.csv, line_data_summary.csv, station_alias_review.csv')

if __name__ == '__main__': main()
