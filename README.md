# OGGM Chile Glacier Runoff Study

## Overview

This project simulates monthly glacier mass balance for all ~13,000 Chilean glaciers (2000–2019) using OGGM v1.6, forced with three climate datasets (CR2MET, ERA5, CRU), and estimates the relative contribution of glacier melt to streamflow across glacierized basins throughout Chile. Simulated mass balance is calibrated against geodetic observations from Hugonnet et al. (2021).

---

## Repository Structure

```
OGGM_CR2_Chile/
├── 01_Andes_2000_2019_CR2_2023.py       # OGGM simulation — CR2MET forcing
├── 01_Andes_2000_2019_ERA5_2023.py      # OGGM simulation — ERA5 forcing
├── 01_Andes_2000_2019_CRU_2023.py       # OGGM simulation — CRU forcing
├── 02_Andes_2000_2019_CR2_figura_2023.py # Validation: SMB vs Hugonnet GMB
├── cr2met_25.py                          # Helper: teaches OGGM to read CR2MET files
└── Processing_clima_dem__cr2met_2.5_1960.R  # (already run) CR2MET preprocessing
```

---

## 01_*.py — OGGM Simulations

Three scripts, one per climate dataset, sharing an identical workflow:

1. Load glacier directories for each regional cluster (OT3, DA1–DA3, WA1–WA6)
2. Process climate data (CR2MET via `cr2met_25.py`; ERA5 and CRU via built-in OGGM modules)
3. Calibrate mass balance parameters against Hugonnet et al. (2021) geodetic observations
4. Run ice thickness inversion and initialise present-day glacier geometry
5. Run dynamic simulation 1999–2020 with monthly hydrology output
6. Compile outputs to NetCDF per cluster

**Key outputs** (written to `/Users/milliespencer/Desktop/CR2_OGGM_Paper/Output/{DATASET}/{CLUSTER}/`):

| File | Contents |
|------|----------|
| `run_output_2000_2019_hydro_TC_{CLUSTER}.nc` | Monthly hydrology: melt, liquid precip, area, volume — all glaciers |
| `mb.csv` | Annual mass balance per glacier |
| `comparacion_gmb_smb_{CLUSTER}_.csv` | SMB vs GMB comparison statistics |

**NetCDF variable units**: `melt_on_glacier_monthly` and `liq_prcp_on_glacier_monthly` are stored in **kg** — divide by 1,000 to convert to m³.

**Clusters**: `['OT3','DA1','DA2','DA3','WA1','WA2','WA3','WA4','WA5','WA6']`

All three simulations are calibrated to the same Hugonnet geodetic mass balance, so the 20-year mean SMB is identical by construction across datasets. Differences in simulated melt volumes reflect differences in how each product partitions accumulation and ablation (see Paper 1).

---

## 02_*.py — Validation

Compares OGGM simulated mass balance (SMB) against Hugonnet geodetic mass balance (GMB):

1. Load compiled NetCDF output
2. Extract annual mass balance per glacier
3. Load Hugonnet et al. (2021) geodetic observations
4. Compute area-weighted regional averages
5. Generate validation plot and save comparison statistics

---

## cr2met_25.py — Helper Module

Teaches OGGM how to read CR2MET NetCDF files. Automatically imported by `01_*_CR2_2023.py`. 

---

## Streamflow Contribution Analysis (Notebooks)

The OGGM outputs above feed into a pair of Jupyter notebooks that estimate glacier melt contributions to streamflow across Chile, using CAMELS-CL discharge records as observational grounding.

### `allipen_test_glacier_melt_streamflow_routing.ipynb`
Single-basin validated case study for Río Allipen en Melipeuco (gauge 9402001, WA1). Established the core methods and validated against known results before scaling up.

### `all_chile_glacier_streamflow_v3.ipynb`
Full all-Chile analysis. 


**Key numbers:**
- 13,246 RGI glaciers simulated (100% of Chilean glacier area, 27,499 km²)
- 6,883 glaciers matched to a CAMELS gauge (26.7% of glacier area — rest drains to ungauged fjords/rivers)
- 137 gauges in final streamflow fraction analysis
- National melt totals (2000–2019 mean): CR2MET 53.9 km³/yr, ERA5 69.3 km³/yr, CRU 32.5 km³/yr

**Glacier runoff definition**: `melt_on_glacier_monthly` + `liq_prcp_on_glacier_monthly` (following Caro et al., 2024)
