"""
Analytics helpers for dashboard metrics and seasonal comparison (FR-8, FR-9).
"""

from datetime import datetime

from ..config import CITIES
from ..database import get_prediction_history
from ..features import _season_flags


def _empty_metrics() -> dict:
    return {
        "sample_count": 0,
        "mean_prediction_wm2": 0.0,
        "min_prediction_wm2": 0.0,
        "max_prediction_wm2": 0.0,
        "std_prediction_wm2": 0.0,
        "model_name": "XGBoost Model II",
        "note": "Metrics computed from stored operational predictions (no negative values).",
    }


def get_model_metrics(city: str) -> dict:
    """Model performance proxies derived from stored prediction history."""
    metrics, _ = get_dashboard_analytics(city)
    return metrics


def get_seasonal_comparison(city: str) -> dict:
    """Compare average GHI between dry and rainy seasons (FR-8, FR-9)."""
    _, seasonal = get_dashboard_analytics(city)
    return seasonal


def get_dashboard_analytics(city: str) -> tuple[dict, dict]:
    """Load history once and derive metrics + seasonal comparison together."""
    city_key = city.lower()
    records = get_prediction_history(city=city_key, limit=5000)

    if not records:
        return _empty_metrics(), {
            "city": city_key,
            "dry_season": {
                "label": "Dry season",
                "avg_prediction_wm2": 0.0,
                "sample_count": 0,
            },
            "rainy_season": {
                "label": "Rainy season",
                "avg_prediction_wm2": 0.0,
                "sample_count": 0,
            },
        }

    values = [float(row["prediction"]) for row in records]
    count = len(values)
    mean_val = sum(values) / count
    variance = sum((value - mean_val) ** 2 for value in values) / count
    std_val = variance**0.5

    metrics = {
        "sample_count": count,
        "mean_prediction_wm2": round(mean_val, 2),
        "min_prediction_wm2": round(min(values), 2),
        "max_prediction_wm2": round(max(values), 2),
        "std_prediction_wm2": round(std_val, 2),
        "model_name": "XGBoost Model II",
        "note": "Metrics computed from stored operational predictions (no negative values).",
    }

    dry_values: list[float] = []
    rainy_values: list[float] = []

    for row in records:
        month = datetime.fromisoformat(row["timestamp"]).month
        is_dry, is_rainy = _season_flags(month, city_key)
        value = float(row["prediction"])
        if is_dry:
            dry_values.append(value)
        if is_rainy:
            rainy_values.append(value)

    def _avg(items: list[float]) -> float:
        return round(sum(items) / len(items), 2) if items else 0.0

    seasonal = {
        "city": city_key,
        "dry_season": {
            "label": "Dry season",
            "avg_prediction_wm2": _avg(dry_values),
            "sample_count": len(dry_values),
        },
        "rainy_season": {
            "label": "Rainy season",
            "avg_prediction_wm2": _avg(rainy_values),
            "sample_count": len(rainy_values),
        },
    }

    return metrics, seasonal


def build_seasonal_report_rows(city: str) -> list[dict]:
    """Detailed rows for CSV export grouped by season and month."""
    city_key = city.lower()
    records = get_prediction_history(city=city_key, limit=10000)
    rows: list[dict] = []

    for row in records:
        ts = datetime.fromisoformat(row["timestamp"])
        is_dry, is_rainy = _season_flags(ts.month, city_key)
        if is_dry:
            season = "dry"
        elif is_rainy:
            season = "rainy"
        else:
            season = "unknown"

        rows.append(
            {
                "city": row["city"],
                "timestamp": row["timestamp"],
                "month": ts.month,
                "season": season,
                "prediction_wm2": row["prediction"],
                "temperature_c": row["temperature"],
                "humidity_pct": row["humidity"],
                "wind_speed_ms": row["wind_speed"],
                "precipitation_mm": row["precipitation"],
            }
        )

    return rows
