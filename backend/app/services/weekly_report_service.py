"""Weekly solar energy and microgrid report generation."""

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..config import MODEL_II_FEATURES
from ..features import build_feature_dataframe
from ..microgrid import _irradiance_to_kwh, simulate_microgrid
from ..model_loader import predict
from ..schemas import MicrogridRequest
from ..weather import fetch_hourly_weather

WEEKLY_HOURS = 168


async def build_weekly_report(
    city: str,
    *,
    battery_capacity_kwh: float,
    daily_load_kwh: float,
    panel_area_m2: float,
    panel_efficiency: float,
) -> dict:
    """Build a 7-day forecast report with solar and microgrid summaries."""
    city_key = city.lower()
    weather_records = await fetch_hourly_weather(city_key, WEEKLY_HOURS)
    feature_df = build_feature_dataframe(
        [record["features"] for record in weather_records],
        MODEL_II_FEATURES,
    )
    prediction_values = predict(city_key, feature_df)

    microgrid_request = MicrogridRequest(
        city=city_key,
        battery_capacity_kwh=battery_capacity_kwh,
        daily_load_kwh=daily_load_kwh,
        panel_area_m2=panel_area_m2,
        panel_efficiency=panel_efficiency,
        hours=WEEKLY_HOURS,
    )
    microgrid_result = simulate_microgrid(
        microgrid_request, weather_records, prediction_values
    )

    predictions = [round(float(value), 2) for value in prediction_values]
    count = len(predictions)
    avg_ghi = sum(predictions) / count if count else 0.0
    total_panel_kwh = sum(
        _irradiance_to_kwh(value, panel_area_m2, panel_efficiency)
        for value in predictions
    )

    soc_values = [row.battery_soc_pct for row in microgrid_result.schedule]
    avg_soc = sum(soc_values) / len(soc_values) if soc_values else 0.0

    period_start = weather_records[0]["datetime"] if weather_records else ""
    period_end = weather_records[-1]["datetime"] if weather_records else ""

    return {
        "city": city_key,
        "period_start": period_start,
        "period_end": period_end,
        "solar": {
            "avg_ghi_wm2": round(avg_ghi, 2),
            "peak_ghi_wm2": round(max(predictions), 2) if predictions else 0.0,
            "min_ghi_wm2": round(min(predictions), 2) if predictions else 0.0,
            "total_panel_energy_kwh": round(total_panel_kwh, 2),
            "sample_hours": count,
        },
        "microgrid": {
            "battery_capacity_kwh": battery_capacity_kwh,
            "daily_load_kwh": daily_load_kwh,
            "panel_area_m2": panel_area_m2,
            "predicted_solar_kwh": microgrid_result.predicted_solar_kwh,
            "grid_import_kwh": microgrid_result.grid_import_kwh,
            "grid_export_kwh": microgrid_result.grid_export_kwh,
            "battery_use_kwh": microgrid_result.battery_use_kwh,
            "self_sufficiency_pct": microgrid_result.self_sufficiency_pct,
            "avg_battery_soc_pct": round(avg_soc, 2),
        },
        "_weather_records": weather_records,
        "_prediction_values": predictions,
        "_microgrid_schedule": microgrid_result.schedule,
    }


def _fmt_period(iso_start: str, iso_end: str) -> str:
    try:
        start = datetime.fromisoformat(iso_start)
        end = datetime.fromisoformat(iso_end)
        return f"{start.strftime('%d %b %Y')} – {end.strftime('%d %b %Y')}"
    except (TypeError, ValueError):
        return f"{iso_start} – {iso_end}"


def _fmt_hour(iso_ts: str) -> str:
    try:
        return datetime.fromisoformat(iso_ts).strftime("%a %d %b %H:%M")
    except (TypeError, ValueError):
        return iso_ts


def _summary_table(rows: list[list[str]]) -> Table:
    table = Table(rows, colWidths=[2.8 * inch, 2.4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _hourly_table(headers: list[str], rows: list[list], col_widths: list[float]) -> Table:
    data = [headers, *rows]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def build_weekly_report_pdf(report: dict) -> bytes:
    """Export weekly solar + microgrid data as a PDF document."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="SolarPredict Weekly Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=6,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=14,
        textColor=colors.HexColor("#475569"),
    )
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=10,
        spaceAfter=8,
        textColor=colors.HexColor("#0f172a"),
    )

    city_label = report["city"].capitalize()
    period_label = _fmt_period(report["period_start"], report["period_end"])
    solar = report["solar"]
    microgrid = report["microgrid"]

    story = [
        Paragraph("SolarPredict Weekly Report", title_style),
        Paragraph(f"{city_label} · {period_label}", subtitle_style),
        Paragraph("Solar Energy Summary", section_style),
        _summary_table(
            [
                ["Metric", "Value"],
                ["Average GHI", f"{solar['avg_ghi_wm2']} W/m²"],
                ["Peak GHI", f"{solar['peak_ghi_wm2']} W/m²"],
                ["Minimum GHI", f"{solar['min_ghi_wm2']} W/m²"],
                ["Total panel energy", f"{solar['total_panel_energy_kwh']} kWh"],
                ["Forecast hours", str(solar["sample_hours"])],
            ]
        ),
        Spacer(1, 0.2 * inch),
        Paragraph("Microgrid Summary", section_style),
        _summary_table(
            [
                ["Metric", "Value"],
                ["Battery capacity", f"{microgrid['battery_capacity_kwh']} kWh"],
                ["Daily load", f"{microgrid['daily_load_kwh']} kWh"],
                ["Panel area", f"{microgrid['panel_area_m2']} m²"],
                ["Predicted solar generation", f"{microgrid['predicted_solar_kwh']} kWh"],
                ["Grid import", f"{microgrid['grid_import_kwh']} kWh"],
                ["Grid export", f"{microgrid['grid_export_kwh']} kWh"],
                ["Battery use", f"{microgrid['battery_use_kwh']} kWh"],
                ["Self-sufficiency", f"{microgrid['self_sufficiency_pct']}%"],
                ["Average battery SoC", f"{microgrid['avg_battery_soc_pct']}%"],
            ]
        ),
        PageBreak(),
    ]

    solar_rows = []
    for record, prediction in zip(report["_weather_records"], report["_prediction_values"]):
        weather = record["weather"]
        solar_rows.append(
            [
                _fmt_hour(record["datetime"]),
                str(prediction),
                str(weather["temperature"]),
                str(weather["humidity"]),
                str(weather["wind_speed"]),
                str(weather["precipitation"]),
            ]
        )

    story.append(Paragraph("Solar Energy — Hourly Forecast", section_style))
    story.append(
        _hourly_table(
            ["Time", "GHI (W/m²)", "Temp (°C)", "Humidity (%)", "Wind (m/s)", "Rain (mm)"],
            solar_rows,
            [1.5 * inch, 0.85 * inch, 0.75 * inch, 0.85 * inch, 0.75 * inch, 0.75 * inch],
        )
    )
    story.append(PageBreak())

    microgrid_rows = []
    for row in report["_microgrid_schedule"]:
        microgrid_rows.append(
            [
                _fmt_hour(row.datetime),
                str(row.prediction),
                str(row.solar_generation_kwh),
                str(row.load_kwh),
                f"{row.battery_soc_pct}%",
                str(row.grid_import_kwh),
                str(row.grid_export_kwh),
                row.microgrid_status,
            ]
        )

    story.append(Paragraph("Microgrid — Hourly Schedule", section_style))
    story.append(
        _hourly_table(
            [
                "Time",
                "GHI (W/m²)",
                "Solar (kWh)",
                "Load (kWh)",
                "SoC",
                "Import (kWh)",
                "Export (kWh)",
                "Status",
            ],
            microgrid_rows,
            [1.35 * inch, 0.7 * inch, 0.65 * inch, 0.6 * inch, 0.5 * inch, 0.65 * inch, 0.65 * inch, 1.0 * inch],
        )
    )

    doc.build(story)
    return buffer.getvalue()
