"""Climate at glacier mean elevation, 2000-2019, per dataset and zone (raw and calibrated), plus mu*.
Reads each glacier's climate_historical.nc; same lapse rate, thresholds (0/2 C snow-rain, 0 C melt) and Pf as the runs."""
import glob, os
import numpy as np, pandas as pd, xarray as xr
ROOT = '/Users/milliespencer/v2_CR2_OGGM_project_11_2026'
par = pd.read_csv(f'{ROOT}/files_chile_OGGM_climate_comparison/LR_Pf.csv').set_index('Cluster')
Z = ['OT3','DA1','DA2','DA3','WA1','WA2','WA3','WA4','WA5','WA6']
rows = []
for ds in ['ERA5','CRU','CR2MET']:
    for z in Z:
        s = f'{ROOT}/Output/{ds}/{z}/RGI_{z}/b_080/L3/summary/'
        g = pd.read_csv(s + f'glacier_statistics__{z}.csv')
        c = pd.read_csv(s + f'climate_statistics__{z}.csv')[['rgi_id', 'flowline_mean_elev']]
        g = g[g['mu_star_glacierwide'].notna()]
        if 'flowline_mean_elev' not in g.columns: g = g.merge(c, on='rgi_id')
        lr, pf = par.loc[z, 'LR'], par.loc[z, 'Pf']
        recs = []
        for _, r in g.iterrows():
            f = glob.glob(f'{ROOT}/Output/{ds}/{z}/per_glacier/*/*/{r.rgi_id}/climate_historical.nc')
            if not f:
                continue
            with xr.open_dataset(f[0]) as nc:
                nc = nc.sel(time=slice('2000-01-01', '2019-12-31'))
                ref = float(nc.attrs['ref_hgt'])
                ref_raw = float(nc.attrs.get('uncorrected_ref_hgt', ref))
                h = r['flowline_mean_elev']
                t_cal = nc['temp'].values + lr * (h - ref)
                t_raw = nc['temp'].values + lr * (h - ref_raw)
                p = nc['prcp'].values
            frac_sol = np.clip((2.0 - t_cal) / 2.0, 0, 1)
            ny = len(p) / 12
            recs.append(dict(area=r['rgi_area_km2'], T_raw=t_raw.mean(), T_cal=t_cal.mean(),
                             P_raw=p.sum() / ny, P_model=pf * p.sum() / ny,
                             snow_pct=100 * (frac_sol * p).sum() / p.sum(),
                             pdd=np.clip(t_cal, 0, None).sum() / ny, mu=r['mu_star_glacierwide']))
        d = pd.DataFrame(recs)
        w = d['area']
        rows.append(dict(dataset=ds, zone=z, n=len(d), **{k: np.average(d[k], weights=w) for k in
                         ['T_raw', 'T_cal', 'P_raw', 'P_model', 'snow_pct', 'pdd', 'mu']}))
        rows[-1]['T_bias'] = rows[-1]['T_cal'] - rows[-1]['T_raw']
        print(f'{ds} {z}: {len(d)} glaciers', flush=True)
out = pd.DataFrame(rows)
out.to_csv(f'{ROOT}/Output/inputs_params_2000_2019_by_zone.csv', index=False)
pd.set_option('display.width', 200)
for col, lab in [('T_raw','raw temperature at mean glacier elevation (C)'), ('T_bias','temperature bias (C)'),
                 ('P_raw','raw precipitation (mm/yr)'), ('P_model','precipitation x Pf (mm/yr)'),
                 ('snow_pct','share of precipitation falling as snow (%)'), ('pdd','positive degree-months (C month/yr)'),
                 ('mu','mu* (mm w.e. K-1 month-1)')]:
    print(f'\n--- {lab}, area-weighted, 2000-2019')
    print(out.pivot(index='zone', columns='dataset', values=col).reindex(Z).round(1).to_string())
