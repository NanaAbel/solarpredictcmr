"""Pydantic request/response schemas for API validation and documentation."""

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """POST /api/predict body."""
    city: str = Field(..., examples=["douala", "maroua"])
    hours: int = Field(default=24, ge=1, le=168)


class WeatherSnapshot(BaseModel):
    """Weather variables used as model inputs for a single hour."""
    temperature: float
    humidity: float
    wind_speed: float
    precipitation: float
    MO: int
    DY: int
    HR: int


class MicrogridAdvice(BaseModel):
    """Rule-based microgrid status and recommendation."""
    status: str
    recommendation: str
    level: str


class PredictionPoint(BaseModel):
    """Single hourly prediction result."""
    datetime: str
    prediction: float
    weather: WeatherSnapshot
    microgrid: MicrogridAdvice


class PredictionResponse(BaseModel):
    """Full prediction response returned to the frontend."""
    city: str
    model: str = "XGBoost Model II"
    hours: int
    predictions: list[PredictionPoint]


class DashboardResponse(BaseModel):
    """Live dashboard cards for the selected city."""
    city: str
    temperature: float
    humidity: float
    wind_speed: float
    precipitation: float
    prediction: float
    timestamp: str
    microgrid_status: str
    microgrid_recommendation: str
    microgrid_level: str
    total_predictions: int
    predictions_by_city: dict[str, int]
    latest_predictions: list[dict]
    average_prediction_by_city: dict[str, float]


class MicrogridRequest(BaseModel):
    """POST /api/microgrid/optimize body."""
    city: str
    battery_capacity_kwh: float = Field(..., gt=0)
    daily_load_kwh: float = Field(..., gt=0)
    panel_area_m2: float = Field(default=10.0, gt=0)
    panel_efficiency: float = Field(default=0.18, gt=0, le=1)
    hours: int = Field(default=24, ge=1, le=48)


class MicrogridHour(BaseModel):
    """One hour in the microgrid optimization schedule."""
    hour: int
    datetime: str
    prediction: float
    solar_generation_kwh: float
    load_kwh: float
    battery_soc_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    microgrid_status: str
    microgrid_recommendation: str


class MicrogridResponse(BaseModel):
    """Microgrid optimization summary and hourly schedule."""
    city: str
    battery_capacity_kwh: float
    daily_load_kwh: float
    predicted_solar_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    battery_use_kwh: float
    self_sufficiency_pct: float
    current_microgrid_status: str
    current_microgrid_recommendation: str
    schedule: list[MicrogridHour]
