from fastapi import FastAPI, HTTPException
from fastapi import Query
from datetime import datetime
from typing import List
import pandas as pd
import numpy as np

## load model results
ALL_DATA = pd.read_parquet("ALL_DATA.parquet")

description = f"""
### Expected inputs
Date format in ISO 8601, lat/long in 5 deg increments, altitude in 50km increments.

### Current date range
{ALL_DATA.columns.min()} to {ALL_DATA.columns.max()}

### Links
"""

app = FastAPI(
    title="Karman Backend Model Runs API",
    description=description,
    summary="Data Driven Thermospheric Density Modeling",
    version="0.0.1",
    # terms_of_service="https://trillium.tech",
    contact={
        "name": "Trillium Tech",
        "url": "https://trillium.tech",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


# prep
## build grid
n_grid = 72
n_samples = n_grid ** 2
u, v = np.linspace(0, 1, n_grid), np.linspace(0, 1, n_grid)
longitude, latitude = np.sort(2 * np.pi * u), np.sort(np.arccos(2 * v - 1) - np.pi / 2)
lonlat_grid = np.stack(
    [*np.meshgrid(longitude, latitude, indexing="ij")], axis=2
).reshape(-1, 2)
lonlat_grid[:, 0] -= np.pi
longitudes = list(np.rad2deg(lonlat_grid[:, 0], dtype=np.float32))
latitudes = list(np.rad2deg(lonlat_grid[:, 1], dtype=np.float32))
LONGITUDES = (np.round(np.array(longitudes) / 2.5) * 2.5).tolist()
LATITUDES = (np.round(np.array(latitudes) / 2.5) * 2.5).tolist()
LON_LAT_DF = pd.DataFrame({'Longitude': LONGITUDES, 'Latitude': LATITUDES})

# ## load model results
# ALL_DATA = pd.read_parquet("ALL_DATA.parquet")

@app.get("/surface")
async def get_surface(altitude: float, date: datetime):
    # determine index
    alt_index = int((altitude - 200) / 50)
    n_samples = n_grid ** 2

    # validation
    if alt_index >= 11 or alt_index < 0:
        raise HTTPException(status_code=404, detail="Altitude not found")

    date_str = date.strftime("%Y-%m-%d %H:%M:%S")

    if date_str not in ALL_DATA.columns:
        raise HTTPException(status_code=404, detail="Date not found")

    # retrieval 
    density = ALL_DATA[date_str][alt_index*n_samples:(alt_index+1)*n_samples]

    return {
        "density": density.values.tolist(),
        "latitudes": LATITUDES,
        "longitudes": LONGITUDES
    }

# Return altitude 
@app.get("/altitude")
async def get_altitude(latitude: float, longitude: float, date: datetime):
    # validation    
    if latitude not in LATITUDES:
        raise HTTPException(status_code=404, detail="Latitude not found")
    
    if longitude not in LONGITUDES:
        raise HTTPException(status_code=404, detail="Longitude not found")

    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    if date_str not in ALL_DATA.columns:
        raise HTTPException(status_code=404, detail="Date not found")
    
    # determine index
    all_altitudes = [200 + i*50 for i in range(11)]
    target_lonlat_idx = int(LON_LAT_DF.query(f"Longitude == {longitude} & Latitude == {latitude}").index[0]-1)

    # retrieval
    density = [ALL_DATA[date_str][target_lonlat_idx + (i * n_samples)] for i in range(11)]

    return {
        "density": density,
        "altitude": all_altitudes
    }

# Return currently selected model info
@app.get("/about")
async def get_about(model_name: str = "default"):

    if model_name:
        # search for model info
        pass

    model_name = "ts_karman_model_tft_run_gpu_tft_w_omni_and_soho_wo_indices_and_proxies_w_10000_lag_100_resolution_valid_mape_14.936_params_1074865"
    model_train_date = pd.Timestamp('2023-09-30')
    model_version = "v0.1"
    model_availability = 3
    forecast_minutes = 100

    return {
        "model": {
            "name": model_name,
            "train_date": model_train_date,
            "version": model_version,
            "availability": model_availability,
            "forecast_minutes": forecast_minutes
        }
    }
