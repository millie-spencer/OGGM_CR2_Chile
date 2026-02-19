#!/usr/bin/env python3
"""
Multi-Dataset Comparison: CR2MET vs CRU vs ERA5
Comprehensive analysis of all three climate datasets
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
print("MULTI-DATASET COMPARISON: CR2MET vs CRU vs ERA5")
print("="*70)

# All 10 clusters
clusters = ['OT3', 'DA1', 'DA2', 'DA3', 'WA1', 'WA2', 'WA3', 'WA4', 'WA5', 'WA6']

# Dataset configurations
datasets = {
    'CR2MET': {
        'path': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/{}/run_output_2000_2019_hydro_TC_{}.nc',
        'color': '#e74c3c',
        'marker': 'o'
    },
    'CRU': {
        'path': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CRU/{}/run_output_2000_2019_hydro_CRU_{}.nc',
        'color': '#3498db',
        'marker': 's'
    },
    'ERA5': {
        'path': '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/ERA5/{}/run_output_2000_2019_hydro_ERA5_{}.nc',
        'color': '#2ecc71',
        'marker': '^'
    }
}

# Load RGI data
rgi_file = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/RGI_BNA_Clusters.csv'
datos_rgi = pd.read_csv(rgi_file)

# Load geodetic data
utils.get_geodetic_mb_dataframe()
geodetic_ref = utils.get_geodetic_mb_dataframe()
geodetic_ref = geodetic_ref[geodetic_ref['period'] == '2000-01-01_2020-01-01']

##############################################################################
# Extract data for all datasets and clusters
##############################################################################

all_results = []

for dataset_name, dataset_config in datasets.items():
    print(f"\n{dataset_name}:")
    
    for cluster in clusters:
        nc_path = dataset_config['path'].format(cluster, cluster)
        
        if not os.path.exists(nc_path):
            print(f"  ✗ {cluster}: File not found")
            continue
        
        try:
            # Open NetCDF
            ds = xr.open_dataset(nc_path)
            
            # Calculate SMB for 2000-2020
            volume_2000 = ds['volume'].sel(time=2000).sum()
            volume_2020 = ds['volume'].sel(time=2020).sum()
            area_2000 = ds['area'].sel(time=2000)
            
            total_area_m2 = area_2000.sum().values
            n_years = 20
            
            smb = float((volume_2020 - volume_2000) / total_area_m2 / n_years)
            
            # Get geodetic observations
            cluster_glaciers = datos_rgi[datos_rgi['Cluster'] == cluster]['RGIId'].tolist()
            gmb_data = geodetic_ref[geodetic_ref.index.isin(cluster_glaciers)]
            
            if len(gmb_data) > 0:
                gmb = np.average(gmb_data['dmdtda'], weights=gmb_data['area'])
                gmb_error = np.average(gmb_data['err_dmdtda'], weights=gmb_data['area'])
                
                all_results.append({
                    'dataset': dataset_name,
                    'cluster': cluster,
                    'SMB': smb,
                    'GMB': gmb,
                    'GMB_error': gmb_error,
                    'bias': smb - gmb,
                    'abs_bias': abs(smb - gmb),
                    'bias_pct': ((smb - gmb) / gmb) * 100,
                    'n_glaciers': len(ds['rgi_id']),
                    'area_km2': float(total_area_m2 / 1e6)
                })
                
                print(f"  ✓ {cluster}: SMB={smb:.3f}, GMB={gmb:.3f}, Bias={smb-gmb:+.3f}")
            
            ds.close()
            
        except Exception as e:
            print(f"  ✗ {cluster}: Error - {e}")

df = pd.DataFrame(all_results)

print(f"\n\nTotal records: {len(df)}")
print(f"Expected: {len(datasets) * len(clusters)} = {len(datasets)}x{len(clusters)}")

##############################################################################
# CREATE COMPREHENSIVE COMPARISON FIGURE
##############################################################################

fig = plt.figure(figsize=(20, 14))
gs = fig.add_gridspec(4, 3, hspace=0.35, wspace=0.3)

##############################################################################
# 1. SMB vs GMB comparison by dataset
##############################################################################

ax1 = fig.add_subplot(gs[0, :])

x_pos = np.arange(len(clusters))
width = 0.25

for i, (dataset_name, dataset_config) in enumerate(datasets.items()):
    df_dataset = df[df['dataset'] == dataset_name].sort_values('cluster')
    
    offset = (i - 1) * width
    ax1.scatter(x_pos + offset, df_dataset['SMB'], 
               s=150, color=dataset_config['color'], 
               marker=dataset_config['marker'],
               label=f'{dataset_name} SMB',
               edgecolors='black', linewidth=1.5, zorder=5)

# Add GMB reference
df_gmb = df[df['dataset'] == 'CR2MET'].sort_values('cluster')  # GMB same for all
ax1.errorbar(x_pos, df_gmb['GMB'], yerr=df_gmb['GMB_error'],
            fmt='D', markersize=12, color='darkred',
            markeredgecolor='black', markeredgewidth=1.5,
            ecolor='gray', capsize=5, capthick=1.5,
            linewidth=1.5, label='GMB (Geodetic)', zorder=10)

ax1.axhline(y=0, color='black', linewidth=1, linestyle='--', alpha=0.5)
ax1.set_ylabel('Mass Balance (m w.e. yr⁻¹)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Cluster', fontsize=14, fontweight='bold')
ax1.set_title('Multi-Dataset Comparison: Simulated vs Observed Mass Balance', 
             fontsize=16, fontweight='bold', pad=15)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(clusters, fontsize=12, fontweight='bold')
ax1.legend(loc='lower left', fontsize=11, ncol=4)
ax1.grid(axis='y', alpha=0.3)

##############################################################################
# 2. Bias comparison by dataset
##############################################################################

ax2 = fig.add_subplot(gs[1, 0])

for i, (dataset_name, dataset_config) in enumerate(datasets.items()):
    df_dataset = df[df['dataset'] == dataset_name].sort_values('cluster')
    offset = (i - 1) * width
    
    colors = [dataset_config['color'] if abs(b) < 0.05 else 'orange' 
              if abs(b) < 0.10 else 'red' for b in df_dataset['bias']]
    
    ax2.bar(x_pos + offset, df_dataset['bias'], width=width,
           color=colors, alpha=0.7, edgecolor='black', linewidth=1,
           label=dataset_name)

ax2.axhline(y=0, color='black', linewidth=2)
ax2.axhline(y=0.05, color='orange', linewidth=1, linestyle='--', alpha=0.5)
ax2.axhline(y=-0.05, color='orange', linewidth=1, linestyle='--', alpha=0.5)
ax2.set_ylabel('Bias (m w.e. yr⁻¹)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Cluster', fontsize=12, fontweight='bold')
ax2.set_title('Bias by Dataset and Cluster', fontsize=13, fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(clusters, fontsize=10, rotation=45)
ax2.legend(fontsize=10)
ax2.grid(axis='y', alpha=0.3)

##############################################################################
# 3. Mean absolute bias by dataset
##############################################################################

ax3 = fig.add_subplot(gs[1, 1])

mean_abs_bias = df.groupby('dataset')['abs_bias'].mean()
std_abs_bias = df.groupby('dataset')['abs_bias'].std()

colors_list = [datasets[ds]['color'] for ds in mean_abs_bias.index]

bars = ax3.bar(range(len(mean_abs_bias)), mean_abs_bias.values,
              yerr=std_abs_bias.values, color=colors_list, alpha=0.7,
              edgecolor='black', linewidth=1.5, capsize=10)

ax3.set_ylabel('Mean Absolute Bias (m w.e. yr⁻¹)', fontsize=12, fontweight='bold')
ax3.set_title('Dataset Performance', fontsize=13, fontweight='bold')
ax3.set_xticks(range(len(mean_abs_bias)))
ax3.set_xticklabels(mean_abs_bias.index, fontsize=11, fontweight='bold')
ax3.grid(axis='y', alpha=0.3)

# Add values on bars
for i, (bar, val) in enumerate(zip(bars, mean_abs_bias.values)):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

##############################################################################
# 4. RMSE and correlation
##############################################################################

ax4 = fig.add_subplot(gs[1, 2])

stats_data = []
for dataset_name in datasets.keys():
    df_dataset = df[df['dataset'] == dataset_name]
    rmse = np.sqrt(np.mean(df_dataset['bias']**2))
    corr = np.corrcoef(df_dataset['SMB'], df_dataset['GMB'])[0, 1]
    stats_data.append({'Dataset': dataset_name, 'RMSE': rmse, 'Correlation': corr})

stats_df = pd.DataFrame(stats_data)

x_stats = np.arange(len(stats_df))
ax4_twin = ax4.twinx()

bars1 = ax4.bar(x_stats - 0.2, stats_df['RMSE'], 0.4, 
               color='coral', alpha=0.7, label='RMSE', edgecolor='black')
bars2 = ax4_twin.bar(x_stats + 0.2, stats_df['Correlation'], 0.4,
                    color='steelblue', alpha=0.7, label='Correlation', edgecolor='black')

ax4.set_ylabel('RMSE (m w.e. yr⁻¹)', fontsize=12, fontweight='bold', color='coral')
ax4_twin.set_ylabel('Correlation (R)', fontsize=12, fontweight='bold', color='steelblue')
ax4.set_title('Statistical Metrics', fontsize=13, fontweight='bold')
ax4.set_xticks(x_stats)
ax4.set_xticklabels(stats_df['Dataset'], fontsize=11, fontweight='bold')
ax4.tick_params(axis='y', labelcolor='coral')
ax4_twin.tick_params(axis='y', labelcolor='steelblue')
ax4_twin.set_ylim(0, 1)

##############################################################################
# 5. Scatter plot: SMB vs GMB for each dataset
##############################################################################

for i, (dataset_name, dataset_config) in enumerate(datasets.items()):
    ax = fig.add_subplot(gs[2, i])
    
    df_dataset = df[df['dataset'] == dataset_name]
    
    ax.errorbar(df_dataset['GMB'], df_dataset['SMB'],
               xerr=df_dataset['GMB_error'],
               fmt=dataset_config['marker'], markersize=10,
               color=dataset_config['color'], markeredgecolor='black',
               markeredgewidth=1.5, ecolor='gray', capsize=5,
               alpha=0.7, linewidth=0)
    
    # 1:1 line
    lims = [min(df_dataset['GMB'].min(), df_dataset['SMB'].min()) - 0.2,
            max(df_dataset['GMB'].max(), df_dataset['SMB'].max()) + 0.2]
    ax.plot(lims, lims, 'k--', alpha=0.5, linewidth=2, label='1:1 line')
    
    # Best fit line
    z = np.polyfit(df_dataset['GMB'], df_dataset['SMB'], 1)
    p = np.poly1d(z)
    ax.plot(lims, p(lims), '-', color=dataset_config['color'], 
           linewidth=2, alpha=0.7, label=f'Best fit: y={z[0]:.2f}x+{z[1]:.2f}')
    
    ax.set_xlabel('GMB (m w.e. yr⁻¹)', fontsize=11, fontweight='bold')
    ax.set_ylabel('SMB (m w.e. yr⁻¹)', fontsize=11, fontweight='bold')
    ax.set_title(f'{dataset_name}', fontsize=12, fontweight='bold')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    
    # Add R² value
    r2 = np.corrcoef(df_dataset['SMB'], df_dataset['GMB'])[0, 1]**2
    ax.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax.transAxes,
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

##############################################################################
# 6. Summary statistics table
##############################################################################

ax6 = fig.add_subplot(gs[3, :])
ax6.axis('off')

summary_text = "SUMMARY STATISTICS\n" + "="*130 + "\n\n"

for dataset_name in datasets.keys():
    df_dataset = df[df['dataset'] == dataset_name]
    summary_text += f"\n{dataset_name}:\n"
    summary_text += f"  Mean Bias: {df_dataset['bias'].mean():+.4f} ± {df_dataset['bias'].std():.4f} m w.e. yr⁻¹\n"
    summary_text += f"  Mean Abs Bias: {df_dataset['abs_bias'].mean():.4f} m w.e. yr⁻¹\n"
    summary_text += f"  RMSE: {np.sqrt(np.mean(df_dataset['bias']**2)):.4f} m w.e. yr⁻¹\n"
    summary_text += f"  Correlation: {np.corrcoef(df_dataset['SMB'], df_dataset['GMB'])[0, 1]:.3f}\n"
    summary_text += f"  Clusters with |Bias| < 0.05 m/yr: {len(df_dataset[df_dataset['abs_bias'] < 0.05])}/{len(df_dataset)}\n"

ax6.text(0.05, 0.95, summary_text, fontsize=10, family='monospace',
        verticalalignment='top', transform=ax6.transAxes,
        bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

plt.tight_layout()

output = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Multi_Dataset_Comparison_Complete.png'
plt.savefig(output, dpi=300, bbox_inches='tight')
print(f"\n✓ Saved: {output}")

##############################################################################
# Save summary CSV
##############################################################################

csv_output = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Multi_Dataset_Summary.csv'
df.to_csv(csv_output, index=False)
print(f"✓ Saved: {csv_output}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE!")
print("="*70)

plt.show()
