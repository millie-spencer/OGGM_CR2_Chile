#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OGGM Validation Script - CR2MET Climate Data
Compares model output (SMB) to geodetic observations (GMB)
"""

##########################################################################
# Global initialization
##########################################################################

# Python module import
from oggm import cfg, utils, workflow, tasks, graphics
import matplotlib.pyplot as plt
import logging
from oggm.core.massbalance import MultipleFlowlineMassBalance
import xarray as xr
import numpy as np
import pandas as pd
import os

# OGGM initialization
cfg.initialize(logging_level='WARNING')
cfg.PARAMS['use_multiprocessing'] = False  # FIXED: Disabled for macOS compatibility
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

# Load glacier and parameter data
datos_rgi = pd.read_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/RGI_BNA_Clusters.csv')
datos_param = pd.read_csv('/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/LR_Pf.csv')

# Base directory
output_base = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/CR2MET/'

##########################################################################
# Main execution (FIXED: Wrapped in if __name__ == '__main__')
##########################################################################

if __name__ == '__main__':
    
    # TEST MODE: Process only one cluster
    # Change 'DA1' to match what you ran in Script 1
    list_region = ['DA1']  # TESTING: Just one cluster
    
    # FULL RUN: Uncomment line below to process all clusters
    # list_region = ['OT3','DA1','DA2','DA3','WA1','WA2','WA3','WA4','WA5','WA6']
    
    for zona in list_region:
        
        print(f"\n{'='*60}")
        print(f"Validating cluster: {zona}")
        print(f"{'='*60}\n")
        
        # Set working directory
        salida = output_base + zona + '/'
        cfg.PATHS['working_dir'] = salida
        compilacion_zona = salida + 'run_output_2000_2019_hydro_TC_' + zona + '.nc'
        
        # Check if simulation output exists
        if not os.path.exists(compilacion_zona):
            print(f"⚠ Warning: Output file not found for {zona}")
            print(f"Expected: {compilacion_zona}")
            print("Skipping this cluster...\n")
            continue
        
        # Extract glaciers for this cluster
        gdf_sel = datos_rgi[datos_rgi['Cluster'] == zona]
        gdf_sel = list(gdf_sel.RGIId)
        
        # Extract parameters for this cluster
        param = datos_param[datos_param['Cluster'] == zona]
        LT_n = float(param.LR.iloc[0])  # FIXED: Use .iloc[0]
        Pf_n = float(param.Pf.iloc[0])  # FIXED: Use .iloc[0]
        
        # Set parameters
        cfg.PARAMS["temp_default_gradient"] = LT_n
        cfg.PARAMS["prcp_scaling_factor"] = Pf_n
        
        # Load simulation results
        print("Loading simulation output...")
        zonax = xr.open_dataset(compilacion_zona)
        rgi_id = zonax['rgi_id'].values
        area = zonax['area'].values
        
        # Calculate total RGI area for this cluster
        rgi_area = datos_rgi[datos_rgi['Cluster'] == zona]
        rgi_area = rgi_area.Area.sum()
        
        ###########################################################################
        # Process area data
        ###########################################################################
        
        ID_area = pd.DataFrame(area)
        ID_rgi = pd.DataFrame(rgi_id)
        ID_rgi.rename(columns={ID_rgi.columns[0]: 'id'}, inplace=True)
        
        # Extract area for year 2000 (should be at index 10)
        ID_area = pd.DataFrame(ID_area.iloc[10])
        ID_area.rename(columns={ID_area.columns[0]: 'area'}, inplace=True)
        ID_area = pd.concat([ID_rgi.reset_index(drop=True), ID_area], axis=1)
        ID_area = ID_area.dropna(axis=0)
        max_n = ID_area[ID_area.columns[0]].count()
        ID_area['number'] = range(0, max_n)
        ID_data = ID_area.number.values.tolist()
        ID_rgi_id = ID_area.id.values.tolist()
        
        print(f"Processing {max_n} glaciers with valid area data")
        
        ###########################################################################
        # Calculate mass balance
        ###########################################################################
        
        print("Calculating mass balance...")
        
        # Initialize glacier directories
        gdirs = workflow.init_glacier_directories(ID_rgi_id)
        
        # Calculate specific mass balance for each glacier
        lista = []
        for i in ID_data:
            x = MultipleFlowlineMassBalance(gdirs[i], use_inversion_flowlines=True)
            lista.append(x)
        
        years = np.arange(2000, 2022)
        mb = []
        for i in lista:
            xx = i.get_specific_mb(year=years)
            mb.append(xx)
        
        mb_per_glacier = pd.DataFrame(mb)
        
        # Add RGI IDs
        mb_per_glacier_id = mb_per_glacier.copy()
        mb_per_glacier_id['rgi_id'] = ID_rgi_id
        
        # Save per-glacier mass balance
        c = salida + 'mb.csv'
        mb_per_glacier_id.to_csv(c, index=False)
        print(f"✓ Saved: mb.csv")
        
        ###########################################################################
        # Calculate area-weighted mean mass balance
        ###########################################################################
        
        areas = ID_area.area.values.tolist()     
        areas = np.divide(areas, 1000000)
        
        mb_mean = pd.DataFrame()
        itera = np.arange(0, 22).tolist()
        
        for i in itera:
            mb_list = mb_per_glacier[i].tolist()
            avg = np.average(mb_list, axis=0, weights=areas)
            data = {'itera': [i], 'mb': [avg]}
            df = pd.DataFrame(data)
            mb_mean = pd.concat([mb_mean, df], axis=0)
        
        mb_mean['year'] = np.arange(2000, 2022)
        c = salida + 'mb_promedio.csv'
        mb_mean.to_csv(c, index=False)
        print(f"✓ Saved: mb_promedio.csv")
        
        ###########################################################################
        # Compare with geodetic mass balance
        ###########################################################################
        
        print("Comparing with geodetic observations...")
        
        gmb = utils.get_geodetic_mb_dataframe()
        gdf_sel_RGIId_list = ID_rgi_id
        lista = pd.DataFrame(gdf_sel_RGIId_list)
        c = salida + 'lista_rgi.csv'
        lista.to_csv(c, index=False)
        
        # Extract geodetic MB for this cluster
        gmb_maipo = gmb.loc[gmb['period'] == '2000-01-01_2020-01-01']
        gmb_maipo['dmdtda_mm'] = gmb_maipo['dmdtda'] * 1000
        gmb_maipo['err_dmdtda_mm'] = gmb_maipo['err_dmdtda'] * 1000
        gmb_maipo['rgiid2'] = gmb_maipo.index 
        gmb_maipo = gmb_maipo[gmb_maipo['rgiid2'].isin(ID_rgi_id)]
        gmb_maipo['dmdtda_mm_pon'] = gmb_maipo.dmdtda_mm * ((gmb_maipo.area/1000000) / (gmb_maipo.area.sum()/1000000))
        gmb_maipo['err_dmdtda_mm_pon'] = gmb_maipo.err_dmdtda_mm * ((gmb_maipo.area/1000000) / (gmb_maipo.area.sum()/1000000))
        
        gmb_value = gmb_maipo.dmdtda_mm_pon.sum()
        gmb_error = gmb_maipo.err_dmdtda_mm_pon.sum()
        
        # Calculate area-weighted SMB
        mb_sim = mb_per_glacier_id.drop(mb_per_glacier_id.columns[20], axis=1)
        mb_sim = pd.DataFrame(mb_sim.mean(axis=1))
        mb_sim.rename(columns={mb_sim.columns[0]: 'mb_sim'}, inplace=True)
        mb_sim['rgiid'] = mb_per_glacier_id['rgi_id']
        mb_sim['area_sim'] = areas
        mb_sim['mb_mm_pon'] = mb_sim.mb_sim * ((mb_sim.area_sim) / (mb_sim.area_sim.sum()))
        
        smb_value = mb_sim.mb_mm_pon.sum()
        
        # Calculate area statistics
        rgi_area_s = (round(rgi_area, 3), 'area_rgi')
        rgi_oggm_s = (round(((ID_area.area.sum())/1000000), 3), 'area_oggm')
        porcentaje_s = (round(((rgi_oggm_s[0]/rgi_area_s[0])*100), 3), 'por_area_oggm')
        n_g_rgi = (len(gdf_sel), 'n_g_rgi')
        n_g_oggm = (max_n, 'n_g_oggm')
        
        # Compile comparison
        comp_gmb_smb = []
        comp_gmb_smb.append((gmb_value, "GMB"))
        comp_gmb_smb.append((gmb_error, "GMB_error"))
        comp_gmb_smb.append((smb_value, "SMB"))
        comp_gmb_smb.append(rgi_area_s)
        comp_gmb_smb.append(rgi_oggm_s)
        comp_gmb_smb.append(porcentaje_s)
        comp_gmb_smb.append(n_g_rgi)
        comp_gmb_smb.append(n_g_oggm)
        
        comp_gmb_smb = pd.DataFrame(comp_gmb_smb)
        c = salida + 'comparacion_gmb_smb_' + zona + '_.csv'
        comp_gmb_smb.to_csv(c, index=False)
        print(f"✓ Saved: comparacion_gmb_smb_{zona}_.csv")
        
        ###########################################################################
        # Create validation plot
        ###########################################################################
        
        print("Creating validation plot...")
        
        a_gmb = np.array([(float(gmb_value))/1000]*22)
        a_error = np.array(([(float(gmb_error))/1000]*22))
        
        rgi_area_plot = round(rgi_area, 1)
        oggm_area = round(((ID_area.area.sum())/1000000), 1)
        porcetaje = round(((oggm_area/rgi_area_plot)*100), 1)
        mean_gmb = str(round(float(gmb_value), 1))
        mean_smb = str(round(float(smb_value), 1))
        oggm_area = str(oggm_area)
        porcetaje = str(porcetaje)
        
        from pylab import figure, text
        plt.rcParams["figure.figsize"] = (7, 4)
        name = 'Annual_mb_' + zona + '_2000-2021.png'
        pathname = salida + name
        
        f = figure()
        ax = f.add_subplot(111)
        plt.plot(mb_mean.year, mb_mean.mb/1000, color="blue", label="OGGM MB")
        plt.plot(years, ([(float(gmb_value))/1000]*22), color="black", label="GMB")
        plt.fill_between(years, a_gmb-a_error, a_gmb+a_error, alpha=0.3, color='black', label="GMB error")
        plt.legend(loc="lower left")
        plt.xlabel('Time [yr]', fontsize=15)
        plt.ylabel("smb [m w.e./yr]", color="black", fontsize=15)
        plt.yticks(fontsize=15) 
        plt.xticks(fontsize=15)
        plt.xticks(np.arange(2000, 2022, 5))
        plt.title(zona, fontsize=20)
        plt.tight_layout()
        
        text(0.7, 0.92, 'A = ' + oggm_area + ' ' + "km\u00b2", ha='left', va='center', transform=ax.transAxes, fontsize=13)
        text(0.7, 0.84, 'A sim = ' + porcetaje + '%', ha='left', va='center', transform=ax.transAxes, fontsize=13)
        text(0.7, 0.76, 'GMB = ' + mean_gmb, ha='left', va='center', transform=ax.transAxes, fontsize=13)
        text(0.7, 0.68, 'SMB = ' + mean_smb, ha='left', va='center', transform=ax.transAxes, fontsize=13)
        
        plt.savefig(pathname, format='png', dpi=300)
        plt.close()
        print(f"✓ Saved: {name}")
        
        ###########################################################################
        # Extract climate variables
        ###########################################################################
        
        print("Extracting climate variables...")
        
        lista_temp = pd.DataFrame()
        lista_prcp = pd.DataFrame()
        lista_ele = pd.DataFrame()
     
        itera = np.arange(0, max_n).tolist()
    
        for i in itera:
            clima = gdirs[i].get_filepath('climate_historical')
            ds = xr.open_dataset(clima)
            prcp_x = pd.DataFrame(ds.prcp)
            temp_x = pd.DataFrame(ds.temp)
            
            id_rgi = gdirs[i].rgi_id
            ele_x = {id_rgi: [ds.ref_hgt]}
            ele_x = pd.DataFrame(ele_x)
            
            lista_prcp = pd.concat([lista_prcp, prcp_x], axis=1) 
            lista_temp = pd.concat([lista_temp, temp_x], axis=1) 
            lista_ele = pd.concat([lista_ele, ele_x], axis=1) 
        
        ct = salida + 'lista_temp.csv'
        cp = salida + 'lista_prec.csv'
        ce = salida + 'lista_ele.csv'
        
        lista_temp.to_csv(ct, index=False)       
        lista_prcp.to_csv(cp, index=False)
        lista_ele.to_csv(ce, index=False)
        print(f"✓ Saved: lista_temp.csv, lista_prec.csv, lista_ele.csv")
        
        print(f"\n✓ Completed validation for cluster {zona}\n")
    
    print("\n" + "="*60)
    print("ALL CLUSTERS VALIDATED SUCCESSFULLY!")
    print("="*60)