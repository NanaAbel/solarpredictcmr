"""
Microgrid optimization logic (FR-6).

24-hour schedule with SoC limits: 20% minimum, 95% maximum.
"""

from .config import (
    BATTERY_SOC_DEFAULT_PCT,
    BATTERY_SOC_MAX_PCT,
    BATTERY_SOC_MIN_PCT,
    MODEL_II_FEATURES,
)
from .features import build_feature_dataframe
from .model_loader import predict
from .schemas import MicrogridHour, MicrogridRequest, MicrogridResponse
from .services.microgrid_recommendation import get_microgrid_recommendation
from .weather import fetch_hourly_weather


def _irradiance_to_kwh(irradiance_wm2: float, panel_area_m2: float, efficiency: float) -> float:
    """Convert W/m² irradiance to kWh for a 1-hour period."""
    return max(0.0, irradiance_wm2 * panel_area_m2 * efficiency / 1000.0)


def _soc_pct(soc_kwh: float, capacity_kwh: float) -> float:
    if capacity_kwh <= 0:
        return 0.0
    return round((soc_kwh / capacity_kwh) * 100.0, 2)


def simulate_microgrid(
    request: MicrogridRequest,
    weather_records: list[dict],
    prediction_values: list[float],
) -> MicrogridResponse:
    """Simulate hourly microgrid operation from pre-computed forecast data."""
    capacity = request.battery_capacity_kwh
    min_soc = capacity * BATTERY_SOC_MIN_PCT
    max_soc = capacity * BATTERY_SOC_MAX_PCT
    battery_soc = capacity * BATTERY_SOC_DEFAULT_PCT

    hourly_load = request.daily_load_kwh / 24.0
    grid_import = 0.0
    grid_export = 0.0
    battery_use = 0.0
    total_solar = 0.0
    schedule: list[MicrogridHour] = []

    for idx, record in enumerate(weather_records):
        prediction_value = round(prediction_values[idx], 2)
        advice = get_microgrid_recommendation(prediction_value)
        solar_kwh = _irradiance_to_kwh(
            prediction_value, request.panel_area_m2, request.panel_efficiency
        )
        total_solar += solar_kwh

        net = solar_kwh - hourly_load
        hour_import = 0.0
        hour_export = 0.0
        charge_kwh = 0.0
        discharge_kwh = 0.0

        if net >= 0:
            charge_room = max(0.0, max_soc - battery_soc)
            charge_kwh = min(net, charge_room)
            battery_soc += charge_kwh
            battery_use += charge_kwh
            surplus = net - charge_kwh
            if surplus > 0:
                hour_export = surplus
                grid_export += surplus
        else:
            deficit = abs(net)
            discharge_room = max(0.0, battery_soc - min_soc)
            discharge_kwh = min(deficit, discharge_room)
            battery_soc -= discharge_kwh
            battery_use += discharge_kwh
            remaining = deficit - discharge_kwh
            if remaining > 0:
                hour_import = remaining
                grid_import += remaining

        schedule.append(
            MicrogridHour(
                hour=idx,
                datetime=record["datetime"],
                prediction=prediction_value,
                solar_generation_kwh=round(solar_kwh, 3),
                load_kwh=round(hourly_load, 3),
                battery_soc_kwh=round(battery_soc, 3),
                battery_soc_pct=_soc_pct(battery_soc, capacity),
                charge_kwh=round(charge_kwh, 3),
                discharge_kwh=round(discharge_kwh, 3),
                grid_import_kwh=round(hour_import, 3),
                grid_export_kwh=round(hour_export, 3),
                microgrid_status=advice.status,
                microgrid_recommendation=advice.recommendation,
            )
        )

    self_sufficiency = 0.0
    total_load_kwh = hourly_load * len(weather_records)
    if total_load_kwh > 0:
        self_sufficiency = min(
            100.0,
            ((total_load_kwh - grid_import) / total_load_kwh) * 100.0,
        )

    current_advice = get_microgrid_recommendation(prediction_values[0])
    # Current hour = first forecast step (not end-of-day SoC).
    if schedule:
        current_soc_pct = schedule[0].battery_soc_pct
    else:
        current_soc_pct = _soc_pct(capacity * BATTERY_SOC_DEFAULT_PCT, capacity)

    return MicrogridResponse(
        city=request.city.lower(),
        battery_capacity_kwh=capacity,
        daily_load_kwh=request.daily_load_kwh,
        predicted_solar_kwh=round(total_solar, 2),
        grid_import_kwh=round(grid_import, 2),
        grid_export_kwh=round(grid_export, 2),
        battery_use_kwh=round(battery_use, 2),
        self_sufficiency_pct=round(self_sufficiency, 2),
        battery_soc_min_pct=BATTERY_SOC_MIN_PCT * 100,
        battery_soc_max_pct=BATTERY_SOC_MAX_PCT * 100,
        current_battery_soc_pct=current_soc_pct,
        current_microgrid_status=current_advice.status,
        current_microgrid_recommendation=current_advice.recommendation,
        schedule=schedule,
    )


async def run_microgrid_optimization(
    request: MicrogridRequest,
    *,
    weather_records: list[dict] | None = None,
    prediction_values: list[float] | None = None,
) -> MicrogridResponse:
    """Fetch forecast if needed, then simulate battery/grid operation."""
    if weather_records is None or prediction_values is None:
        weather_records = await fetch_hourly_weather(request.city, request.hours)
        feature_df = build_feature_dataframe(
            [record["features"] for record in weather_records],
            MODEL_II_FEATURES,
        )
        prediction_values = predict(request.city, feature_df)

    return simulate_microgrid(request, weather_records, prediction_values)
