"""
Alert generation (FR-7).

Triggers when 6-hour predicted solar production is below 0.5 kWh/m²
AND battery state of charge is below 40%.
"""

from dataclasses import dataclass

from ..config import (
    ALERT_BATTERY_SOC_PCT,
    ALERT_FORECAST_HOURS,
    ALERT_SOLAR_THRESHOLD_KWH_M2,
)

LOAD_SHEDDING_PRIORITY = [
    "1. Defer non-essential loads (HVAC comfort, water heating)",
    "2. Reduce secondary lighting and signage",
    "3. Limit appliance use (washing, cooking during peak deferral)",
    "4. Operate critical loads only (communications, refrigeration, security)",
]


@dataclass(frozen=True)
class AlertResult:
    active: bool
    message: str
    severity: str  # none | warning | critical
    solar_6h_kwh_m2: float
    battery_soc_pct: float
    load_shedding_priority: list[str]


def ghi_to_kwh_m2(irradiance_wm2: float) -> float:
    """Convert hourly GHI (W/m²) to energy density (kWh/m²) for one hour."""
    return max(0.0, irradiance_wm2 / 1000.0)


def evaluate_alert(
    predictions_wm2: list[float],
    battery_soc_pct: float,
) -> AlertResult:
    """
    FR-7: Alert when next 6 h solar < 0.5 kWh/m² AND SoC < 40%.
    """
    window = predictions_wm2[:ALERT_FORECAST_HOURS]
    solar_6h = round(sum(ghi_to_kwh_m2(value) for value in window), 3)

    low_solar = solar_6h < ALERT_SOLAR_THRESHOLD_KWH_M2
    low_battery = battery_soc_pct < ALERT_BATTERY_SOC_PCT
    active = low_solar and low_battery

    if active:
        message = (
            f"Low solar forecast ({solar_6h} kWh/m² over 6 h) with battery at "
            f"{round(battery_soc_pct, 1)}%. Initiate load shedding."
        )
        severity = "critical"
    elif low_solar or low_battery:
        message = (
            f"Watch condition: 6 h solar={solar_6h} kWh/m², "
            f"battery={round(battery_soc_pct, 1)}%."
        )
        severity = "warning"
    else:
        message = "No alert — solar production and battery levels are adequate."
        severity = "none"

    return AlertResult(
        active=active,
        message=message,
        severity=severity,
        solar_6h_kwh_m2=solar_6h,
        battery_soc_pct=round(battery_soc_pct, 2),
        load_shedding_priority=list(LOAD_SHEDDING_PRIORITY) if active else [],
    )
