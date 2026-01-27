# OGGM Multi-Dataset Climate Comparison Study - ReadMe

## Study Goals
1. **Compare historical climate datasets**: CR2MET, ERA5, and CRU (2000-2019)
2. **Assess climate forcing uncertainty**: Quantify how climate input choice affects glacier mass balance
3. **Validate against observations**: Compare simulated vs geodetic mass balance (Hugonnet et al., 2021)

---

## Datasets Used

| Dataset | Type | Resolution | Period |
|---------|------|-----------|--------|
| **CR2MET** | Regional downscaled | 2.5 km | 1960-2021 |
| **ERA5** | Global reanalysis | ~25 km | 1940-present |
| **CRU** | Station-based observations | ~50 km | 1901-present |

**Why these three datasets?**
- **CR2MET**: Regional, high-resolution Chilean climate product optimized for the Andes
- **ERA5**: Global reanalysis providing consistent worldwide coverage
- **CRU**: Independent station-based observations for validation

All three datasets cover the 2000-2019 simulation period and provide monthly temperature and precipitation data.

---

## File Locations

### Input Files
```
/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/
├── CR2met_t2m_hgt_2022_1960_dic_2021_2.5.nc  # CR2MET temperature + elevation
├── CR2met_pr_2022_1960_dic_2021_2.5.nc       # CR2MET precipitation
├── RGI_BNA_Clusters.csv                       # Glacier inventory with clusters
├── LR_Pf.csv                                  # Temperature lapse rate & precip factors per cluster
└── gmb_df_RGI60-all_pergla_worldwide_2000_2019_Hugonnet_h14_corr.hdf  # Geodetic observations
```

### Scripts
```
/Users/milliespencer/OGGM_CR2_Chile/
├── 01_Andes_2000_2019_CR2_2023.py      # Main simulation script (CR2MET)
├── 01_Andes_2000_2019_ERA5_2023.py     # Main simulation script (ERA5)
├── 01_Andes_2000_2019_CRU_2023.py      # Main simulation script (CRU)
├── 02_Andes_2000_2019_CR2_figura_2023.py  # Validation script
├── cr2met_25.py                         # Helper module (don't run directly)
└── Processing_clima_dem__cr2met_2.5_1960.R  # CR2Met data reprocessing 
```

### Outputs
```
/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/
├── CR2MET/DA1/
│   ├── run_output_2000_2019_hydro_TC_DA1.nc       # Compiled results
│   ├── RGI_DA1/b_080/L3/summary/                  # Summary statistics
│   ├── Annual_mb_DA1_2000-2021.png                # Validation plot
│   ├── comparacion_gmb_smb_DA1_.csv               # GMB vs SMB comparison
│   └── per_glacier/RGI60-*/                       # Per-glacier diagnostics
│
├── ERA5/DA1/
│   ├── run_output_2000_2019_hydro_ERA5_DA1.nc
│   └── [same structure as CR2MET]
│
└── CRU/DA1/
    ├── run_output_2000_2019_hydro_CRU_DA1.nc
    └── [same structure as CR2MET]
```

---

## Script Descriptions

### Main Simulation Scripts (01_*.py)

Each script runs the complete OGGM workflow for one climate dataset:

**Script 01_Andes_2000_2019_CR2_2023.py** (CR2MET)
```python
# Key sections:
1. Initialize OGGM with regional parameters (LR, Pf from LR_Pf.csv)
2. Load glacier directories from RGI Level 2 prepro
3. Process CR2MET climate data (custom module)
4. Calibrate mass balance using geodetic observations
5. Run ice thickness inversion
6. Initialize present-time glacier geometry
7. Run dynamic simulations 1999-2020 with monthly hydrology
8. Compile outputs to NetCDF
```

**Scripts 01_*_ERA5/CRU_2023.py** (ERA5/CRU)
- Identical workflow to CR2MET version
- Only differences: climate data source and output paths

**Runtime**: ~1.5 hours per cluster (422 glaciers) with multiprocessing OFF

---

### Validation Script (02_*.py)

**Script 02_Andes_2000_2019_CR2_figura_2023.py**

Compares OGGM simulated mass balance (SMB) vs geodetic observations (GMB):

```python
# Workflow:
1. Load compiled simulation output (.nc file)
2. Extract annual mass balance for each glacier
3. Load geodetic observations from Hugonnet et al. (2021)
4. Calculate area-weighted regional averages
5. Create validation plot (SMB vs GMB timeseries)
6. Save comparison statistics to CSV
7. Extract climate timeseries (temp, precip, elevation)
```

**Outputs**:
- `Annual_mb_[CLUSTER]_2000-2021.png` - Validation plot
- `comparacion_gmb_smb_[CLUSTER]_.csv` - Statistics
- `mb.csv` - Per-glacier annual mass balance
- `lista_temp.csv`, `lista_prec.csv`, `lista_ele.csv` - Climate extractions

**To run on other datasets**: Update input/output paths to point to ERA5 or CRU directories

---

### Helper Modules (Don't Run Directly)

**cr2met_25.py**
- Teaches OGGM how to read CR2MET NetCDF files
- Extracts temperature, precipitation, and elevation at glacier locations
- Automatically imported by Script 01 when using CR2MET

**Processing_clima_dem__cr2met_2.5_1960.R** (Already executed)
- R script that preprocessed original CR2MET files
- Resampled DEM to match climate grid (0.05°)
- Combined temperature + elevation into single NetCDF
- **You don't need to run this** - outputs already exist
- Future researchers can modify this to update to newer CR2MET versions

---

## Example Results (DA1 Cluster)

### Mass Balance Comparison
The validation workflow compares OGGM simulated mass balance (SMB) against geodetic observations (GMB) from Hugonnet et al. (2021):

**Example for CR2MET:**
- **Glaciers processed**: 422/422 (100%)
- **Area coverage**: 152.1 km² (102.7% of RGI area)
- **Geodetic MB (GMB)**: -98.7 ± 152.6 mm w.e./yr
- **Simulated MB (SMB)**: -118.4 mm w.e./yr
- **Difference**: -19.7 mm w.e./yr (20% overestimation)
- **Assessment**: Within observational uncertainty ✅

### Multi-Dataset Comparison
Once all three datasets are processed, the comparison quantifies climate forcing uncertainty:

```python
# Example multi-dataset results:
CR2MET:  -118.4 mm/yr
ERA5:    -XXX mm/yr
CRU:     -XXX mm/yr
---
Mean:    -YYY mm/yr
Std Dev: ±ZZZ mm/yr  ← Climate forcing uncertainty!
```

The standard deviation across datasets represents the uncertainty in mass balance estimates attributable to climate forcing choice alone.

---

## Workflow Summary

### Phase 1: Single Cluster Test
The workflow is designed to test on a single cluster (e.g., DA1) before expanding to all clusters:

```
1. Run Script 01 with CR2MET → Generate outputs for test cluster
2. Run Script 02 on CR2MET outputs → Validate against geodetic observations
3. Run Script 01 with ERA5 → Generate outputs for test cluster
4. Run Script 01 with CRU → Generate outputs for test cluster
5. Run Script 02 on ERA5 outputs → Validate against geodetic observations
6. Run Script 02 on CRU outputs → Validate against geodetic observations
7. Compare all three datasets → Estimate climate forcing uncertainty
```

### Phase 2: All Clusters
Once the workflow is validated on one cluster, expand to all 10:

```
8. Update list_region in Script 01 to include all 10 clusters
9. Run Scripts 01+02 for each cluster × 3 datasets
10. Create regional comparison plots
11. Analyze latitudinal patterns in climate uncertainty
```

### Phase 3: Multi-Dataset Analysis
Final synthesis across all clusters and datasets:

```
12. Create Script 03 for cross-dataset comparison
13. Quantify uncertainty from climate forcing by region
14. Identify glaciers most sensitive to climate choice
15. Write up results for publication
```

---

## Key Configuration Parameters

### Common to All Datasets
```python
cfg.PARAMS['use_multiprocessing'] = False  # True speeds up 4-8x on 8-core Mac
cfg.PARAMS['border'] = 80                   # Map border for calculations
cfg.PARAMS['hydro_month_sh'] = 1            # Southern Hemisphere hydro year start
cfg.PARAMS['max_mu_star'] = 600             # Mass balance calibration limit
cfg.PARAMS['temp_melt'] = 0                 # Melt temperature threshold
cfg.PARAMS['temp_default_gradient'] = -0.008  # From LR_Pf.csv per cluster
cfg.PARAMS['prcp_scaling_factor'] = 2.0     # From LR_Pf.csv per cluster
```

### Dataset-Specific
```python
# CR2MET
cfg.PARAMS['baseline_climate'] = 'CR2MET25'
from oggm.shop import cr2met_25
workflow.execute_entity_task(cr2met_25.process_cr2met_25_data, gdirs)

# ERA5 (built-in, auto-downloads)
cfg.PARAMS['baseline_climate'] = 'ERA5'
from oggm.shop import ecmwf
workflow.execute_entity_task(ecmwf.process_ecmwf_data, gdirs, dataset='ERA5')

# CRU (built-in, auto-downloads)
cfg.PARAMS['baseline_climate'] = 'CRU'
from oggm.shop import cru
workflow.execute_entity_task(cru.process_cru_data, gdirs)
```

---

## Chilean Glacier Clusters

| Cluster | Region | # Glaciers | Area (km²) | Latitude |
|---------|--------|-----------|-----------|----------|
| OT3 | Norte Grande | ~50 | ~15 | 18-27°S |
| DA1 | Maipo | 422 | 148 | 33-34°S |
| DA2 | Aconcagua | ~300 | ~100 | 32-33°S |
| DA3 | Central | ~800 | ~200 | 34-35°S |
| WA1 | Sur Norte | ~2000 | ~300 | 36-38°S |
| WA2 | Sur Central | ~3000 | ~500 | 38-41°S |
| WA3 | Patagonia Norte | ~4000 | ~1000 | 41-46°S |
| WA4 | Campos de Hielo Norte | ~200 | ~4000 | 46-47°S |
| WA5 | Campos de Hielo Sur | ~100 | ~13000 | 48-51°S |
| WA6 | Patagonia Sur | ~100 | ~800 | 51-56°S |

**Test mode**: `list_region = ['DA1']` (current)
**Full run**: `list_region = ['OT3','DA1','DA2','DA3','WA1','WA2','WA3','WA4','WA5','WA6']`

---

## Common Issues & Solutions

### Issue: NumPy compatibility error
```python
# Add this at top of script after imports:
import warnings
if not hasattr(np, 'warnings'):
    np.warnings = warnings
```

### Issue: Indentation errors in script
```python
# Check lines 112-113 and 120 in Script 01
# Should be aligned with if statement, not over-indented
```

### Issue: Missing ye parameter
```python
# Script 01, line 120 needs:
workflow.execute_entity_task(tasks.run_with_hydro, gdirs,
                     ys=1999,
                     ye=2020,  # Must include end year!
                     ...)
```

### Issue: Column indexing in Script 02
```python
# Line 198 should use column name, not position:
mb_sim = mb_per_glacier_id.drop('rgi_id', axis=1)  # Not: .columns[20]
```

---

## Tips for Efficient Running

### Speed Up Simulations
Turn on multiprocessing (after testing):
```python
cfg.PARAMS['use_multiprocessing'] = True  # Use all 8 cores
# Runtime: ~1.5 hrs → ~20-30 min for DA1
```

### Test Before Full Run
Always test with one cluster before running all 10:
```python
list_region = ['DA1']  # Test mode
# list_region = ['OT3','DA1',...,'WA6']  # Full run (comment out for testing)
```

### Monitor Progress
Use `tee` to save logs:
```bash
python 01_Andes_2000_2019_ERA5_2023.py 2>&1 | tee era5_log.txt
```

---

## Scientific Context

### Research Question
How does the choice of climate forcing dataset affect glacier mass balance simulations in the Chilean Andes?

### Hypothesis
Different climate datasets will produce varying estimates of glacier mass loss due to differences in:
1. Spatial resolution (2.5 km vs 25 km vs 50 km)
2. Data sources (regional model vs reanalysis vs stations)
3. Temperature and precipitation biases

### Expected Outcome
The standard deviation across the three datasets quantifies the **uncertainty due to climate forcing choice**, independent of model structure or calibration methodology.

---

## Citation Information

### Datasets
- **CR2MET**: Boisier et al. (2018), Center for Climate and Resilience Research
- **ERA5**: Hersbach et al. (2020), ECMWF
- **CRU**: Harris et al. (2020), University of East Anglia

### Model
- **OGGM**: Maussion et al. (2019), Open Global Glacier Model v1.5.3

### Validation
- **Geodetic MB**: Hugonnet et al. (2021), Global glacier mass changes 2000-2019

---

## Recommended Workflow

### For Testing
1. **Start with one cluster** (e.g., DA1 with ~400 glaciers)
2. **Run all three climate datasets** on that cluster
3. **Validate results** against geodetic observations
4. **Compare datasets** to verify workflow before scaling up

### For Full Analysis
1. **Expand to all clusters** after validating workflow
2. **Enable multiprocessing** for faster computation (`cfg.PARAMS['use_multiprocessing'] = True`)
3. **Monitor outputs** using log files (`2>&1 | tee logfile.txt`)
4. **Create comparison scripts** to synthesize results across all datasets and clusters