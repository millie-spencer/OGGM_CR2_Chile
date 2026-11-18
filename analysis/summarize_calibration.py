"""Summarize OGGM calibration per dataset and zone: failures, mu*, temperature bias."""
import os, glob
import pandas as pd

ROOT = '/Users/milliespencer/v2_CR2_OGGM_project_11_2026'
OUT = f'{ROOT}/Output'
rgi = pd.read_csv(f'{ROOT}/files_chile_OGGM_climate_comparison/RGI_BNA_Clusters.csv')[['RGIId', 'TermType', 'Area', 'Cluster']]
lr = pd.read_csv(f'{ROOT}/files_chile_OGGM_climate_comparison/LR_Pf.csv').set_index('Cluster')['LR']
ZONES = ['OT3', 'DA1', 'DA2', 'DA3', 'WA1', 'WA2', 'WA3', 'WA4', 'WA5', 'WA6']

rows, fails = [], []
for ds in ['ERA5', 'CRU', 'CR2MET']:
    for z in ZONES:
        f = f'{OUT}/{ds}/{z}/RGI_{z}/b_080/L3/summary/glacier_statistics__{z}.csv'
        d = pd.read_csv(f).merge(rgi, left_on='rgi_id', right_on='RGIId', how='left')
        ok = d['mu_star_glacierwide'].notna()
        dh = d['ref_hgt_calib_diff'].fillna(0) if 'ref_hgt_calib_diff' in d else pd.Series(0.0, index=d.index)
        dT = -dh * lr[z]                                  # temperature bias in deg C (positive = warmed)
        corr = ok & (dh != 0)
        rows.append(dict(
            dataset=ds, zone=z, glaciers=len(d), area_km2=d['rgi_area_km2'].sum(),
            failed=int((~ok).sum()), failed_area_km2=d.loc[~ok, 'rgi_area_km2'].sum(),
            failed_lake_term=int(((~ok) & (d['TermType'] == 2)).sum()),
            mu_median=d.loc[ok, 'mu_star_glacierwide'].median(),
            mu_at_cap_pct=100 * (d.loc[ok, 'mu_star_glacierwide'] > 590).mean(),
            tbias_glaciers=int(corr.sum()),
            tbias_area_pct=100 * d.loc[corr, 'rgi_area_km2'].sum() / d.loc[ok, 'rgi_area_km2'].sum(),
            tbias_median_C=dT[corr].median() if corr.any() else 0.0,
            tbias_max_C=dT[corr].max() if corr.any() else 0.0,
            tbias_over3C=int((corr & (dT.abs() > 3)).sum())))
        if 'error_task' in d:
            for _, r in d.loc[~ok].iterrows():
                fails.append(dict(dataset=ds, zone=z, rgi_id=r['rgi_id'], area_km2=r['rgi_area_km2'],
                                  TermType=r['TermType'], error_task=r.get('error_task'), error_msg=str(r.get('error_msg'))[:120]))

s = pd.DataFrame(rows)
s.to_csv(f'{OUT}/calibration_summary_by_zone.csv', index=False)
pd.DataFrame(fails).to_csv(f'{OUT}/failed_glaciers_all_datasets.csv', index=False)

pd.set_option('display.width', 200)
print(s.round(1).to_string(index=False))
print('\n--- national, per dataset')
nat = s.groupby('dataset').agg(glaciers=('glaciers', 'sum'), area_km2=('area_km2', 'sum'), failed=('failed', 'sum'),
                               failed_area_km2=('failed_area_km2', 'sum'), tbias_glaciers=('tbias_glaciers', 'sum'))
nat['failed_area_pct'] = 100 * nat['failed_area_km2'] / nat['area_km2']
print(nat.round(1).to_string())
if fails:
    fd = pd.DataFrame(fails)
    print('\n--- failures by step (first failing task), per dataset')
    print(fd.groupby(['dataset', 'error_task']).size().unstack(0).fillna(0).astype(int).to_string())
