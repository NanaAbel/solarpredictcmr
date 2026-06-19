"""
Microgrid optimization logic.

Combines irradiance-based recommendations with battery/grid simulation.
"""

from .config import MODEL_II_FEATURES
from .features import build_feature_dataframe
from .model_loader import predict
from .schemas import MicrogridHour, MicrogridRequest, MicrogridResponse
from .services.microgrid_recommendation import get_microgrid_recommendation
from .weather import fetch_hourly_weather


def _irradiance_to_kwh(irradiance_wm2: float, panel_area_m2: float, efficiency: float) -> float:
    """Convert W/m² irradiance to kWh for a 1-hour period."""
    # W/m2 * m2 gives W; divide by 1000 and assume one forecast hour.
    return max(0.0, irradiance_wm2 * panel_area_m2 * efficiency / 1000.0)


async def run_microgrid_optimization(request: MicrogridRequest) -> MicrogridResponse:
    """Simulate hourly microgrid operation with irradiance-based advice."""
    # Reuse the same weather -> features -> XGBoost pipeline as /api/predict.
    weather_records = await fetch_hourly_weather(request.city, request.hours)
    feature_df = build_feature_dataframe(
        [record["features"] for record in weather_records],
        MODEL_II_FEATURES,
    )
    prediction_values = predict(request.city, feature_df)

    # Simplifying assumptions: load is evenly distributed and battery starts 50% full.
    hourly_load = request.daily_load_kwh / request.hours
    battery_soc = request.battery_capacity_kwh * 0.5
    # Accumulators for the final optimization summary cards.
    grid_import = 0.0
    grid_export = 0.0
    battery_use = 0.0
    total_solar = 0.0
    schedule: list[MicrogridHour] = []

    for idx, record in enumerate(weather_records):
        # Convert each irradiance prediction into available solar energy.
        prediction_value = round(prediction_values[idx], 2)
        advice = get_microgrid_recommendation(prediction_value)
        solar_kwh = _irradiance_to_kwh(
            prediction_value, request.panel_area_m2, request.panel_efficiency
        )
        total_solar += solar_kwh

        # Positive net means surplus solar; negative net means demand deficit.
        net = solar_kwh - hourly_load
        hour_import = 0.0
        hour_export = 0.0

        if net >= 0:
            # Surplus charges the battery first, then exports to the grid.
            charge_room = request.battery_capacity_kwh - battery_soc
            charge = min(net, charge_room)
            battery_soc += charge
            battery_use += charge
            surplus = net - charge
            if surplus > 0:
                hour_export = surplus
                grid_export += surplus
        else:
            # Deficit is covered by battery first, then imported from the grid.
            deficit = abs(net)
            discharge = min(deficit, battery_soc)
            battery_soc -= discharge
            battery_use += discharge
            remaining = deficit - discharge
            if remaining > 0:
                hour_import = remaining
                grid_import += remaining

        # Store one detailed row for the frontend table and bar chart.
        schedule.append(
            MicrogridHour(
                hour=idx,
                datetime=record["datetime"],
                prediction=prediction_value,
                solar_generation_kwh=round(solar_kwh, 3),
                load_kwh=round(hourly_load, 3),
                battery_soc_kwh=round(battery_soc, 3),
                grid_import_kwh=round(hour_import, 3),
                grid_export_kwh=round(hour_export, 3),
                microgrid_status=advice.status,
                microgrid_recommendation=advice.recommendation,
            )
        )

    # Self-sufficiency measures how much load was served without grid import.
    self_sufficiency = 0.0
    if request.daily_load_kwh > 0:
        self_sufficiency = min(
            100.0,
            ((request.daily_load_kwh - grid_import) / request.daily_load_kwh) * 100.0,
        )

    # The summary badge uses the first/current forecast hour.
    current_advice = get_microgrid_recommendation(prediction_values[0])

    return MicrogridResponse(
        city=request.city.lower(),
        battery_capacity_kwh=request.battery_capacity_kwh,
        daily_load_kwh=request.daily_load_kwh,
        predicted_solar_kwh=round(total_solar, 2),
        grid_import_kwh=round(grid_import, 2),
        grid_export_kwh=round(grid_export, 2),
        battery_use_kwh=round(battery_use, 2),
        self_sufficiency_pct=round(self_sufficiency, 2),
        current_microgrid_status=current_advice.status,
        current_microgrid_recommendation=current_advice.recommendation,
        schedule=schedule,
    )
