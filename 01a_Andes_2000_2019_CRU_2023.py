#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OGGM Glacier Simulations - CRU Climate Data
Multi-dataset comparison: CRU observational forcing

@author: Millie 
"""

##########################################################################
# Global initialization
##########################################################################

from oggm import cfg, utils, workflow, tasks
import logging
import numpy as np
import os
import pandas
import warnings

# Workaround for numpy.warnings issue
if not hasattr(np, 'warnings'):
    np.warnings = warnings

# OGGM initialization
cfg.initialize(logging_level='WARNING')
cfg.PARAMS['use_multiprocessing'] = False  # Set to False for macOS
cfg.PARAMS['continue_on_error'] = True
cfg.PARAMS['run_mb_calibration'] = True
cfg.PARAMS['store_model_geometry'] = True
cfg.PARAMS['border'] = 80
cfg.PARAMS['store_fl_diagnostics'] = True

cfg.PARAMS["climate_qc_months"] = 3
cfg.PARAMS["hydro_month_nh"] = 1
cfg.PARAMS["hydro_month_sh"] = 1
cfg.PARAMS["max_mu_star"] = 600

cfg.PARAMS["temp_all_solid"] = 0.0
cfg.PARAMS["temp_all_liq"] = 2.0 
cfg.PARAMS["temp_melt"] = 0

cfg.PARAMS['cfl_min_dt'] = 10

# Load glacier and parameter data
datos_rgi = pandas.read_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/RGI_BNA_Clusters.csv')
datos_param = pandas.read_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/LR_Pf.csv')

##########################################################################
# Main execution
##########################################################################

if __name__ == '__main__':
    
    # TEST MODE: Just DA1
    list_region = ['DA1']
    
    # FULL RUN: Uncomment to run all clusters
    # list_region = ['OT3','DA1','DA2','DA3','WA1','WA2','WA3','WA4','WA5','WA6']
    
    for zona in list_region:
        
        print(f"\n{'='*70}")
        print(f"PROCESSING CLUSTER: {zona} with CRU climate data")
        print(f"{'='*70}\n")
        
        # Output directory for CRU results
        salida = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CRU/' + zona + '/'
        os.makedirs(salida, exist_ok=True)
        cfg.PATHS['working_dir'] = salida
        
        # Extract glaciers for this cluster
        gdf_sel = datos_rgi[datos_rgi['Cluster'] == zona]
        gdf_sel = list(gdf_sel.RGIId)
        
        print(f"Number of glaciers in {zona}: {len(gdf_sel)}")
        
        # Extract parameters for this cluster
        param = datos_param[datos_param['Cluster'] == zona]
        LT_n = float(param.LR.iloc[0])
        Pf_n = float(param.Pf.iloc[0])
        
        print(f"Temperature lapse rate: {LT_n}")
        print(f"Precipitation factor: {Pf_n}")
        
        # Set parameters
        cfg.PARAMS["temp_default_gradient"] = LT_n
        cfg.PARAMS["prcp_scaling_factor"] = Pf_n
        cfg.PARAMS['use_winter_prcp_factor'] = False
        
        ###
        ### SIMULATION PERIOD 2000-2019
        ###
        
        # Setup output directories
        output_folder = salida
        rgi_version = '_' + zona
        border = 80
        output_base_dir = os.path.join(output_folder, 'RGI{}'.format(rgi_version), 'b_{:03d}'.format(border))
        sum_dir = os.path.join(output_base_dir, 'L3', 'summary')
        utils.mkdir(sum_dir)
        
        # Initialize glacier directories from preprocessed Level 2
        print("\nInitializing glacier directories...")
        gdirs = workflow.init_glacier_directories(gdf_sel, from_prepro_level=2,
                                                  prepro_base_url='https://cluster.klima.uni-bremen.de/~oggm/gdirs/oggm_v1.6/L1-L2_files/centerlines/',
                                                  prepro_border=80)
        
        print(f"Successfully initialized {len(gdirs)} glacier directories")
        
        # Process CRU climate data
        print("\nProcessing CRU climate data...")
        cfg.PARAMS['baseline_climate'] = 'CRU'
        from oggm.shop import cru
        workflow.execute_entity_task(cru.process_cru_data, gdirs)
        
        print("\nCalibrating mass balance...")
        utils.get_geodetic_mb_dataframe()
        workflow.execute_entity_task(tasks.mu_star_calibration_from_geodetic_mb, gdirs, ref_period='2000-01-01_2020-01-01')
        workflow.execute_entity_task(tasks.apparent_mb_from_any_mb, gdirs)
        
        print("\nRunning ice thickness inversion...")
        filter = border >= 20
        workflow.calibrate_inversion_from_consensus(gdirs, apply_fs_on_mismatch=True, error_on_mismatch=False, filter_inversion_output=filter)
        
        print("\nInitializing glaciers for simulation...")
        log = logging.getLogger(__name__)
        if border >= 20:
            workflow.execute_entity_task(tasks.init_present_time_glacier, gdirs)
        else:
            log.workflow('L3: for map border values < 20, wont initialize glaciers for the run.')
        
        compilacion = '_2000_2019_hydro_CRU_' + zona
        
        # Run simulations
        print("\nRunning glacier evolution simulations...")
        workflow.execute_entity_task(tasks.run_with_hydro, gdirs,
                             ys=1999,
                             ye=2020,
                             run_task=tasks.run_from_climate_data,
                             store_monthly_hydro=True,
                             ref_area_from_y0=True,
                             output_filesuffix=compilacion,
                             )
        
        # Compile statistics
        print("\nCompiling statistics...")
        rgi_reg = '_' + zona
        
        opath = os.path.join(sum_dir, 'glacier_statistics_{}.csv'.format(rgi_reg))
        utils.compile_glacier_statistics(gdirs, path=opath)
        
        opath = os.path.join(sum_dir, 'climate_statistics_{}.csv'.format(rgi_reg))
        utils.compile_climate_statistics(gdirs, path=opath)
        
        opath = os.path.join(sum_dir, 'fixed_geometry_mass_balance_{}.csv'.format(rgi_reg))
        utils.compile_fixed_geometry_mass_balance(gdirs, path=opath)
        
        # Compile run outputs
        print("\nCompiling run outputs...")
        ds2000 = utils.compile_run_output(gdirs, input_filesuffix=compilacion)
        output_file = os.path.join(salida, f'run_output{compilacion}.nc')
        ds2000.to_netcdf(output_file)
        
        print(f"\n{'='*70}")
        print(f"FINISHED PROCESSING CLUSTER: {zona}")
        print(f"{'='*70}")
        print(f"Results saved to: {salida}")
        print(f"{'='*70}\n")
