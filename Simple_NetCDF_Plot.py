#!/usr/bin/env python3
"""
Simple NetCDF-only plotter - extracts mass balance directly from NetCDF
"""

import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from oggm import utils
import warnings
import os

if not hasattr(np, 'warnings'):
    np.warnings = warnings

print("\n" + "="*70)
print("EXTRACTING DATA FROM NETCDF FILES")
print("="*70)

# Clusters and their NetCDF file paths
clusters_to_check = {
    'DA1': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA1/run_output_2000_2019_hydro_TC_DA1.nc',
    'DA2': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA2/run_output_2000_2019_hydro_TC_DA2.nc',
    'DA3': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA3/run_output_2000_2019_hydro_TC_DA3.nc',
    'WA1': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA1/run_output_2000_2019_hydro_TC_WA1.nc',
    'WA2': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA2/run_output_2000_2019_hydro_TC_WA2.nc',
    'WA3': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA3/run_output_2000_2019_hydro_TC_WA3.nc',
}

# Load RGI data
rgi_file = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/RGI_BNA_Clusters.csv'
datos_rgi = pd.read_csv(rgi_file)

# Load geodetic data
utils.get_geodetic_mb_dataframe()
geodetic_ref = utils.get_geodetic_mb_dataframe()
geodetic_ref = geodetic_ref[geodetic_ref['period'] == '2000-01-01_2020-01-01']

results = []

for cluster, nc_path in clusters_to_check.items():
    print(f"\n{cluster}:")
    
    try:
        # Open NetCDF
        ds = xr.open_dataset(nc_path)
        
        print(f"  ✓ Opened NetCDF")
        
        # Get glacier IDs
        glacier_ids = [str(x) for x in ds['rgi_id'].values]
        n_glaciers = len(glacier_ids)
        
        # Calculate mass balance for 2000-2020 (matching calibration period)
        volume_2000 = ds['volume'].sel(time=2000).sum()
        volume_2020 = ds['volume'].sel(time=2020).sum()
        area_2000 = ds['area'].sel(time=2000)
        
        # Volume change in m³, divide by total area and time to get m w.e./yr
        total_area_m2 = area_2000.sum().values
        n_years = 20  # 2000-2020 period (matches calibration)
        
        # SMB in m w.e./yr, then convert to mm/yr
        smb_m_per_yr = (volume_2020 - volume_2000) / total_area_m2 / n_years
        smb_mm_per_yr = float(smb_m_per_yr * 1000)
        
        print(f"  SMB: {smb_mm_per_yr:.1f} mm/yr")
        
        # Get cluster glaciers from RGI
        cluster_glaciers = datos_rgi[datos_rgi['Cluster'] == cluster]['RGIId'].tolist()
        
        # Get geodetic observations
        gmb_data = geodetic_ref[geodetic_ref.index.isin(cluster_glaciers)]
        
        if len(gmb_data) > 0:
            gmb_weighted = np.average(gmb_data['dmdtda'] * 1000, weights=gmb_data['area'])
            gmb_error = np.average(gmb_data['err_dmdtda'] * 1000, weights=gmb_data['area'])
            
            print(f"  GMB: {gmb_weighted:.1f} ± {gmb_error:.1f} mm/yr")
            print(f"  Glaciers: {n_glaciers}")
            
            results.append({
                'cluster': cluster,
                'SMB': smb_mm_per_yr,
                'GMB': gmb_weighted,
                'GMB_error': gmb_error,
                'n_glaciers': n_glaciers,
                'area_km2': float(total_area_m2 / 1e6)
            })
        else:
            print(f"  ⚠ No geodetic data")
        
        ds.close()
        
    except FileNotFoundError:
        print(f"  ✗ File not found")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print(f"\n\nTotal clusters loaded: {len(results)}")

if len(results) == 0:
    print("❌ No data to plot!")
    exit(1)

##############################################################################
# PLOT
##############################################################################

df = pd.DataFrame(results)

fig, ax = plt.subplots(figsize=(14, 8))

n = len(df)
x_pos = np.arange(n)

# SMB - circles
ax.plot(x_pos - 0.1, df['SMB'], 'o', markersize=14, color='#e74c3c', 
       markeredgecolor='black', markeredgewidth=2, label='SMB (CR2MET)', zorder=5)

# GMB - diamonds with error bars
ax.errorbar(x_pos + 0.1, df['GMB'], yerr=df['GMB_error'],
           fmt='D', markersize=14, color='darkred',
           markeredgecolor='black', markeredgewidth=2,
           ecolor='gray', capsize=8, capthick=2,
           linewidth=2, label='GMB (Geodetic)', zorder=10)

ax.axhline(y=0, color='black', linewidth=1, linestyle='--', alpha=0.5)

ax.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=15, fontweight='bold')
ax.set_xlabel('Cluster', fontsize=15, fontweight='bold')
ax.set_title(f'CR2MET Mass Balance - {n} Clusters', fontsize=17, fontweight='bold', pad=20)
ax.set_xticks(x_pos)
ax.set_xticklabels(df['cluster'], fontsize=14, fontweight='bold')
ax.legend(loc='best', fontsize=13)
ax.grid(axis='y', alpha=0.4)

# Labels
for i, row in df.iterrows():
    ax.text(i - 0.1, row['SMB'] + 20, f"{row['SMB']:.1f}", 
           ha='center', va='bottom', fontweight='bold', fontsize=10, color='#e74c3c')
    ax.text(i + 0.1, row['GMB'] - 20, f"{row['GMB']:.1f}", 
           ha='center', va='top', fontsize=10, color='darkred')
    
    bias = row['SMB'] - row['GMB']
    bias_pct = (bias / row['GMB']) * 100
    ax.text(i, min(row['SMB'], row['GMB']) - 60, f'{bias:+.0f}\n({bias_pct:+.0f}%)',
           ha='center', va='top', fontsize=8,
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()

output = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/CR2MET_Clusters_Simple.png'
plt.savefig(output, dpi=300, bbox_inches='tight')
print(f"\n✓ Saved: {output}")

print("\n" + "="*70)
print("RESULTS")
print("="*70)
for _, row in df.iterrows():
    bias = row['SMB'] - row['GMB']
    print(f"{row['cluster']}: SMB={row['SMB']:.1f}, GMB={row['GMB']:.1f}, Bias={bias:+.1f}")
print("="*70)

plt.show()