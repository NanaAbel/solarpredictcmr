"""
Open-Meteo weather API client.

Fetches hourly forecast data and builds Model II feature rows for each timestamp.
"""

from datetime import datetime

import httpx

from .config import CITIES
from .features import build_model_ii_row

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_hourly_weather(city: str, forecast_hours: int = 48) -> list[dict]:
    """
    Fetch hourly weather from Open-Meteo for a city.

    Returns a list of dicts, each containing:
      - datetime: ISO timestamp
      - weather: {T2M, RH2M, WS10M, PRECTOTCORR, MO, DY, HR}
      - features: full Model II feature dict for XGBoost
    """
    # Normalize user input so "Douala", "DOUALA", and "douala" behave alike.
    city_key = city.lower()
    if city_key not in CITIES:
        raise ValueError(f"Unknown city: {city}")

    # Pull coordinates/timezone from one central config dictionary.
    city_cfg = CITIES[city_key]

    # Open-Meteo request parameters.
    # forecast_days must be whole days, so requested hours are rounded up.
    params = {
        "latitude": city_cfg["latitude"],
        "longitude": city_cfg["longitude"],
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
        "wind_speed_unit": "ms",  # Match NASA POWER WS10M units (m/s)
        "timezone": city_cfg["timezone"],
        "forecast_days": min(7, max(1, (forecast_hours + 23) // 24)),
    }

    # Async HTTP keeps FastAPI responsive while waiting for the weather service.
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        # Convert failed HTTP responses into exceptions handled by main.py.
        response.raise_for_status()
        payload = response.json()

    # Parse hourly arrays from the API response.
    # Open-Meteo returns one list per variable, aligned by index.
    hourly = payload["hourly"]
    timestamps = hourly["time"][:forecast_hours]
    temperatures = hourly["temperature_2m"][:forecast_hours]
    humidities = hourly["relative_humidity_2m"][:forecast_hours]
    wind_speeds = hourly["wind_speed_10m"][:forecast_hours]
    precipitations = hourly["precipitation"][:forecast_hours]

    # Each record carries display weather plus model-ready features.
    records = []
    for idx, ts in enumerate(timestamps):
        dt = datetime.fromisoformat(ts)

        # Engineer Model II features from weather + datetime.
        # Missing numeric values are treated as 0.0 for rain/wind safety.
        features = build_model_ii_row(
            dt=dt,
            t2m=temperatures[idx],
            rh2m=humidities[idx],
            ws10m=wind_speeds[idx] or 0.0,
            prectotcorr=precipitations[idx] or 0.0,
            city=city_key,
        )

        # Keep the frontend response readable while preserving all model inputs.
        records.append(
            {
                "datetime": dt.isoformat(),
                "weather": {
                    "temperature": features["T2M"],
                    "humidity": features["RH2M"],
                    "wind_speed": features["WS10M"],
                    "precipitation": features["PRECTOTCORR"],
                    "MO": features["MO"],
                    "DY": features["DY"],
                    "HR": features["HR"],
                },
                "features": features,
            }
        )

    return records
