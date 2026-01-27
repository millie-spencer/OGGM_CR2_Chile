"""
OGGM Integration with CR2MET Climate Data for Chilean Andes Glaciers
This script processes all glaciers in Chile using CR2MET climate data instead of ERA5.
"""

import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
from oggm import cfg, utils, workflow, tasks
from oggm.shop import rgitopo
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

# File paths
PRECIP_FILE = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/CR2MET_pr_v2.5_month_1960_2021_005deg.nc'
TEMP_FILE = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/CR2MET_tmean_v2.5_mon_1960_2021_005deg.nc'

# Working directory for OGGM output
WORKING_DIR = '/Users/milliespencer/Desktop/CR2_OGGM_Paper/experimenting_output'

# RGI Region for Chile (South America)
RGI_REGION = '17'  # South America (Andes)

# =============================================================================
# STEP 1: LOAD AND PREPARE CR2MET DATA
# =============================================================================

def load_cr2met_data():
    """Load CR2MET precipitation and temperature data with proper time decoding."""
    
    print("Loading CR2MET data...")
    
    # Load datasets without automatic time decoding
    prcp = xr.open_dataset(PRECIP_FILE, decode_times=False)
    temp = xr.open_dataset(TEMP_FILE, decode_times=False)
    
    # Fix time coordinate (months since 1960-01-01)
    start_date = pd.Timestamp('1960-01-01')
    n_months = len(prcp.time)
    dates = pd.date_range(start=start_date, periods=n_months, freq='MS')
    
    prcp['time'] = dates
    temp['time'] = dates
    
    # Rename variables to standard names if needed
    if 'pr_month' in prcp.data_vars:
        prcp = prcp.rename({'pr_month': 'prcp'})
    
    print(f"CR2MET data loaded: {dates[0]} to {dates[-1]}")
    print(f"Spatial extent: lat {prcp.lat.min().values:.2f} to {prcp.lat.max().values:.2f}")
    print(f"                lon {prcp.lon.min().values:.2f} to {prcp.lon.max().values:.2f}")
    
    return prcp, temp


# =============================================================================
# STEP 2: EXTRACT CLIMATE DATA FOR GLACIER LOCATIONS
# =============================================================================

def extract_climate_for_glacier(gdir, prcp_ds, temp_ds):
    """
    Extract CR2MET climate time series for a specific glacier location.
    
    Parameters:
    -----------
    gdir : oggm.GlacierDirectory
        Glacier directory object
    prcp_ds : xarray.Dataset
        Precipitation dataset
    temp_ds : xarray.Dataset
        Temperature dataset
    """
    
    # Get glacier centroid coordinates
    lon = gdir.cenlon
    lat = gdir.cenlat
    
    # Extract nearest grid point (you could also do bilinear interpolation)
    prcp_ts = prcp_ds.sel(lon=lon, lat=lat, method='nearest')['prcp']
    temp_ts = temp_ds.sel(lon=lon, lat=lat, method='nearest')['tmean']
    
    # Convert to pandas Series with proper time index
    prcp_series = prcp_ts.to_series()
    temp_series = temp_ts.to_series()
    
    # OGGM expects specific column names
    climate_df = pd.DataFrame({
        'temp': temp_series.values,
        'prcp': prcp_series.values
    }, index=temp_series.index)
    
    # Save to glacier directory
    climate_file = gdir.get_filepath('climate_historical')
    climate_df.to_csv(climate_file)
    
    return climate_df


# =============================================================================
# STEP 3: INITIALIZE OGGM AND GET CHILEAN GLACIERS
# =============================================================================

def initialize_oggm():
    """Initialize OGGM configuration."""
    
    cfg.initialize(logging_level='INFO')
    
    # Set working directory
    cfg.PATHS['working_dir'] = WORKING_DIR
    
    # Use COPDEM for topography (good global coverage)
    cfg.PARAMS['use_intersects'] = False
    cfg.PARAMS['continue_on_error'] = True
    
    # Regional parameters for Chilean Andes
    # These may need tuning based on your specific study
    cfg.PARAMS['prcp_fac'] = 2.5  # Precipitation correction factor
    cfg.PARAMS['temp_bias'] = 0.0  # Temperature bias correction
    
    print(f"OGGM initialized. Working directory: {WORKING_DIR}")


def get_chilean_glaciers(region='17'):
    """
    Get all glaciers in Chile from RGI.
    
    Parameters:
    -----------
    region : str
        RGI region number (17 = South America/Andes)
        
    Returns:
    --------
    rgi_df : GeoDataFrame
        Glacier inventory for Chile
    """
    
    print(f"Loading RGI glaciers for region {region}...")
    
    # Download RGI files if needed
    from oggm import utils
    rgi_path = utils.get_rgi_region_file(region, version='62')
    
    # Load RGI shapefile
    rgi_df = gpd.read_file(rgi_path)
    
    # Filter for Chile only (CenLon between ~-76 and -66, CenLat between -56 and -17)
    chile_glaciers = rgi_df[
        (rgi_df.CenLon >= -77) & 
        (rgi_df.CenLon <= -66) &
        (rgi_df.CenLat >= -56) &
        (rgi_df.CenLat <= -17)
    ]
    
    print(f"Found {len(chile_glaciers)} glaciers in Chile")
    
    return chile_glaciers


# =============================================================================
# STEP 4: BATCH PROCESS ALL GLACIERS
# =============================================================================

def process_glacier_with_cr2met(gdir, prcp_ds, temp_ds):
    """
    Process a single glacier with CR2MET climate data.
    
    Parameters:
    -----------
    gdir : oggm.GlacierDirectory
        Already initialized glacier directory
    prcp_ds : xarray.Dataset
        Precipitation dataset
    temp_ds : xarray.Dataset
        Temperature dataset
    """
    
    try:
        # Extract and process CR2MET climate data
        climate_df = extract_climate_for_glacier(gdir, prcp_ds, temp_ds)
        
        # Process climate data for mass balance
        tasks.apparent_mb_from_any_mb(gdir)
        
        print(f"✓ Processed {gdir.rgi_id}")
        return gdir
        
    except Exception as e:
        print(f"✗ Error processing {gdir.rgi_id}: {str(e)}")
        return None


def batch_process_all_glaciers():
    """Main function to batch process all Chilean glaciers with CR2MET."""
    
    # Initialize OGGM
    initialize_oggm()
    
    # Load CR2MET data
    prcp_ds, temp_ds = load_cr2met_data()
    
    # Get Chilean glaciers
    chile_glaciers = get_chilean_glaciers(RGI_REGION)
    
    # =============================================================================
    # TEST MODE: Uncomment the next line to test with just 10 glaciers
    # =============================================================================
    chile_glaciers = chile_glaciers.head(10)
    
    # =============================================================================
    # FULL RUN: Comment out the line above to process ALL glaciers
    # =============================================================================
    
    print(f"\nStep 1: Initializing {len(chile_glaciers)} glacier directories...")
    print("=" * 60)
    
    # Get list of RGI IDs
    rgi_ids = chile_glaciers.RGIId.tolist()
    
    # Initialize all glacier directories at once (downloads outlines, DEMs, etc.)
    print("Downloading glacier outlines and DEMs (this may take a while)...")
    gdirs = workflow.init_glacier_directories(rgi_ids, from_prepro_level=None, prepro_border=80)
    
    print(f"✓ Initialized {len(gdirs)} glacier directories")
    
    print(f"\nStep 2: Running preprocessing tasks...")
    print("=" * 60)
    
    # Run preprocessing tasks on all glaciers
    workflow.execute_entity_task(tasks.define_glacier_region, gdirs)
    workflow.execute_entity_task(tasks.glacier_masks, gdirs)
    workflow.execute_entity_task(tasks.compute_centerlines, gdirs)
    workflow.execute_entity_task(tasks.initialize_flowlines, gdirs)
    workflow.execute_entity_task(tasks.compute_downstream_line, gdirs)
    workflow.execute_entity_task(tasks.compute_downstream_bedshape, gdirs)
    workflow.execute_entity_task(tasks.catchment_area, gdirs)
    workflow.execute_entity_task(tasks.catchment_intersections, gdirs)
    workflow.execute_entity_task(tasks.catchment_width_geom, gdirs)
    workflow.execute_entity_task(tasks.catchment_width_correction, gdirs)
    
    print(f"\nStep 3: Processing CR2MET climate data for each glacier...")
    print("=" * 60)
    
    # Process climate data for each glacier
    successful_gdirs = []
    for idx, gdir in enumerate(gdirs):
        result = process_glacier_with_cr2met(gdir, prcp_ds, temp_ds)
        if result is not None:
            successful_gdirs.append(result)
        
        # Progress update every 100 glaciers
        if (idx + 1) % 100 == 0:
            print(f"Progress: {idx + 1}/{len(gdirs)} glaciers")
    
    print("=" * 60)
    print(f"Successfully processed {len(successful_gdirs)}/{len(gdirs)} glaciers")
    
    return successful_gdirs


# =============================================================================
# STEP 5: RUN PROJECTIONS (OPTIONAL)
# =============================================================================

def run_projections(gdirs, years=100):
    """
    Run glacier projections using the historical climate.
    
    Parameters:
    -----------
    gdirs : list
        List of glacier directories
    years : int
        Number of years to project forward
    """
    
    print(f"\nRunning {years}-year projections...")
    
    for gdir in gdirs:
        try:
            # Run random climate with temperature bias
            tasks.run_random_climate(gdir, nyears=years, temperature_bias=0)
            print(f"✓ Projection complete for {gdir.rgi_id}")
        except Exception as e:
            print(f"✗ Error in projection for {gdir.rgi_id}: {str(e)}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    
    # Create working directory if it doesn't exist
    os.makedirs(WORKING_DIR, exist_ok=True)
    
    # Run the batch processing
    gdirs = batch_process_all_glaciers()
    
    # Optional: Run projections
    # run_projections(gdirs, years=100)
    
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print(f"Results saved to: {WORKING_DIR}")
    print("=" * 60)