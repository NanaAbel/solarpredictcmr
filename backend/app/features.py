"""
Model II feature engineering.

Transforms raw weather + datetime into the 21 features expected by XGBoost.
Mirrors the logic in feature_model_II.ipynb.
"""

import math
from datetime import datetime

import numpy as np
import pandas as pd


def _season_flags(month: int, city: str) -> tuple[int, int]:
    """Return (season_dry, season_rainy) based on Cameroon climate patterns."""
    city_key = city.lower()
    if city_key == "douala":
        # Coastal: dry season Dec–Feb
        is_dry = month in (12, 1, 2)
    elif city_key == "maroua":
        # Far North: rainy season Jun–Sep
        is_dry = month not in (6, 7, 8, 9)
    else:
        is_dry = False
    return int(is_dry), int(not is_dry)


def build_model_ii_row(
    dt: datetime,
    t2m: float,
    rh2m: float,
    ws10m: float,
    prectotcorr: float,
    city: str,
) -> dict:
    """
    Build a single row of Model II features from weather and timestamp.

    Weather inputs (from Open-Meteo): T2M, RH2M, WS10M, PRECTOTCORR
    Derived automatically: cyclic time, season, rain/wind transforms
    """
    hour = dt.hour
    month = dt.month
    day_of_year = int(dt.timetuple().tm_yday)
    season_dry, season_rainy = _season_flags(month, city)

    return {
        # Calendar features
        "YEAR": dt.year,
        "MO": month,
        "DY": dt.day,
        "HR": hour,
        # Weather features from Open-Meteo
        "T2M": float(t2m),
        "RH2M": float(rh2m),
        "PRECTOTCORR": float(prectotcorr),
        "WS10M": float(ws10m),
        # Cyclic time encodings (daily + yearly patterns)
        "hour_sin": math.sin(2 * math.pi * hour / 24),
        "hour_cos": math.cos(2 * math.pi * hour / 24),
        "month_sin": math.sin(2 * math.pi * month / 12),
        "month_cos": math.cos(2 * math.pi * month / 12),
        "day_sin": math.sin(2 * math.pi * day_of_year / 365),
        "day_cos": math.cos(2 * math.pi * day_of_year / 365),
        "day_of_year": day_of_year,
        # Binary / transformed features
        "is_daytime": int(6 <= hour <= 18),
        "is_rainy": int(prectotcorr > 0),
        "rain_log1p": float(np.log1p(prectotcorr)),
        "ws10m_log1p": float(np.log1p(ws10m)),
        "season_dry": season_dry,
        "season_rainy": season_rainy,
    }


def build_feature_dataframe(rows: list[dict], feature_names: list[str]) -> pd.DataFrame:
    """Convert a list of feature dicts into a DataFrame with correct column order."""
    return pd.DataFrame(rows)[feature_names]
