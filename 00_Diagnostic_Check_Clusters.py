#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script to check which clusters are failing and why
"""

import pandas as pd
import os
from oggm import cfg, utils, workflow
import warnings
import numpy as np

# Workaround for numpy.warnings
if not hasattr(np, 'warnings'):
    np.warnings = warnings

# Initialize OGGM
cfg.initialize(logging_level='WARNING')
cfg.PARAMS['use_multiprocessing'] = False
cfg.PARAMS['continue_on_error'] = True

# Define paths
datos_rgi_path = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/RGI_BNA_Clusters.csv'
output_base = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/'

# Load cluster data
datos_rgi = pd.read_csv(datos_rgi_path)

# All clusters to check
clusters = ['OT3','DA1','DA2','DA3','WA1','WA2','WA3','WA4','WA5','WA6']

print("\n" + "="*70)
print("CLUSTER DIAGNOSTIC CHECK")
print("="*70)

for cluster in clusters:
    print(f"\n{'='*70}")
    print(f"CLUSTER: {cluster}")
    print(f"{'='*70}")
    
    # Get glaciers for this cluster
    gdf_sel = datos_rgi[datos_rgi['Cluster'] == cluster]
    n_glaciers = len(gdf_sel)
    total_area = gdf_sel['Area'].sum()
    
    print(f"  Total glaciers in RGI: {n_glaciers}")
    print(f"  Total area: {total_area:.2f} km²")
    
    if n_glaciers == 0:
        print(f"  ⚠ WARNING: No glaciers found for cluster {cluster}")
        continue
    
    # Check if output directory exists
    output_dir = f"{output_base}{cluster}/"
    if not os.path.exists(output_dir):
        print(f"  ⚠ Output directory doesn't exist: {output_dir}")
        continue
    
    # Check for compiled output
    compiled_file = f"{output_dir}run_output_2000_2019_hydro_TC_{cluster}.nc"
    if os.path.exists(compiled_file):
        print(f"  ✓ Compiled output exists")
        import xarray as xr
        try:
            ds = xr.open_dataset(compiled_file)
            n_simulated = len(ds.rgi_id)
            print(f"  ✓ Successfully simulated: {n_simulated}/{n_glaciers} glaciers ({n_simulated/n_glaciers*100:.1f}%)")
            ds.close()
        except Exception as e:
            print(f"  ✗ Error reading compiled file: {e}")
    else:
        print(f"  ✗ No compiled output found")
    
    # Try to initialize glacier directories to see what happens
    try:
        print(f"  Attempting to initialize glacier directories...")
        cfg.PATHS['working_dir'] = output_dir
        
        gdf_sel_list = list(gdf_sel.RGIId)
        
        gdirs = workflow.init_glacier_directories(
            gdf_sel_list, 
            from_prepro_level=2,
            prepro_base_url='https://cluster.klima.uni-bremen.de/~oggm/gdirs/oggm_v1.6/L1-L2_files/centerlines/',
            prepro_border=80
        )
        
        print(f"  ✓ Successfully initialized {len(gdirs)} glacier directories")
        
        # Check for existing run files
        n_with_runs = 0
        for gd in gdirs[:5]:  # Check first 5 as sample
            run_file = gd.get_filepath('model_run', filesuffix='_2000_2019_hydro')
            if os.path.exists(run_file):
                n_with_runs += 1
        
        if n_with_runs > 0:
            print(f"  ✓ Found run files (sample: {n_with_runs}/5)")
        else:
            print(f"  ✗ No run files found in sample")
            
    except Exception as e:
        print(f"  ✗ Error initializing directories: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
