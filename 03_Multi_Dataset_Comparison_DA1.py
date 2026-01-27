#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Dataset Climate Comparison for DA1 Cluster
Compares CR2MET, ERA5, and CRU glacier mass balance simulations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

##############################################################################
# Load comparison data from all three datasets
##############################################################################

# CR2MET
cr2_file = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA1/comparacion_gmb_smb_DA1_.csv'
cr2_data = pd.read_csv(cr2_file, header=None, index_col=0).T
cr2_data.columns = cr2_data.iloc[0]
cr2_data = cr2_data.drop(cr2_data.index[0])

# ERA5
era5_file = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/ERA5/DA1/comparacion_gmb_smb_DA1_.csv'
era5_data = pd.read_csv(era5_file, header=None, index_col=0).T
era5_data.columns = era5_data.iloc[0]
era5_data = era5_data.drop(era5_data.index[0])

# CRU
cru_file = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CRU/DA1/comparacion_gmb_smb_DA1_.csv'
cru_data = pd.read_csv(cru_file, header=None, index_col=0).T
cru_data.columns = cru_data.iloc[0]
cru_data = cru_data.drop(cru_data.index[0])

# Extract values
gmb_value = float(cr2_data['GMB'].values[0])
gmb_error = float(cr2_data['GMB_error'].values[0])

cr2_smb = float(cr2_data['SMB'].values[0])
era5_smb = float(era5_data['SMB'].values[0])
cru_smb = float(cru_data['SMB'].values[0])

cr2_area = float(cr2_data['area_oggm'].values[0])
era5_area = float(era5_data['area_oggm'].values[0])
cru_area = float(cru_data['area_oggm'].values[0])

cr2_n = float(cr2_data['n_g_oggm'].values[0])
era5_n = float(era5_data['n_g_oggm'].values[0])
cru_n = float(cru_data['n_g_oggm'].values[0])

##############################################################################
# Calculate statistics
##############################################################################

smb_values = np.array([cr2_smb, era5_smb, cru_smb])
smb_mean = np.mean(smb_values)
smb_std = np.std(smb_values, ddof=1)  # Sample std dev
smb_range = np.max(smb_values) - np.min(smb_values)

print("\n" + "="*70)
print("MULTI-DATASET COMPARISON - DA1 CLUSTER")
print("="*70)
print(f"\nGeodetic Mass Balance (GMB): {gmb_value:.1f} ± {gmb_error:.1f} mm w.e./yr")
print(f"\nSimulated Mass Balance (SMB) by Dataset:")
print(f"  CR2MET: {cr2_smb:.1f} mm/yr ({cr2_n:.0f} glaciers, {cr2_area:.1f} km²)")
print(f"  ERA5:   {era5_smb:.1f} mm/yr ({era5_n:.0f} glaciers, {era5_area:.1f} km²)")
print(f"  CRU:    {cru_smb:.1f} mm/yr ({cru_n:.0f} glaciers, {cru_area:.1f} km²)")
print(f"\nMulti-Dataset Statistics:")
print(f"  Mean SMB:     {smb_mean:.1f} mm/yr")
print(f"  Std Dev:      ±{smb_std:.1f} mm/yr (climate forcing uncertainty)")
print(f"  Range:        {smb_range:.1f} mm/yr")
print(f"  Coef. Var.:   {(smb_std/abs(smb_mean)*100):.1f}%")
print("="*70 + "\n")

##############################################################################
# Create comparison plots
##############################################################################

fig = plt.figure(figsize=(16, 10))

# Plot 1: Bar chart comparison
ax1 = plt.subplot(2, 3, 1)
datasets = ['CR2MET\n(2.5 km)', 'ERA5\n(~25 km)', 'CRU\n(~50 km)']
smb_vals = [cr2_smb, era5_smb, cru_smb]
colors = ['#e74c3c', '#3498db', '#2ecc71']

bars = ax1.bar(datasets, smb_vals, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
ax1.axhline(y=gmb_value, color='black', linestyle='--', linewidth=2, label=f'GMB: {gmb_value:.1f} mm/yr')
ax1.axhspan(gmb_value - gmb_error, gmb_value + gmb_error, alpha=0.2, color='gray', label='GMB uncertainty')
ax1.axhline(y=smb_mean, color='purple', linestyle=':', linewidth=2, label=f'Mean SMB: {smb_mean:.1f} mm/yr')

ax1.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=12, fontweight='bold')
ax1.set_title('Simulated vs Geodetic Mass Balance\nDA1 Cluster (2000-2019)', fontsize=13, fontweight='bold')
ax1.legend(loc='lower right', fontsize=9)
ax1.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar, val in zip(bars, smb_vals):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.1f}',
            ha='center', va='bottom' if height < 0 else 'top', 
            fontweight='bold', fontsize=10)

# Plot 2: Difference from GMB
ax2 = plt.subplot(2, 3, 2)
differences = [cr2_smb - gmb_value, era5_smb - gmb_value, cru_smb - gmb_value]
bars2 = ax2.bar(datasets, differences, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=2)
ax2.set_ylabel('Difference from GMB (mm w.e./yr)', fontsize=12, fontweight='bold')
ax2.set_title('Model Bias Relative to Observations', fontsize=13, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

# Add value labels
for bar, val in zip(bars2, differences):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.1f}\n({val/gmb_value*100:.1f}%)',
            ha='center', va='bottom' if height > 0 else 'top', 
            fontweight='bold', fontsize=9)

# Plot 3: Uncertainty breakdown
ax3 = plt.subplot(2, 3, 3)
uncertainty_sources = ['GMB\nObservational', 'Climate\nForcing']
uncertainty_values = [gmb_error, smb_std]
colors_unc = ['#95a5a6', '#e67e22']

bars3 = ax3.bar(uncertainty_sources, uncertainty_values, color=colors_unc, alpha=0.7, 
               edgecolor='black', linewidth=1.5)
ax3.set_ylabel('Uncertainty (mm w.e./yr)', fontsize=12, fontweight='bold')
ax3.set_title('Uncertainty Sources', fontsize=13, fontweight='bold')
ax3.grid(axis='y', alpha=0.3)

for bar, val in zip(bars3, uncertainty_values):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f'±{val:.1f}',
            ha='center', va='bottom', fontweight='bold', fontsize=11)

# Plot 4: Dataset characteristics
ax4 = plt.subplot(2, 3, 4)
characteristics = pd.DataFrame({
    'Dataset': datasets,
    'Resolution (km)': [2.5, 25, 50],
    'Glaciers': [cr2_n, era5_n, cru_n],
    'Area (km²)': [cr2_area, era5_area, cru_area]
})

ax4.axis('tight')
ax4.axis('off')
table = ax4.table(cellText=characteristics.values, 
                 colLabels=characteristics.columns,
                 cellLoc='center',
                 loc='center',
                 colColours=['#f0f0f0']*4)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)
ax4.set_title('Dataset Characteristics', fontsize=13, fontweight='bold', pad=20)

# Plot 5: Spread visualization
ax5 = plt.subplot(2, 3, 5)
x_pos = [1, 2, 3]
ax5.errorbar(x_pos, smb_vals, yerr=[[0,0,0], [0,0,0]], 
            fmt='o', markersize=12, color='black', capsize=5, linewidth=2)
for i, (x, y, c, label) in enumerate(zip(x_pos, smb_vals, colors, datasets)):
    ax5.scatter(x, y, s=300, color=c, alpha=0.7, edgecolor='black', linewidth=2, zorder=3)
    ax5.text(x, y, label.replace('\n', ' '), ha='center', va='center', 
            fontweight='bold', fontsize=9)

ax5.axhline(y=gmb_value, color='black', linestyle='--', linewidth=2, label='GMB')
ax5.axhspan(gmb_value - gmb_error, gmb_value + gmb_error, alpha=0.2, color='gray')
ax5.axhspan(smb_mean - smb_std, smb_mean + smb_std, alpha=0.2, color='purple', 
           label=f'±1σ climate uncertainty')

ax5.set_xlim(0.5, 3.5)
ax5.set_xticks([])
ax5.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=12, fontweight='bold')
ax5.set_title('Dataset Spread & Uncertainty Envelope', fontsize=13, fontweight='bold')
ax5.legend(loc='lower right', fontsize=9)
ax5.grid(axis='y', alpha=0.3)

# Plot 6: Summary statistics box
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

summary_text = f"""
SUMMARY STATISTICS - DA1 CLUSTER

Geodetic Observation (2000-2019):
  Mass Balance: {gmb_value:.1f} ± {gmb_error:.1f} mm w.e./yr
  
Multi-Dataset Ensemble:
  Mean SMB:      {smb_mean:.1f} mm w.e./yr
  Std Dev:       ±{smb_std:.1f} mm w.e./yr
  Range:         {smb_range:.1f} mm w.e./yr
  Coef. Var.:    {(smb_std/abs(smb_mean)*100):.1f}%
  
Climate Forcing Uncertainty:
  Absolute:      ±{smb_std:.1f} mm w.e./yr
  Relative:      ±{(smb_std/abs(smb_mean)*100):.1f}% of signal
  
Agreement with GMB:
  CR2MET: {cr2_smb - gmb_value:+.1f} mm/yr ({(cr2_smb - gmb_value)/gmb_value*100:+.1f}%)
  ERA5:   {era5_smb - gmb_value:+.1f} mm/yr ({(era5_smb - gmb_value)/gmb_value*100:+.1f}%)
  CRU:    {cru_smb - gmb_value:+.1f} mm/yr ({(cru_smb - gmb_value)/gmb_value*100:+.1f}%)
  
Interpretation:
  • All estimates within GMB uncertainty
  • CR2MET overestimates mass loss (20%)
  • ERA5 & CRU underestimate (3-4%)
  • Climate forcing contributes ±13 mm/yr uncertainty
"""

ax6.text(0.1, 0.95, summary_text, transform=ax6.transAxes,
        fontsize=10, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/Multi_Dataset_Comparison_DA1.png', 
           dpi=300, bbox_inches='tight')
print("✓ Saved: Multi_Dataset_Comparison_DA1.png")

# Create a simpler comparison plot
fig2, ax = plt.subplots(figsize=(10, 6))

x_pos = np.arange(len(datasets))
bars = ax.bar(x_pos, smb_vals, color=colors, alpha=0.8, edgecolor='black', linewidth=2, width=0.6)

# Add GMB reference
ax.axhline(y=gmb_value, color='black', linestyle='--', linewidth=2.5, 
          label=f'Geodetic Obs: {gmb_value:.1f} ± {gmb_error:.1f} mm/yr', zorder=1)
ax.axhspan(gmb_value - gmb_error, gmb_value + gmb_error, alpha=0.15, color='gray', zorder=0)

# Add ensemble mean
ax.axhline(y=smb_mean, color='purple', linestyle=':', linewidth=2.5, 
          label=f'Ensemble Mean: {smb_mean:.1f} ± {smb_std:.1f} mm/yr', zorder=1)

ax.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=14, fontweight='bold')
ax.set_xlabel('Climate Dataset', fontsize=14, fontweight='bold')
ax.set_title('Multi-Dataset Climate Forcing Comparison\nDA1 Cluster (Maipo Basin) • 2000-2019', 
            fontsize=15, fontweight='bold', pad=20)
ax.set_xticks(x_pos)
ax.set_xticklabels(datasets, fontsize=12)
ax.legend(loc='lower right', fontsize=11, framealpha=0.95)
ax.grid(axis='y', alpha=0.4, linestyle='--')

# Add value labels on bars
for bar, val, dataset in zip(bars, smb_vals, datasets):
    height = bar.get_height()
    diff = val - gmb_value
    ax.text(bar.get_x() + bar.get_width()/2., height,
           f'{val:.1f} mm/yr\n({diff:+.1f})',
           ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/Multi_Dataset_Comparison_Simple_DA1.png', 
           dpi=300, bbox_inches='tight')
print("✓ Saved: Multi_Dataset_Comparison_Simple_DA1.png")

plt.show()

print("\n" + "="*70)
print("COMPARISON PLOTS CREATED SUCCESSFULLY!")
print("="*70)
print("\nOutput files:")
print("  1. Multi_Dataset_Comparison_DA1.png (6-panel detailed)")
print("  2. Multi_Dataset_Comparison_Simple_DA1.png (simple bar chart)")
print("\nLocation: /Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/")
print("="*70 + "\n")
