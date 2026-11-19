"""Per dataset and zone: climate inputs at the glaciers (raw and corrected) and calibrated parameters."""
import pandas as pd, numpy as np
ROOT = '/Users/milliespencer/v2_CR2_OGGM_project_11_2026'
lr = pd.read_csv(f'{ROOT}/files_chile_OGGM_climate_comparison/LR_Pf.csv').set_index('Cluster')['LR']
Z = ['OT3','DA1','DA2','DA3','WA1','WA2','WA3','WA4','WA5','WA6']
P = '1980-2010_'
rows = []
for ds in ['ERA5','CRU','CR2MET']:
    for z in Z:
        s = f'{ROOT}/Output/{ds}/{z}/RGI_{z}/b_080/L3/summary/'
        g = pd.read_csv(s + f'glacier_statistics__{z}.csv')[['rgi_id','rgi_area_km2','mu_star_glacierwide','ref_hgt_calib_diff']]
        c = pd.read_csv(s + f'climate_statistics__{z}.csv')
        d = g.merge(c[['rgi_id', P+'avg_temp_mean_elev', P+'avg_prcp', P+'avg_prcpsol_mean_elev', P+'avg_tempmelt_mean_elev']], on='rgi_id')
        d = d[d['mu_star_glacierwide'].notna()]
        w = d['rgi_area_km2']
        dT = -d['ref_hgt_calib_diff'].fillna(0) * lr[z]
        wm = lambda x: np.average(x, weights=w)
        rows.append(dict(dataset=ds, zone=z,
            T_corrected_C=wm(d[P+'avg_temp_mean_elev']),
            T_raw_C=wm(d[P+'avg_temp_mean_elev'] - dT),
            temp_bias_C=wm(dT),
            prcp_mm=wm(d[P+'avg_prcp']),
            snow_frac_pct=100 * wm(d[P+'avg_prcpsol_mean_elev'] / d[P+'avg_prcp']),
            tempmelt_Cmonth=wm(d[P+'avg_tempmelt_mean_elev']),
            mu_star=wm(d['mu_star_glacierwide'])))
r = pd.DataFrame(rows)
r.to_csv(f'{ROOT}/Output/inputs_params_by_zone.csv', index=False)
pd.set_option('display.width', 200)
for col in ['T_raw_C','T_corrected_C','temp_bias_C','prcp_mm','snow_frac_pct','mu_star']:
    print(f'\n--- {col} (area-weighted mean, 1980-2010 climate)')
    print(r.pivot(index='zone', columns='dataset', values=col).reindex(Z).round(1).to_string())
