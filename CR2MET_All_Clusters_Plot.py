#!/usr/bin/env python3
"""
CR2MET Complete Results - All 10 Clusters
Comparison of simulated mass balance (SMB) vs geodetic observations (GMB)
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
print("CR2MET - ALL CLUSTERS COMPARISON")
print("="*70)

# All 10 clusters
clusters_to_check = {
    'OT3': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/OT3/run_output_2000_2019_hydro_TC_OT3.nc',
    'DA1': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA1/run_output_2000_2019_hydro_TC_DA1.nc',
    'DA2': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA2/run_output_2000_2019_hydro_TC_DA2.nc',
    'DA3': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA3/run_output_2000_2019_hydro_TC_DA3.nc',
    'WA1': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA1/run_output_2000_2019_hydro_TC_WA1.nc',
    'WA2': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA2/run_output_2000_2019_hydro_TC_WA2.nc',
    'WA3': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA3/run_output_2000_2019_hydro_TC_WA3.nc',
    'WA4': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA4/run_output_2000_2019_hydro_TC_WA4.nc',
    'WA5': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA5/run_output_2000_2019_hydro_TC_WA5.nc',
    'WA6': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/WA6/run_output_2000_2019_hydro_TC_WA6.nc',
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
    
    if not os.path.exists(nc_path):
        print(f"  ✗ File not found")
        continue
    
    try:
        # Open NetCDF
        ds = xr.open_dataset(nc_path)
        
        print(f"  ✓ Opened NetCDF")
        
        # Get glacier IDs
        glacier_ids = [str(x) for x in ds['rgi_id'].values]
        n_glaciers = len(glacier_ids)
        
        # Calculate mass balance for 2000-2020
        volume_2000 = ds['volume'].sel(time=2000).sum()
        volume_2020 = ds['volume'].sel(time=2020).sum()
        area_2000 = ds['area'].sel(time=2000)
        
        # SMB in m w.e./yr
        total_area_m2 = area_2000.sum().values
        n_years = 20  # 2000-2020 period
        
        smb_m_per_yr = (volume_2020 - volume_2000) / total_area_m2 / n_years
        smb = float(smb_m_per_yr)  # Keep in m w.e./yr
        
        print(f"  SMB: {smb:.3f} m w.e./yr")
        
        # Get cluster glaciers from RGI
        cluster_glaciers = datos_rgi[datos_rgi['Cluster'] == cluster]['RGIId'].tolist()
        
        # Get geodetic observations
        gmb_data = geodetic_ref[geodetic_ref.index.isin(cluster_glaciers)]
        
        if len(gmb_data) > 0:
            gmb_weighted = np.average(gmb_data['dmdtda'], weights=gmb_data['area'])  # Keep in m w.e./yr
            gmb_error = np.average(gmb_data['err_dmdtda'], weights=gmb_data['area'])
            
            print(f"  GMB: {gmb_weighted:.3f} ± {gmb_error:.3f} m w.e./yr")
            print(f"  Glaciers: {n_glaciers}")
            
            results.append({
                'cluster': cluster,
                'SMB': smb,
                'GMB': gmb_weighted,
                'GMB_error': gmb_error,
                'n_glaciers': n_glaciers,
                'area_km2': float(total_area_m2 / 1e6),
                'bias': smb - gmb_weighted,
                'bias_pct': ((smb - gmb_weighted) / gmb_weighted) * 100
            })
        else:
            print(f"  ⚠ No geodetic data")
        
        ds.close()
        
    except Exception as e:
        print(f"  ✗ Error: {e}")

print(f"\n\nTotal clusters loaded: {len(results)}")

if len(results) == 0:
    print("❌ No data to plot!")
    exit(1)

##############################################################################
# CREATE COMPREHENSIVE PLOT
##############################################################################

df = pd.DataFrame(results)

# Sort by cluster name for better visualization
cluster_order = ['OT3', 'DA1', 'DA2', 'DA3', 'WA1', 'WA2', 'WA3', 'WA4', 'WA5', 'WA6']
df['cluster'] = pd.Categorical(df['cluster'], categories=cluster_order, ordered=True)
df = df.sort_values('cluster').reset_index(drop=True)

# Create figure with multiple subplots
fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

##############################################################################
# 1. Main comparison plot (SMB vs GMB)
##############################################################################
ax1 = fig.add_subplot(gs[0, :])

n = len(df)
x_pos = np.arange(n)

# SMB - circles
ax1.plot(x_pos - 0.15, df['SMB'], 'o', markersize=12, color='#e74c3c', 
       markeredgecolor='black', markeredgewidth=1.5, label='SMB (CR2MET Simulated)', zorder=5)

# GMB - diamonds with error bars
ax1.errorbar(x_pos + 0.15, df['GMB'], yerr=df['GMB_error'],
           fmt='D', markersize=12, color='darkred',
           markeredgecolor='black', markeredgewidth=1.5,
           ecolor='gray', capsize=6, capthick=1.5,
           linewidth=1.5, label='GMB (Geodetic Observed)', zorder=10)

ax1.axhline(y=0, color='black', linewidth=1, linestyle='--', alpha=0.5)

ax1.set_ylabel('Mass Balance (m w.e. yr⁻¹)', fontsize=13, fontweight='bold')
ax1.set_xlabel('Cluster', fontsize=13, fontweight='bold')
ax1.set_title('CR2MET Mass Balance Validation - All Chilean Glacier Clusters (2000-2020)', 
             fontsize=15, fontweight='bold', pad=15)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(df['cluster'], fontsize=12, fontweight='bold')
ax1.legend(loc='lower left', fontsize=11)
ax1.grid(axis='y', alpha=0.3)

# Add bias labels
for i, row in df.iterrows():
    bias = row['bias']
    bias_pct = row['bias_pct']
    y_pos = min(row['SMB'], row['GMB']) - 80
    ax1.text(i, y_pos, f'{bias:+.0f}\n({bias_pct:+.0f}%)',
           ha='center', va='top', fontsize=8,
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.6))

##############################################################################
# 2. Bias analysis
##############################################################################
ax2 = fig.add_subplot(gs[1, 0])

colors = ['green' if abs(b) < 0.03 else 'orange' if abs(b) < 0.10 else 'red' for b in df['bias']]
ax2.bar(x_pos, df['bias'], color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
ax2.axhline(y=0, color='black', linewidth=2)
ax2.set_ylabel('Bias (m w.e. yr⁻¹)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Cluster', fontsize=12, fontweight='bold')
ax2.set_title('SMB - GMB Bias by Cluster', fontsize=13, fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(df['cluster'], fontsize=10)
ax2.grid(axis='y', alpha=0.3)

# Add reference lines
ax2.axhline(y=0.03, color='orange', linewidth=1, linestyle='--', alpha=0.5, label='±0.03 m/yr')
ax2.axhline(y=-0.03, color='orange', linewidth=1, linestyle='--', alpha=0.5)
ax2.legend(fontsize=9)

##############################################################################
# 3. Glacier count and area
##############################################################################
ax3 = fig.add_subplot(gs[1, 1])

ax3_twin = ax3.twinx()
ax3.bar(x_pos - 0.2, df['n_glaciers'], width=0.4, color='steelblue', 
       alpha=0.7, label='Number of Glaciers', edgecolor='black')
ax3_twin.bar(x_pos + 0.2, df['area_km2'], width=0.4, color='coral', 
            alpha=0.7, label='Total Area (km²)', edgecolor='black')

ax3.set_ylabel('Number of Glaciers', fontsize=12, fontweight='bold', color='steelblue')
ax3_twin.set_ylabel('Total Area (km²)', fontsize=12, fontweight='bold', color='coral')
ax3.set_xlabel('Cluster', fontsize=12, fontweight='bold')
ax3.set_title('Cluster Size Distribution', fontsize=13, fontweight='bold')
ax3.set_xticks(x_pos)
ax3.set_xticklabels(df['cluster'], fontsize=10)
ax3.tick_params(axis='y', labelcolor='steelblue')
ax3_twin.tick_params(axis='y', labelcolor='coral')
ax3.legend(loc='upper left', fontsize=9)
ax3_twin.legend(loc='upper right', fontsize=9)

##############################################################################
# 4. Summary statistics table
##############################################################################
ax4 = fig.add_subplot(gs[2, :])
ax4.axis('off')

# Create summary table
summary_text = "SUMMARY STATISTICS\n" + "="*70 + "\n\n"
summary_text += f"Total Clusters: {len(df)}\n"
summary_text += f"Total Glaciers: {df['n_glaciers'].sum():.0f}\n"
summary_text += f"Total Area: {df['area_km2'].sum():.1f} km²\n\n"

summary_text += f"Mean SMB: {df['SMB'].mean():.3f} m w.e./yr\n"
summary_text += f"Mean GMB: {df['GMB'].mean():.3f} m w.e./yr\n"
summary_text += f"Overall Bias: {df['bias'].mean():.3f} m w.e./yr\n\n"

summary_text += f"Clusters with |Bias| < 0.03 m/yr: {len(df[df['bias'].abs() < 0.03])}/{len(df)}\n"
summary_text += f"Clusters with |Bias| < 0.10 m/yr: {len(df[df['bias'].abs() < 0.10])}/{len(df)}\n"
summary_text += f"Max Bias: {df['bias'].abs().max():.3f} m/yr ({df.loc[df['bias'].abs().idxmax(), 'cluster']})\n"

ax4.text(0.1, 0.8, summary_text, fontsize=11, family='monospace',
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

# Add detailed cluster table
table_data = []
for _, row in df.iterrows():
    table_data.append([
        row['cluster'],
        f"{row['n_glaciers']:.0f}",
        f"{row['area_km2']:.1f}",
        f"{row['SMB']:.3f}",
        f"{row['GMB']:.3f}",
        f"{row['bias']:+.3f}",
        f"{row['bias_pct']:+.1f}%"
    ])

table = ax4.table(cellText=table_data,
                 colLabels=['Cluster', 'N Glaciers', 'Area\n(km²)', 'SMB\n(m/yr)', 'GMB\n(m/yr)', 'Bias\n(m/yr)', 'Bias\n(%)'],
                 cellLoc='center',
                 loc='center',
                 bbox=[0.05, 0.05, 0.9, 0.5])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

# Color code bias cells
for i in range(1, len(df) + 1):
    bias = df.iloc[i-1]['bias']
    if abs(bias) < 0.03:
        color = 'lightgreen'
    elif abs(bias) < 0.10:
        color = 'lightyellow'
    else:
        color = 'lightcoral'
    table[(i, 5)].set_facecolor(color)
    table[(i, 6)].set_facecolor(color)

plt.tight_layout()

output = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/CR2MET_Complete_Analysis.png'
plt.savefig(output, dpi=300, bbox_inches='tight')
print(f"\n✓ Saved: {output}")

# Print detailed results
print("\n" + "="*70)
print("DETAILED RESULTS")
print("="*70)
for _, row in df.iterrows():
    print(f"{row['cluster']}: SMB={row['SMB']:7.1f}, GMB={row['GMB']:7.1f}, "
          f"Bias={row['bias']:+7.1f} ({row['bias_pct']:+5.1f}%), "
          f"N={row['n_glaciers']:.0f}, Area={row['area_km2']:.1f} km²")
print("="*70)

plt.show()