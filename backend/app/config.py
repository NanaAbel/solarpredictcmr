"""Application configuration — paths, city metadata, and Model II feature list."""

from pathlib import Path

# Project root (SolarPredict/). pathlib keeps paths portable across machines.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Trained XGBoost model files live here. main.py preloads them at startup.
MODEL_DIR = BASE_DIR / "Model"

# SQLite database file path. database.py creates it automatically if missing.
DB_PATH = BASE_DIR / "backend" / "solar_predict.db"

# City definitions: coordinates for Open-Meteo and model file mapping.
# The dictionary key is the city id sent by the frontend.
CITIES = {
    "douala": {
        "name": "Douala",
        "latitude": 4.0511,
        "longitude": 9.7679,
        "timezone": "Africa/Douala",
        "model_file": "douala_xgb_model_ii.pkl",
    },
    "maroua": {
        "name": "Maroua",
        "latitude": 10.5956,
        "longitude": 14.3247,
        "timezone": "Africa/Douala",
        "model_file": "maroua_xgb_model_ii.pkl",
    },
}

# Full Model II feature list — must match training notebook order
# Full Model II feature list.
# IMPORTANT: this order must match the training notebooks and saved XGBoost model.
MODEL_II_FEATURES = [
    "YEAR",
    "MO",
    "DY",
    "HR",
    "T2M",
    "RH2M",
    "PRECTOTCORR",
    "WS10M",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
    "day_sin",
    "day_cos",
    "day_of_year",
    "is_daytime",
    "is_rainy",
    "rain_log1p",
    "ws10m_log1p",
    "season_dry",
    "season_rainy",
]

# Target variable predicted by the model (W/m²)
TARGET = "ALLSKY_SFC_SW_DWN"
