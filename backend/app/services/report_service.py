"""Seasonal report generation with CSV export (FR-9)."""

import csv
import io

from .analytics_service import build_seasonal_report_rows, get_seasonal_comparison


def build_seasonal_report(city: str) -> dict:
    """JSON report comparing dry vs rainy season performance."""
    comparison = get_seasonal_comparison(city)
    rows = build_seasonal_report_rows(city)

    return {
        "city": city.lower(),
        "summary": comparison,
        "record_count": len(rows),
        "export_hint": "Use /api/reports/seasonal/csv for downloadable CSV.",
    }


def build_seasonal_report_csv(city: str) -> str:
    """Return seasonal performance data as CSV text."""
    rows = build_seasonal_report_rows(city)
    output = io.StringIO()

    if not rows:
        writer = csv.writer(output)
        writer.writerow(["message"])
        writer.writerow(["No prediction records available for this city."])
        return output.getvalue()

    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
