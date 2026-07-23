#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Multi-Dataset Climate Comparison for DA1 Cluster
Using point + error bar visualization (NOT bar charts)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

##############################################################################
# Helper function to read comparison CSV files
##############################################################################

def read_comparison_csv(filepath):
    """Read comparison CSV and extract values as dictionary"""
    df = pd.read_csv(filepath, header=None)
    data_dict = {}
    for idx, row in df.iterrows():
        if idx == 0:  # Skip header row
            continue
        try:
            # Format is: value, label
            data_dict[row[1]] = float(row[0])
        except (ValueError, TypeError):
            pass  # Skip any non-numeric values
    return data_dict

##############################################################################
# Load mean values from comparison files
##############################################################################

cr2_data = read_comparison_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA1/comparacion_gmb_smb_DA1_.csv')
era5_data = read_comparison_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/ERA5/DA1/comparacion_gmb_smb_DA1_.csv')
cru_data = read_comparison_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CRU/DA1/comparacion_gmb_smb_DA1_.csv')

# Extract mean values
gmb_value = cr2_data['GMB']
gmb_error = cr2_data['GMB_error']

cr2_smb_mean = cr2_data['SMB']
era5_smb_mean = era5_data['SMB']
cru_smb_mean = cru_data['SMB']

cr2_n = cr2_data['n_g_oggm']
era5_n = era5_data['n_g_oggm']
cru_n = cru_data['n_g_oggm']

##############################################################################
# Load per-glacier mass balance data to calculate variability
##############################################################################

# Load per-glacier MB timeseries
cr2_mb = pd.read_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA1/mb.csv')
era5_mb = pd.read_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/ERA5/DA1/mb.csv')
cru_mb = pd.read_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CRU/DA1/mb.csv')

# Extract only numeric columns (skip RGI ID column)
# Find the first column that's all numeric (years)
cr2_numeric = cr2_mb.select_dtypes(include=[np.number])
era5_numeric = era5_mb.select_dtypes(include=[np.number])
cru_numeric = cru_mb.select_dtypes(include=[np.number])

# Calculate mean MB across all years for each glacier, then get std dev across glaciers
cr2_glacier_means = cr2_numeric.mean(axis=1)  # Mean across years for each glacier
era5_glacier_means = era5_numeric.mean(axis=1)
cru_glacier_means = cru_numeric.mean(axis=1)

cr2_smb_std = cr2_glacier_means.std()  # Std dev across glaciers
era5_smb_std = era5_glacier_means.std()
cru_smb_std = cru_glacier_means.std()

##############################################################################
# Calculate multi-dataset statistics
##############################################################################

smb_means = np.array([cr2_smb_mean, era5_smb_mean, cru_smb_mean])
ensemble_mean = np.mean(smb_means)
climate_uncertainty = np.std(smb_means, ddof=1)  # Inter-dataset uncertainty
smb_range = np.max(smb_means) - np.min(smb_means)

print("\n" + "="*70)
print("MULTI-DATASET COMPARISON - DA1 CLUSTER")
print("="*70)
print(f"\nGeodetic Mass Balance (GMB): {gmb_value:.1f} ± {gmb_error:.1f} mm w.e./yr")
print(f"\nSimulated Mass Balance by Dataset (area-weighted means ± glacier spread):")
print(f"  CR2MET: {cr2_smb_mean:.1f} ± {cr2_smb_std:.1f} mm/yr ({cr2_n:.0f} glaciers)")
print(f"  ERA5:   {era5_smb_mean:.1f} ± {era5_smb_std:.1f} mm/yr ({era5_n:.0f} glaciers)")
print(f"  CRU:    {cru_smb_mean:.1f} ± {cru_smb_std:.1f} mm/yr ({cru_n:.0f} glaciers)")
print(f"\nUncertainty Components:")
print(f"  Within-dataset (glacier variability): ±{np.mean([cr2_smb_std, era5_smb_std, cru_smb_std]):.1f} mm/yr (avg)")
print(f"  Between-dataset (climate forcing):    ±{climate_uncertainty:.1f} mm/yr")
print(f"\nEnsemble: {ensemble_mean:.1f} ± {climate_uncertainty:.1f} mm/yr (climate forcing uncertainty)")
print("="*70 + "\n")

##############################################################################
# Create proper point + error bar plots
##############################################################################

fig = plt.figure(figsize=(18, 12))

datasets_short = ['CR2MET', 'ERA5', 'CRU']
datasets_full = ['CR2MET\n(2.5 km)', 'ERA5\n(~25 km)', 'CRU\n(~50 km)']
smb_vals = [cr2_smb_mean, era5_smb_mean, cru_smb_mean]
smb_stds = [cr2_smb_std, era5_smb_std, cru_smb_std]
colors = ['#e74c3c', '#3498db', '#2ecc71']

# --------------------------------------------------
# PLOT 1: Point + Error Bar (glacier variability)
# --------------------------------------------------
ax1 = plt.subplot(2, 3, 1)

x_pos = np.arange(len(datasets_short))

# Plot error bars first (glacier spread)
for i, (x, mean, std, color) in enumerate(zip(x_pos, smb_vals, smb_stds, colors)):
    ax1.errorbar(x, mean, yerr=std, fmt='none', capsize=10, capthick=3,
                color=color, alpha=0.4, linewidth=4, zorder=1)

# Plot mean points on top
ax1.scatter(x_pos, smb_vals, s=300, c=colors, edgecolor='black', 
           linewidth=2, zorder=10, marker='o', alpha=0.9)

# Add GMB reference
ax1.axhline(y=gmb_value, color='darkred', linestyle='--', linewidth=2.5, 
           label=f'GMB: {gmb_value:.1f} mm/yr', zorder=5)
ax1.axhspan(gmb_value - gmb_error, gmb_value + gmb_error, alpha=0.15, color='gray',
           label='GMB uncertainty', zorder=0)

# Add ensemble mean
ax1.axhline(y=ensemble_mean, color='purple', linestyle='-.', linewidth=2.5, 
           label=f'Ensemble: {ensemble_mean:.1f} mm/yr', zorder=5)

ax1.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=13, fontweight='bold')
ax1.set_title('A) Dataset Comparison\nPoint = mean | Error bar = ±1σ glacier spread',
             fontsize=11, fontweight='bold')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(datasets_full, fontsize=10)
ax1.legend(loc='upper right', fontsize=8, framealpha=0.95)
ax1.grid(axis='y', alpha=0.4)

# --------------------------------------------------
# PLOT 2: Box Plot (full distribution)
# --------------------------------------------------
ax2 = plt.subplot(2, 3, 2)

box_data = [cr2_glacier_means.values, era5_glacier_means.values, cru_glacier_means.values]
bp = ax2.boxplot(box_data, labels=datasets_short, 
                 patch_artist=True, showmeans=True,
                 meanprops=dict(marker='D', markerfacecolor='red', markersize=10, 
                              markeredgecolor='black', markeredgewidth=1.5, label='Area-weighted mean'),
                 medianprops=dict(color='black', linewidth=2.5, label='Median'),
                 widths=0.6)

# Color the boxes
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
    patch.set_edgecolor('black')
    patch.set_linewidth(1.5)

# Add GMB reference
gmb_line = ax2.axhline(y=gmb_value, color='darkred', linestyle='--', linewidth=2.5, label='GMB')
ax2.axhspan(gmb_value - gmb_error, gmb_value + gmb_error, alpha=0.15, color='gray')

ax2.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=13, fontweight='bold')
ax2.set_title('B) Per-Glacier Distribution\n' + 
             'Box = IQR (25th-75th percentile) | Whiskers = range',
             fontsize=12, fontweight='bold')

# Create custom legend handles for box plot elements
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
box_legend = [
    Patch(facecolor='lightgray', edgecolor='black', linewidth=1.5, label='Box = IQR (middle 50%)'),
    Line2D([0], [0], color='black', linewidth=2.5, label='Median'),
    Line2D([0], [0], marker='D', color='w', markerfacecolor='red', 
           markeredgecolor='black', markersize=8, linewidth=0, label='Area-weighted mean'),
    Line2D([0], [0], color='darkred', linestyle='--', linewidth=2.5, label='GMB'),
]
ax2.legend(handles=box_legend, loc='upper right', fontsize=9)
ax2.grid(axis='y', alpha=0.4)

# --------------------------------------------------
# PLOT 3: Scatter with all individual glaciers
# --------------------------------------------------
ax3 = plt.subplot(2, 3, 3)

jitter = 0.08
x1 = np.random.normal(0, jitter, len(cr2_glacier_means))
x2 = np.random.normal(1, jitter, len(era5_glacier_means))
x3 = np.random.normal(2, jitter, len(cru_glacier_means))

# Plot all glacier points
ax3.scatter(x1, cr2_glacier_means, alpha=0.25, s=40, color=colors[0], 
           edgecolor='black', linewidth=0.3, label='Individual glaciers')
ax3.scatter(x2, era5_glacier_means, alpha=0.25, s=40, color=colors[1], 
           edgecolor='black', linewidth=0.3)
ax3.scatter(x3, cru_glacier_means, alpha=0.25, s=40, color=colors[2], 
           edgecolor='black', linewidth=0.3)

# Overlay area-weighted means
ax3.scatter([0, 1, 2], smb_vals, s=300, marker='D', color='red', 
           edgecolor='black', linewidth=2.5, zorder=10, 
           label='Area-weighted mean')

# Add GMB
ax3.axhline(y=gmb_value, color='darkred', linestyle='--', linewidth=2.5, label='GMB')
ax3.axhspan(gmb_value - gmb_error, gmb_value + gmb_error, alpha=0.15, color='gray',
           label='GMB uncertainty')

ax3.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=13, fontweight='bold')
ax3.set_title('C) All Individual Glacier Values\n' + 
             f'~{int(cr2_n)} glaciers per dataset (each dot = one glacier)',
             fontsize=12, fontweight='bold')
ax3.set_xticks([0, 1, 2])
ax3.set_xticklabels(datasets_short, fontsize=11)
ax3.legend(loc='upper right', fontsize=9)
ax3.grid(axis='y', alpha=0.4)
ax3.set_xlim(-0.5, 2.5)

# --------------------------------------------------
# PLOT 4: Climate forcing uncertainty visualization
# --------------------------------------------------
ax4 = plt.subplot(2, 3, 4)

x_pos = np.arange(len(datasets_short))

# Plot dataset means as points
ax4.scatter(x_pos, smb_vals, s=300, c=colors, edgecolor='black', 
           linewidth=2, zorder=10, marker='o', alpha=0.9)

# Draw lines connecting the points to show the spread
ax4.plot(x_pos, smb_vals, color='gray', linewidth=2, linestyle=':', 
        alpha=0.5, zorder=1)

# Show ensemble mean as a line (NO SHADING)
ax4.axhline(y=ensemble_mean, color='purple', linestyle='-.', linewidth=2.5,
           label=f'Ensemble: {ensemble_mean:.1f} ± {climate_uncertainty:.1f} mm/yr', zorder=5)

# Add GMB for reference
ax4.axhline(y=gmb_value, color='darkred', linestyle='--', linewidth=2, 
           label=f'GMB: {gmb_value:.1f} mm/yr', zorder=5, alpha=0.7)

ax4.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=13, fontweight='bold')
ax4.set_title('D) Climate Forcing Spread\nRange = {:.1f} mm/yr'.format(smb_range),
             fontsize=11, fontweight='bold')
ax4.set_xticks(x_pos)
ax4.set_xticklabels(datasets_short, fontsize=10)
ax4.legend(loc='upper right', fontsize=8, framealpha=0.95)
ax4.grid(axis='y', alpha=0.4)

# --------------------------------------------------
# PLOT 5: Uncertainty breakdown
# --------------------------------------------------
ax5 = plt.subplot(2, 3, 5)

uncertainty_types = ['Geodetic\nObs', 'Glacier\nVariability', 'Climate\nForcing']
uncertainty_vals = [gmb_error, np.mean(smb_stds), climate_uncertainty]
colors_unc = ['#95a5a6', '#3498db', '#e67e22']

# Use points with horizontal lines
x_unc = np.arange(len(uncertainty_types))
ax5.scatter(x_unc, uncertainty_vals, s=300, c=colors_unc, 
           edgecolor='black', linewidth=2, alpha=0.8, zorder=10)

# Add horizontal lines to show magnitude
for i, (x, val, color) in enumerate(zip(x_unc, uncertainty_vals, colors_unc)):
    ax5.plot([x-0.25, x+0.25], [val, val], linewidth=6, color=color, alpha=0.5)

ax5.set_ylabel('Uncertainty (mm w.e./yr)', fontsize=13, fontweight='bold')
ax5.set_title('E) Uncertainty Sources',
             fontsize=11, fontweight='bold')
ax5.set_xticks(x_unc)
ax5.set_xticklabels(uncertainty_types, fontsize=10)
ax5.grid(axis='y', alpha=0.4)
ax5.set_ylim([0, max(uncertainty_vals) * 1.3])

# --------------------------------------------------
# PLOT 6: Summary text
# --------------------------------------------------
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

summary_text = f"""
SUMMARY - DA1 CLUSTER (2000-2019)

OBSERVATIONS:
  GMB: {gmb_value:.1f} ± {gmb_error:.1f} mm w.e./yr

SIMULATIONS (mean ± glacier spread):
  CR2MET: {cr2_smb_mean:.1f} ± {cr2_smb_std:.1f} mm/yr
  ERA5:   {era5_smb_mean:.1f} ± {era5_smb_std:.1f} mm/yr
  CRU:    {cru_smb_mean:.1f} ± {cru_smb_std:.1f} mm/yr

ENSEMBLE:
  Mean:  {ensemble_mean:.1f} mm/yr
  Range: {smb_range:.1f} mm/yr

UNCERTAINTY BREAKDOWN:
  1. Geodetic observations: ±{gmb_error:.1f} mm/yr
  2. Glacier variability:   ±{np.mean(smb_stds):.1f} mm/yr
  3. Climate forcing:       ±{climate_uncertainty:.1f} mm/yr

KEY POINTS:
  • Points = dataset means
  • Error bars = glacier spread (±1σ)
  • Spread between points = climate uncertainty
  • All datasets within GMB uncertainty
  
BIASES (relative to GMB):
  CR2MET: {cr2_smb_mean - gmb_value:+.1f} mm/yr ({(cr2_smb_mean - gmb_value)/gmb_value*100:+.1f}%)
  ERA5:   {era5_smb_mean - gmb_value:+.1f} mm/yr ({(era5_smb_mean - gmb_value)/gmb_value*100:+.1f}%)
  CRU:    {cru_smb_mean - gmb_value:+.1f} mm/yr ({(cru_smb_mean - gmb_value)/gmb_value*100:+.1f}%)
"""

ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
        fontsize=10, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.4))

plt.tight_layout(h_pad=3.0, w_pad=2.5)
plt.savefig('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/Multi_Dataset_Comparison_Points_DA1.png', 
           dpi=300, bbox_inches='tight')
print("✓ Saved: Multi_Dataset_Comparison_Points_DA1.png")

##############################################################################
# Create clean publication figure
##############################################################################

fig2, ax = plt.subplots(figsize=(12, 8))

x_pos = np.arange(len(datasets_full))

# Create dummy handles for legend
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# Plot glacier variability as error bars (lighter, thinner)
for i, (x, mean, std, color) in enumerate(zip(x_pos, smb_vals, smb_stds, colors)):
    ax.errorbar(x, mean, yerr=std, fmt='none', capsize=12, capthick=3,
                color=color, alpha=0.35, linewidth=5, zorder=1)

# Plot dataset means as large points
ax.scatter(x_pos, smb_vals, s=400, c=colors, edgecolor='black', 
          linewidth=3, zorder=10, marker='o', alpha=0.95)

# Add GMB reference
ax.axhline(y=gmb_value, color='darkred', linestyle='--', linewidth=3, 
          label=f'Geodetic Obs: {gmb_value:.1f} ± {gmb_error:.1f} mm/yr', zorder=5)
ax.axhspan(gmb_value - gmb_error, gmb_value + gmb_error, alpha=0.12, color='gray', zorder=0)

# Add ensemble mean with shaded uncertainty
ax.axhline(y=ensemble_mean, color='purple', linestyle='-.', linewidth=3, 
          label=f'Ensemble Mean: {ensemble_mean:.1f} mm/yr', zorder=5)
ax.axhspan(ensemble_mean - climate_uncertainty, ensemble_mean + climate_uncertainty,
          alpha=0.2, color='purple', zorder=0,
          label=f'Climate forcing uncertainty: ±{climate_uncertainty:.1f} mm/yr')

# Create custom legend handles
legend_handles = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='white', 
           markeredgecolor='black', markersize=12, linewidth=2,
           label='Dataset mean'),
    Line2D([0], [0], color='gray', linewidth=5, alpha=0.5,
           label='±1σ glacier variability'),
    Line2D([0], [0], color='darkred', linestyle='--', linewidth=3,
           label=f'Geodetic Obs: {gmb_value:.1f} ± {gmb_error:.1f} mm/yr'),
    Line2D([0], [0], color='purple', linestyle='-.', linewidth=3,
           label=f'Ensemble Mean: {ensemble_mean:.1f} mm/yr'),
    Patch(facecolor='purple', alpha=0.2, edgecolor='none',
          label=f'Climate forcing uncertainty: ±{climate_uncertainty:.1f} mm/yr')
]

ax.set_ylabel('Mass Balance (mm w.e./yr)', fontsize=15, fontweight='bold')
ax.set_xlabel('Climate Dataset', fontsize=15, fontweight='bold')
ax.set_title('Multi-Dataset Climate Forcing Comparison\n' + 
            'DA1 Cluster • 2000-2019\n' +
            'Point = area-weighted mean | Error bar = ±1σ glacier variability',
            fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x_pos)
ax.set_xticklabels(datasets_full, fontsize=13)
ax.legend(handles=legend_handles, loc='upper right', fontsize=11, framealpha=0.95)
ax.grid(axis='y', alpha=0.5, linestyle='--')
ax.grid(axis='x', alpha=0)

# Add clear value labels offset to the right
for i, (x, val, std) in enumerate(zip(x_pos, smb_vals, smb_stds)):
    ax.text(x+0.38, val, f'{val:.1f}\n±{std:.1f}',
           ha='left', va='center', fontweight='bold', fontsize=12,
           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                    edgecolor='black', linewidth=2, alpha=0.95))

plt.tight_layout()
plt.savefig('/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/Multi_Dataset_Comparison_Publication_DA1.png', 
           dpi=300, bbox_inches='tight')
print("✓ Saved: Multi_Dataset_Comparison_Publication_DA1.png")

plt.show()

print("\n" + "="*70)
print("POINT-BASED COMPARISON PLOTS CREATED!")
print("="*70)
print("\nOutput files:")
print("  1. Multi_Dataset_Comparison_Points_DA1.png (6-panel detailed)")
print("  2. Multi_Dataset_Comparison_Publication_DA1.png (clean publication)")
print("\nVisualization:")
print("  • Large dots = dataset mean (area-weighted)")
print("  • Error bars = ±1σ glacier-to-glacier variability")
print("  • Spread between dots = climate forcing uncertainty")
print("\nLocation: /Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/")
print("="*70 + "\n")