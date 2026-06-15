"""
FastAPI application entry point.

Exposes REST APIs for:
  - Solar irradiance prediction (XGBoost Model II)
  - Prediction history (SQLite)
  - Dashboard live cards + microgrid recommendation
  - Microgrid optimization
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import CITIES, MODEL_II_FEATURES
from .database import (
    get_dashboard_stats,
    get_prediction_history,
    init_db,
    save_predictions,
)
from .features import build_feature_dataframe
from .microgrid import run_microgrid_optimization
from .model_loader import get_model, predict
from .schemas import (
    DashboardResponse,
    MicrogridAdvice,
    MicrogridRequest,
    MicrogridResponse,
    PredictionPoint,
    PredictionRequest,
    PredictionResponse,
    WeatherSnapshot,
)
from .services.microgrid_recommendation import get_microgrid_recommendation
from .weather import fetch_hourly_weather

app = FastAPI(
    title="Solar Energy Forecasting API",
    description="Solar irradiance prediction and microgrid optimization for Douala and Maroua",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize SQLite and preload XGBoost models into memory."""
    init_db()
    for city in CITIES:
        get_model(city)


@app.get("/api/health")
def health_check():
    """Check API status and list supported cities."""
    return {"status": "ok", "cities": list(CITIES.keys())}


@app.get("/api/cities")
def list_cities():
    """Return city names and coordinates."""
    return [
        {
            "id": city_id,
            "name": cfg["name"],
            "latitude": cfg["latitude"],
            "longitude": cfg["longitude"],
        }
        for city_id, cfg in CITIES.items()
    ]


@app.get("/api/dashboard", response_model=DashboardResponse)
async def dashboard(city: str = "douala"):
    """
    Dashboard cards: live weather, current prediction, and microgrid advice.

    Fetches Open-Meteo data, runs XGBoost for the current hour, and returns
    the six dashboard metrics plus aggregated history stats.
    """
    city_key = city.lower()
    if city_key not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {city}")

    try:
        weather_records = await fetch_hourly_weather(city_key, 1)
        feature_df = build_feature_dataframe(
            [record["features"] for record in weather_records],
            MODEL_II_FEATURES,
        )
        prediction_value = predict(city_key, feature_df)[0]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    record = weather_records[0]
    weather = record["weather"]
    advice = get_microgrid_recommendation(prediction_value)
    stats = get_dashboard_stats(city_key)

    # Persist current reading so dashboard refreshes build history
    save_predictions(
        city_key,
        [
            {
                "temperature": weather["temperature"],
                "humidity": weather["humidity"],
                "wind_speed": weather["wind_speed"],
                "precipitation": weather["precipitation"],
                "prediction": round(prediction_value, 2),
                "timestamp": record["datetime"],
            }
        ],
    )

    return DashboardResponse(
        city=city_key,
        temperature=weather["temperature"],
        humidity=weather["humidity"],
        wind_speed=weather["wind_speed"],
        precipitation=weather["precipitation"],
        prediction=round(prediction_value, 2),
        timestamp=record["datetime"],
        microgrid_status=advice.status,
        microgrid_recommendation=advice.recommendation,
        microgrid_level=advice.level,
        total_predictions=stats["total_predictions"],
        predictions_by_city=stats["predictions_by_city"],
        latest_predictions=stats["latest_predictions"],
        average_prediction_by_city=stats["average_prediction_by_city"],
    )


@app.post("/api/predict", response_model=PredictionResponse)
async def predict_solar(request: PredictionRequest):
    """Run hourly solar forecast, save to SQLite, attach microgrid advice."""
    city = request.city.lower()
    if city not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {request.city}")

    try:
        weather_records = await fetch_hourly_weather(city, request.hours)
        feature_df = build_feature_dataframe(
            [record["features"] for record in weather_records],
            MODEL_II_FEATURES,
        )
        prediction_values = predict(city, feature_df)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather or prediction failed: {exc}") from exc

    predictions: list[PredictionPoint] = []
    db_records = []

    for record, prediction_value in zip(weather_records, prediction_values):
        weather = WeatherSnapshot(**record["weather"])
        rounded = round(prediction_value, 2)
        advice = get_microgrid_recommendation(rounded)

        predictions.append(
            PredictionPoint(
                datetime=record["datetime"],
                prediction=rounded,
                weather=weather,
                microgrid=MicrogridAdvice(
                    status=advice.status,
                    recommendation=advice.recommendation,
                    level=advice.level,
                ),
            )
        )
        db_records.append(
            {
                "temperature": weather.temperature,
                "humidity": weather.humidity,
                "wind_speed": weather.wind_speed,
                "precipitation": weather.precipitation,
                "prediction": rounded,
                "timestamp": record["datetime"],
            }
        )

    save_predictions(city, db_records)

    return PredictionResponse(
        city=city,
        hours=request.hours,
        predictions=predictions,
    )


@app.get("/api/history")
def prediction_history(city: str | None = None, limit: int = 100):
    """Retrieve stored predictions, optionally filtered by city."""
    if city and city.lower() not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {city}")
    return get_prediction_history(city=city, limit=limit)


@app.get("/api/microgrid/recommendation")
def microgrid_recommendation(prediction: float):
    """Return rule-based microgrid status for a given irradiance value."""
    advice = get_microgrid_recommendation(prediction)
    return {
        "prediction": prediction,
        "status": advice.status,
        "recommendation": advice.recommendation,
        "level": advice.level,
    }


@app.post("/api/microgrid/optimize", response_model=MicrogridResponse)
async def optimize_microgrid(request: MicrogridRequest):
    """Run battery/grid optimization using predicted solar generation."""
    city = request.city.lower()
    if city not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {request.city}")

    try:
        return await run_microgrid_optimization(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
