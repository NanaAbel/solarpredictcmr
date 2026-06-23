"""
FastAPI application entry point.

Exposes REST APIs for:
  - Solar irradiance prediction (XGBoost Model II)
  - Prediction history (SQLite)
  - Dashboard live cards + microgrid recommendation
  - Microgrid optimization
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response

from .config import (
    CITIES,
    DEFAULT_BATTERY_CAPACITY_KWH,
    DEFAULT_DAILY_LOAD_KWH,
    DEFAULT_PANEL_AREA_M2,
    DEFAULT_PANEL_EFFICIENCY,
    MODEL_II_FEATURES,
)
from .database import (
    get_dashboard_stats,
    get_latest_prediction,
    get_prediction_history,
    init_db,
    save_predictions,
)
from .features import build_feature_dataframe
from .microgrid import run_microgrid_optimization
from .model_loader import get_model, predict
from .schemas import (
    AlertResponse,
    DashboardResponse,
    EnhancedDashboardResponse,
    ForecastPoint,
    MicrogridAdvice,
    MicrogridRequest,
    MicrogridResponse,
    ModelMetrics,
    PredictionPoint,
    PredictionRequest,
    PredictionResponse,
    SeasonalComparison,
    SeasonalReportResponse,
    SeasonBucket,
    WeatherSnapshot,
)
from .services.alert_service import evaluate_alert
from .services.analytics_service import get_dashboard_analytics
from .services.microgrid_recommendation import get_microgrid_recommendation
from .services.report_service import build_seasonal_report, build_seasonal_report_csv
from .services.weekly_report_service import build_weekly_report, build_weekly_report_pdf
from .weather import close_weather_client, fetch_hourly_weather

app = FastAPI(
    title="Solar Energy Forecasting API",
    description="Solar irradiance prediction and microgrid optimization for Douala and Maroua",
    version="1.0.0",
)

def _cors_origins() -> list[str]:
    """Local dev origins plus optional Vercel/production URLs from env."""
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    vercel_url = os.getenv("VERCEL_URL")
    if vercel_url:
        origins.append(f"https://{vercel_url}")
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url.rstrip("/"))
    return origins


# Allow local Vite dev and deployed Vercel frontend (when env vars are set).
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize SQLite and preload XGBoost models into memory."""
    # Create/migrate the SQLite database before any route tries to use it.
    init_db()
    # Preloading avoids a slow first prediction request for each city.
    for city in CITIES:
        get_model(city)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_weather_client()


@app.get("/")
def root():
    """Help users who open the backend URL directly in the browser."""
    return {
        "message": "SolarPredict API is running.",
        "frontend": "Open http://localhost:5173 in your browser for the dashboard UI.",
        "docs": "/docs",
        "health": "/api/health",
    }


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


@app.get("/api/dashboard", response_model=EnhancedDashboardResponse)
async def dashboard(
    city: str = "douala",
    battery_capacity_kwh: float = DEFAULT_BATTERY_CAPACITY_KWH,
    daily_load_kwh: float = DEFAULT_DAILY_LOAD_KWH,
    panel_area_m2: float = DEFAULT_PANEL_AREA_M2,
    panel_efficiency: float = DEFAULT_PANEL_EFFICIENCY,
):
    """
    FR-8 dashboard: live cards, 24 h GHI forecast, microgrid schedule,
    battery SoC, alert status, model metrics, and seasonal comparison.
    """
    city_key = city.lower()
    if city_key not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {city}")

    if battery_capacity_kwh <= 0 or daily_load_kwh <= 0 or panel_area_m2 <= 0:
        raise HTTPException(status_code=400, detail="Microgrid parameters must be positive")
    if panel_efficiency <= 0 or panel_efficiency > 1:
        raise HTTPException(status_code=400, detail="panel_efficiency must be between 0 and 1")

    try:
        weather_records = await fetch_hourly_weather(city_key, 24)
        feature_df = build_feature_dataframe(
            [record["features"] for record in weather_records],
            MODEL_II_FEATURES,
        )
        prediction_values = predict(city_key, feature_df)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    record = weather_records[0]
    weather = record["weather"]
    prediction_value = round(prediction_values[0], 2)
    advice = get_microgrid_recommendation(prediction_value)
    stats = get_dashboard_stats(city_key)

    latest = get_latest_prediction(city_key)
    if not latest or latest["timestamp"] != record["datetime"]:
        save_predictions(
            city_key,
            [
                {
                    "temperature": weather["temperature"],
                    "humidity": weather["humidity"],
                    "wind_speed": weather["wind_speed"],
                    "precipitation": weather["precipitation"],
                    "prediction": prediction_value,
                    "timestamp": record["datetime"],
                }
            ],
        )

    microgrid_result = await run_microgrid_optimization(
        MicrogridRequest(
            city=city_key,
            battery_capacity_kwh=battery_capacity_kwh,
            daily_load_kwh=daily_load_kwh,
            panel_area_m2=panel_area_m2,
            panel_efficiency=panel_efficiency,
            hours=24,
        ),
        weather_records=weather_records,
        prediction_values=prediction_values,
    )

    alert_data = evaluate_alert(
        [float(value) for value in prediction_values],
        microgrid_result.current_battery_soc_pct,
    )

    metrics_raw, seasonal_raw = get_dashboard_analytics(city_key)

    forecast_24h = [
        ForecastPoint(datetime=row["datetime"], prediction=round(float(value), 2))
        for row, value in zip(weather_records, prediction_values)
    ]

    return EnhancedDashboardResponse(
        city=city_key,
        temperature=weather["temperature"],
        humidity=weather["humidity"],
        wind_speed=weather["wind_speed"],
        precipitation=weather["precipitation"],
        prediction=prediction_value,
        timestamp=record["datetime"],
        microgrid_status=advice.status,
        microgrid_recommendation=advice.recommendation,
        microgrid_level=advice.level,
        total_predictions=stats["total_predictions"],
        predictions_by_city=stats["predictions_by_city"],
        latest_predictions=stats["latest_predictions"],
        average_prediction_by_city=stats["average_prediction_by_city"],
        forecast_24h=forecast_24h,
        microgrid_schedule=microgrid_result.schedule,
        current_battery_soc_pct=microgrid_result.current_battery_soc_pct,
        alert=AlertResponse(
            active=alert_data.active,
            message=alert_data.message,
            severity=alert_data.severity,
            solar_6h_kwh_m2=alert_data.solar_6h_kwh_m2,
            battery_soc_pct=alert_data.battery_soc_pct,
            load_shedding_priority=alert_data.load_shedding_priority,
        ),
        model_metrics=ModelMetrics(**metrics_raw),
        seasonal_comparison=SeasonalComparison(
            city=seasonal_raw["city"],
            dry_season=SeasonBucket(**seasonal_raw["dry_season"]),
            rainy_season=SeasonBucket(**seasonal_raw["rainy_season"]),
        ),
    )


@app.get("/api/dashboard/basic", response_model=DashboardResponse)
async def dashboard_basic(city: str = "douala"):
    """Legacy lightweight dashboard (revert-friendly)."""
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
    # The city comes from user input, so normalize and validate it.
    city = request.city.lower()
    if city not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {request.city}")

    try:
        # Fetch weather, build feature rows, and run model inference in batch.
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

    # Keep frontend response objects separate from database insert records.
    predictions: list[PredictionPoint] = []
    db_records = []

    for record, prediction_value in zip(weather_records, prediction_values):
        # Pydantic converts and validates the weather dictionary structure.
        weather = WeatherSnapshot(**record["weather"])
        rounded = round(prediction_value, 2)
        advice = get_microgrid_recommendation(rounded)

        # Response row: includes prediction, weather, and advice.
        predictions.append(
            PredictionPoint(
                datetime=record["datetime"],
                prediction=rounded,
                reference_ghi=round(float(record.get("reference_ghi", 0.0)), 2),
                weather=weather,
                microgrid=MicrogridAdvice(
                    status=advice.status,
                    recommendation=advice.recommendation,
                    level=advice.level,
                ),
            )
        )
        # Database row: only columns stored in SQLite.
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
    # Optional filter is validated only when present.
    if city and city.lower() not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {city}")
    return get_prediction_history(city=city, limit=limit)


@app.get("/api/microgrid/recommendation")
def microgrid_recommendation(prediction: float):
    """Return rule-based microgrid status for a given irradiance value."""
    # This endpoint is useful for testing recommendation thresholds alone.
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
    # Pydantic validates numeric constraints; this checks city support.
    city = request.city.lower()
    if city not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {request.city}")

    try:
        return await run_microgrid_optimization(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/reports/seasonal", response_model=SeasonalReportResponse)
def seasonal_report(city: str = "douala"):
    """FR-9: seasonal performance report (dry vs rainy)."""
    city_key = city.lower()
    if city_key not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {city}")

    payload = build_seasonal_report(city_key)
    return SeasonalReportResponse(
        city=payload["city"],
        summary=SeasonalComparison(
            city=payload["summary"]["city"],
            dry_season=SeasonBucket(**payload["summary"]["dry_season"]),
            rainy_season=SeasonBucket(**payload["summary"]["rainy_season"]),
        ),
        record_count=payload["record_count"],
        export_hint=payload["export_hint"],
    )


@app.get("/api/reports/seasonal/csv")
def seasonal_report_csv(city: str = "douala"):
    """FR-9: downloadable CSV export of seasonal performance data."""
    city_key = city.lower()
    if city_key not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {city}")

    csv_text = build_seasonal_report_csv(city_key)
    filename = f"solarpredict_{city_key}_seasonal_report.csv"
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _weekly_report_params(
    city: str,
    battery_capacity_kwh: float,
    daily_load_kwh: float,
    panel_area_m2: float,
    panel_efficiency: float,
) -> dict:
    city_key = city.lower()
    if city_key not in CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported city: {city}")
    if battery_capacity_kwh <= 0 or daily_load_kwh <= 0 or panel_area_m2 <= 0:
        raise HTTPException(status_code=400, detail="Microgrid parameters must be positive")
    if panel_efficiency <= 0 or panel_efficiency > 1:
        raise HTTPException(status_code=400, detail="panel_efficiency must be between 0 and 1")

    try:
        return await build_weekly_report(
            city_key,
            battery_capacity_kwh=battery_capacity_kwh,
            daily_load_kwh=daily_load_kwh,
            panel_area_m2=panel_area_m2,
            panel_efficiency=panel_efficiency,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/reports/weekly/pdf")
async def weekly_report_pdf(
    city: str = "douala",
    battery_capacity_kwh: float = DEFAULT_BATTERY_CAPACITY_KWH,
    daily_load_kwh: float = DEFAULT_DAILY_LOAD_KWH,
    panel_area_m2: float = DEFAULT_PANEL_AREA_M2,
    panel_efficiency: float = DEFAULT_PANEL_EFFICIENCY,
):
    """Download weekly solar + microgrid report as PDF."""
    payload = await _weekly_report_params(
        city,
        battery_capacity_kwh,
        daily_load_kwh,
        panel_area_m2,
        panel_efficiency,
    )
    pdf_bytes = build_weekly_report_pdf(payload)
    city_key = city.lower()
    filename = f"solarpredict_{city_key}_weekly_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
