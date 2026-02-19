#!/usr/bin/env python3
"""
Check if mu_star calibration is actually being applied to glaciers
"""

import pandas as pd
import numpy as np
import os
from oggm import cfg, utils, workflow
import warnings

if not hasattr(np, 'warnings'):
    np.warnings = warnings

print("\n" + "="*70)
print("CHECKING MU_STAR CALIBRATION")
print("="*70)

# Initialize
cfg.initialize(logging_level='WARNING')
cfg.PARAMS['use_multiprocessing'] = False

# Load RGI
rgi_file = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/RGI_BNA_Clusters.csv'
datos_rgi = pd.read_csv(rgi_file)

# Check DA1 (works well) and DA3 (has large bias)
clusters_to_check = ['DA1', 'DA3']

for cluster in clusters_to_check:
    print(f"\n{'='*70}")
    print(f"CLUSTER: {cluster}")
    print(f"{'='*70}")
    
    # Get a sample glacier
    cluster_glaciers = datos_rgi[datos_rgi['Cluster'] == cluster]['RGIId'].tolist()
    sample_glacier = cluster_glaciers[0]
    
    print(f"\nSample glacier: {sample_glacier}")
    
    # Set working directory
    output_dir = f'/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/{cluster}/'
    
    if not os.path.exists(output_dir):
        print(f"  ✗ Output directory doesn't exist")
        continue
    
    cfg.PATHS['working_dir'] = output_dir
    
    try:
        # Initialize glacier
        gdirs = workflow.init_glacier_directories(
            [sample_glacier],
            from_prepro_level=2,
            prepro_base_url='https://cluster.klima.uni-bremen.de/~oggm/gdirs/oggm_v1.6/L1-L2_files/centerlines/',
            prepro_border=80
        )
        
        gdir = gdirs[0]
        
        print(f"  ✓ Glacier directory initialized")
        
        # Check if mu_star exists in climate file
        try:
            import xarray as xr
            climate_file = gdir.get_filepath('climate_historical')
            
            if os.path.exists(climate_file):
                ds = xr.open_dataset(climate_file)
                
                # Check for mu_star
                if 'mu_star' in ds.attrs:
                    mu_star = ds.attrs['mu_star']
                    print(f"  ✓ mu_star found: {mu_star:.2f}")
                else:
                    print(f"  ✗ mu_star NOT found in climate file!")
                    print(f"    Available attrs: {list(ds.attrs.keys())}")
                
                ds.close()
            else:
                print(f"  ✗ Climate file doesn't exist")
                
        except Exception as e:
            print(f"  ✗ Error reading climate: {e}")
        
        # Check if apparent_mb file exists
        try:
            mb_file = gdir.get_filepath('apparent_mb')
            if os.path.exists(mb_file):
                print(f"  ✓ apparent_mb file exists")
            else:
                print(f"  ⚠ apparent_mb file does NOT exist")
        except Exception as e:
            print(f"  ⚠ Cannot check apparent_mb: {e}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "="*70)
print("DIAGNOSIS:")
print("="*70)
print("\nIf mu_star exists and apparent_mb exists:")
print("  → Calibration is working")
print("\nIf missing:")
print("  → Calibration didn't work properly")
print("="*70)
