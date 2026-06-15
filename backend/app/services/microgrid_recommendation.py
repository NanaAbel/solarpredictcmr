"""
Microgrid recommendation engine.

Maps predicted solar irradiance (W/m²) to operational status and advice.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MicrogridRecommendation:
    """Status and recommendation for a given irradiance level."""
    status: str
    recommendation: str
    level: str  # high | moderate | low


def get_microgrid_recommendation(prediction: float) -> MicrogridRecommendation:
    """
    Return microgrid status and recommendation based on predicted irradiance.

    Rules:
      - prediction > 700        → High Solar Energy
      - 400 <= prediction <= 700 → Moderate Solar Energy
      - prediction < 400        → Low Solar Energy
    """
    if prediction > 700:
        return MicrogridRecommendation(
            status="High Solar Energy",
            recommendation="Charge batteries and prioritize solar generation",
            level="high",
        )
    if prediction >= 400:
        return MicrogridRecommendation(
            status="Moderate Solar Energy",
            recommendation="Hybrid operation mode",
            level="moderate",
        )
    return MicrogridRecommendation(
        status="Low Solar Energy",
        recommendation="Use battery reserves or grid support",
        level="low",
    )
