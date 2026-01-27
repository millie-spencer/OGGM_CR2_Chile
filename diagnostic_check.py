#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script to investigate why simulations failed
"""

from oggm import cfg, utils, workflow
import pandas
import os

# Initialize OGGM
cfg.initialize(logging_level='WARNING')

# Paths
salida = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/DA1/'
cfg.PATHS['working_dir'] = salida

# Load glacier list
datos_rgi = pandas.read_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/RGI_BNA_Clusters.csv')
gdf_sel = datos_rgi[datos_rgi['Cluster'] == 'DA1']
gdf_sel = list(gdf_sel.RGIId)

print(f"Total glaciers in DA1: {len(gdf_sel)}")
print(f"Working directory: {salida}")

# Try to load glacier directories
try:
    gdirs = workflow.init_glacier_directories(gdf_sel, 
                                              from_prepro_level=2,
                                              prepro_base_url='https://cluster.klima.uni-bremen.de/~oggm/gdirs/oggm_v1.6/L1-L2_files/centerlines/',
                                              prepro_border=80,
                                              reset=False)  # Don't reset - load existing
    print(f"Successfully loaded {len(gdirs)} glacier directories")
except Exception as e:
    print(f"Error loading glacier directories: {e}")
    exit(1)

# Check status of each glacier
compilacion = '_2000_2019_hydro_TC_DA1'

status = {
    'has_climate': 0,
    'has_calibration': 0,
    'has_inversion': 0,
    'has_model_flowlines': 0,
    'has_diagnostics': 0,
    'has_fl_diagnostics': 0,
    'has_geometry': 0
}

failed_glaciers = []
successful_glaciers = []

print("\nChecking glacier status...")
for i, gdir in enumerate(gdirs):
    try:
        # Check what files exist
        has_climate = gdir.has_file('climate_historical')
        has_calib = gdir.has_file('local_mustar')
        has_inv = gdir.has_file('inversion_output')
        has_flowlines = gdir.has_file('model_flowlines')
        has_diag = gdir.has_file('model_diagnostics', filesuffix=compilacion)
        has_fl_diag = gdir.has_file('fl_diagnostics', filesuffix=compilacion)
        has_geom = gdir.has_file('model_geometry', filesuffix=compilacion)
        
        if has_climate: status['has_climate'] += 1
        if has_calib: status['has_calibration'] += 1
        if has_inv: status['has_inversion'] += 1
        if has_flowlines: status['has_model_flowlines'] += 1
        if has_diag: status['has_diagnostics'] += 1
        if has_fl_diag: status['has_fl_diagnostics'] += 1
        if has_geom: status['has_geometry'] += 1
        
        if has_diag:
            successful_glaciers.append(gdir.rgi_id)
        else:
            failed_glaciers.append({
                'rgi_id': gdir.rgi_id,
                'has_climate': has_climate,
                'has_calibration': has_calib,
                'has_inversion': has_inv,
                'has_flowlines': has_flowlines
            })
            
        # Progress
        if (i + 1) % 50 == 0:
            print(f"  Checked {i+1}/{len(gdirs)} glaciers...")
            
    except Exception as e:
        print(f"Error checking {gdir.rgi_id}: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC SUMMARY")
print("="*70)
print(f"\nTotal glaciers: {len(gdirs)}")
print(f"\nFile Status:")
print(f"  Climate data processed:    {status['has_climate']:4d} ({status['has_climate']/len(gdirs)*100:.1f}%)")
print(f"  Mass balance calibrated:   {status['has_calibration']:4d} ({status['has_calibration']/len(gdirs)*100:.1f}%)")
print(f"  Ice thickness inverted:    {status['has_inversion']:4d} ({status['has_inversion']/len(gdirs)*100:.1f}%)")
print(f"  Model flowlines ready:     {status['has_model_flowlines']:4d} ({status['has_model_flowlines']/len(gdirs)*100:.1f}%)")
print(f"  Simulations completed:     {status['has_diagnostics']:4d} ({status['has_diagnostics']/len(gdirs)*100:.1f}%)")
print(f"    - Model diagnostics:     {status['has_diagnostics']:4d}")
print(f"    - Flowline diagnostics:  {status['has_fl_diagnostics']:4d}")
print(f"    - Model geometry:        {status['has_geometry']:4d}")

print(f"\n" + "="*70)
print(f"SUCCESSFUL: {len(successful_glaciers)} glaciers")
print(f"FAILED: {len(failed_glaciers)} glaciers")
print("="*70)

if len(failed_glaciers) > 0:
    print("\nFirst 10 failed glaciers:")
    for i, fail in enumerate(failed_glaciers[:10]):
        print(f"\n{i+1}. {fail['rgi_id']}")
        print(f"   Climate: {fail['has_climate']}, Calibration: {fail['has_calibration']}, "
              f"Inversion: {fail['has_inversion']}, Flowlines: {fail['has_flowlines']}")
    
    # Check log files for first failed glacier
    if len(failed_glaciers) > 0:
        first_fail = failed_glaciers[0]['rgi_id']
        print(f"\n" + "="*70)
        print(f"Checking log file for {first_fail}:")
        print("="*70)
        
        try:
            # Find the glacier directory
            for gdir in gdirs:
                if gdir.rgi_id == first_fail:
                    log_file = gdir.get_filepath('log')
                    if os.path.exists(log_file):
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            # Print last 20 lines
                            print("\nLast 20 lines of log:")
                            print("".join(lines[-20:]))
                    else:
                        print("No log file found")
                    break
        except Exception as e:
            print(f"Error reading log: {e}")

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

if status['has_diagnostics'] == 0:
    print("\n❌ No simulations completed!")
    print("\nPossible causes:")
    print("1. Simulation code didn't run (check if init_present_time_glacier failed)")
    print("2. All glaciers failed during simulation")
    print("3. Working directory was reset before saving outputs")
    
    if status['has_model_flowlines'] == 0:
        print("\n⚠️  No glaciers initialized for modeling!")
        print("   The init_present_time_glacier task likely failed.")
        print("   Check error messages in the main script output.")
    
elif status['has_diagnostics'] < len(gdirs) * 0.5:
    print(f"\n⚠️  Only {status['has_diagnostics']/len(gdirs)*100:.1f}% of simulations completed")
    print("\nPossible causes:")
    print("1. Climate data issues for some glaciers")
    print("2. Numerical instabilities in glacier dynamics")
    print("3. Missing calibration data")
    print("\nRecommendation: Use 'continue_on_error=True' (already set)")
    print("The successful glaciers can still be analyzed.")
    
else:
    print(f"\n✅ {status['has_diagnostics']/len(gdirs)*100:.1f}% of simulations completed successfully!")
    print("\nYou can compile the successful runs with:")
    print("  ds = utils.compile_run_output(gdirs, input_filesuffix=compilacion)")

print("\n" + "="*70)
