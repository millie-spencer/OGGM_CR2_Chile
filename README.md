# OGGM Climate Comparison Study - Quick Reference

## Study Goals
1. **Compare historical climate datasets**: ERA5, TerraClimate, CR2MET (1960-2021)
2. **Assess impact on glacier modeling**: How does climate input affect mass balance?
3. **Run future projections**: Use best-performing dataset for 21st century projections

---

## Files Overview

### Input Climate Files

| Dataset | Temperature File | Precipitation File | Notes |
|---------|-----------------|-------------------|-------|
| **ERA5** | Auto-downloaded | Auto-downloaded | No files needed |
| **TerraClimate** | `TC_tmean_hgt_2022.nc` | `TC_pr_2022.nc` | Manual download required |
| **CR2MET** | `CR2met_t2m_hgt_2022_1960_dic_2021_2.5.nc` | `CR2met_pr_2022_1960_dic_2021_2.5.nc` | Already preprocessed |

**All climate files location**: `/Users/milliespencer/Desktop/CR2_OGGM_Paper/files_chile_OGGM_climate_comparison/`

---

## Scripts Reference

### Helper Modules (Don't Run These)

**`terraclimate.py`**
- Module that teaches OGGM how to read TerraClimate files
- Imported automatically when processing TerraClimate

**`cr2met_25.py`**
- Module that teaches OGGM how to read CR2MET files
- Imported automatically when processing CR2MET

**`gcm_climate.py`**
- Module for processing future climate projections (CMIP5/CMIP6)
- Used in Step 2 after historical comparison is complete

---

### Preprocessing Script (Already Run)

**`Processing_clima_dem__cr2met_2.5_1960.R`**
- R script that converts original CR2MET files to OGGM format
- Creates the two `CR2met_*.nc` files above
- You have the outputs already - no need to run this

---

### Main Processing Script (What You Run)

**Your main script** (to be created/modified)
- Processes all Chilean glaciers with chosen climate dataset
- Run 3 times (once per dataset)
- Outputs climate summaries and glacier data

---

## Workflow

### Phase 1: Historical Climate Comparison

```
Step 1: Process with ERA5
├── Set: cfg.PARAMS['baseline_climate'] = 'ERA5'
├── Use: Built-in OGGM functions
└── Output: ./output/ERA5/

Step 2: Process with TerraClimate
├── Set: cfg.PARAMS['baseline_climate'] = 'terraclimate'
├── Import: terraclimate.py
└── Output: ./output/TerraClimate/

Step 3: Process with CR2MET
├── Set: cfg.PARAMS['baseline_climate'] = 'CR2MET25'
├── Import: cr2met_25.py
└── Output: ./output/CR2MET/

Step 4: Compare Results
└── Analyze climate_summary.csv from each dataset
```

### Phase 2: Future Projections (After Phase 1)

```
Step 5: Choose best historical dataset
└── Based on comparison with observations/validation

Step 6: Process CMIP projections
├── Use: gcm_climate.py module
├── Input: GCM/CMIP model files (e.g., SSP scenarios)
└── Output: Future glacier evolution (2025-2100)
```

---

## Key Configuration Settings

**For each climate dataset, you must set:**

```python
# ERA5
cfg.PARAMS['baseline_climate'] = 'ERA5'
# No import needed - built into OGGM
# No file paths needed - auto-downloaded

# TerraClimate
cfg.PARAMS['baseline_climate'] = 'terraclimate'
import terraclimate
terraclimate.set_terraclimate_url('/path/to/files/')

# CR2MET
cfg.PARAMS['baseline_climate'] = 'CR2MET25'
import cr2met_25
cr2met_25.set_cr2met_url('/path/to/files/')
```

---

## Output Files

### Per Dataset Output Structure
```
output/
├── ERA5/
│   ├── per_glacier/
│   │   └── RGI60-17.XXXXX/
│   │       └── climate_historical.csv
│   └── climate_summary.csv
├── TerraClimate/
│   ├── per_glacier/
│   │   └── RGI60-17.XXXXX/
│   │       └── climate_historical.csv
│   └── climate_summary.csv
└── CR2MET/
    ├── per_glacier/
    │   └── RGI60-17.XXXXX/
    │       └── climate_historical.csv
    └── climate_summary.csv
```

### Key Output Files

**`climate_historical.csv`** (per glacier)
- Monthly temperature and precipitation time series
- One file per glacier per dataset

**`climate_summary.csv`** (per dataset)
- Summary statistics for all glaciers
- Mean temp, mean precip, totals
- Used for comparison across datasets

---

## Quick Start Guide

### 1. Test Run (10 glaciers, ~10 minutes each)
```python
# In your script, set:
chile_glaciers = chile_glaciers.head(10)

# Run once for each dataset
# Change cfg.PARAMS['baseline_climate'] each time
```

### 2. Full Run (~16,000 glaciers, hours per dataset)
```python
# Comment out the test line:
# chile_glaciers = chile_glaciers.head(10)

# Run three times with full dataset
```

### 3. Compare Results
```python
# Load all three climate_summary.csv files
# Compare temperature and precipitation values
# Assess which dataset best matches observations
```

### 4. Future Projections
```python
# After choosing best dataset, run projections:
# - Load CMIP/GCM future climate data
# - Use gcm_climate.py to process projections
# - Run glacier model to 2100
```

---

## Common Issues

**Problem**: Files not found
```python
# Solution: Update paths in modules
terraclimate.set_terraclimate_url('/correct/path/')
cr2met_25.set_cr2met_url('/correct/path/')
```

**Problem**: Wrong baseline climate error
```python
# Solution: Check that baseline matches your processing function
# ERA5 → 'ERA5'
# TerraClimate → 'terraclimate'  
# CR2MET → 'CR2MET25'
```

**Problem**: Time period mismatch
```python
# Solution: Use overlapping period for fair comparison
y0 = 1960  # All three datasets start here or later
y1 = 2021  # CR2MET ends here
```

---

## Dataset Comparison Table

| Feature | ERA5 | TerraClimate | CR2MET |
|---------|------|--------------|--------|
| **Resolution** | ~31 km | ~4 km | ~5 km |
| **Coverage** | Global | Global | Chile only |
| **Period** | 1940-present | 1958-present | 1960-2021 |
| **Data Type** | Reanalysis | Gridded obs + models | Stations + reanalysis |
| **Best For** | Global consistency | High-res global | Chilean accuracy |
| **Files Needed** | None | 2 files | 2 files |
| **Module** | Built-in | `terraclimate.py` | `cr2met_25.py` |

---

## Next Steps After Comparison

1. Validate against observations (if available)
2. Analyze spatial patterns of climate differences
3. Assess mass balance sensitivity to climate input
4. Choose best dataset for projections
5. Run 21st century projections with CMIP scenarios