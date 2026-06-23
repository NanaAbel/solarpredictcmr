/**
 * Reports — seasonal and weekly performance exports.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, downloadSeasonalCsv, downloadWeeklyPdf } from "../api/client";
import { loadMicrogridSettings } from "../utils/microgridSettings";

export default function Reports() {
  const [city, setCity] = useState("douala");
  const [microgridSettings] = useState(loadMicrogridSettings);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [weeklyError, setWeeklyError] = useState("");
  const [loading, setLoading] = useState(true);
  const [weeklyDownloading, setWeeklyDownloading] = useState(false);
  const chartRef = useRef(null);

  const loadReport = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.seasonalReport(city);
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [city]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handleWeeklyDownload = async () => {
    setWeeklyDownloading(true);
    setWeeklyError("");
    try {
      await downloadWeeklyPdf(city, microgridSettings);
    } catch (err) {
      setWeeklyError(err.message);
    } finally {
      setWeeklyDownloading(false);
    }
  };

  const chartData = report?.summary
    ? [
        {
          season: "Dry",
          avg: report.summary.dry_season.avg_prediction_wm2,
          count: report.summary.dry_season.sample_count,
        },
        {
          season: "Rainy",
          avg: report.summary.rainy_season.avg_prediction_wm2,
          count: report.summary.rainy_season.sample_count,
        },
      ]
    : [];

  const exportChartPng = () => {
    const svg = chartRef.current?.querySelector("svg");
    if (!svg) return;

    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svg);
    const canvas = document.createElement("canvas");
    const image = new Image();
    const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    image.onload = () => {
      canvas.width = image.width || 900;
      canvas.height = image.height || 400;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#0b1220";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);

      const link = document.createElement("a");
      link.download = `solarpredict_${city}_seasonal_chart.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    };
    image.src = url;
  };

  return (
    <div>
      <header className="page-header page-header--row">
        <div>
          <h2>Reports</h2>
          <p>Seasonal analytics and weekly solar + microgrid exports.</p>
        </div>
        <div className="toolbar toolbar--inline">
          <div className="field">
            <label>City</label>
            <select value={city} onChange={(e) => setCity(e.target.value)}>
              <option value="douala">Douala</option>
              <option value="maroua">Maroua</option>
            </select>
          </div>
          <button className="btn btn-secondary" onClick={loadReport} disabled={loading}>
            Refresh
          </button>
        </div>
      </header>

      <section className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginBottom: 8 }}>Weekly Report — Solar & Microgrid</h3>
        <p style={{ marginBottom: 16, color: "var(--text-muted)" }}>
          Download a 7-day PDF with solar irradiance and microgrid energy summaries.
          Uses your Microgrid page settings ({microgridSettings.battery_capacity_kwh} kWh battery,{" "}
          {microgridSettings.daily_load_kwh} kWh/day load, {microgridSettings.panel_area_m2} m² panels).
        </p>

        <div className="toolbar">
          <button className="btn" onClick={handleWeeklyDownload} disabled={weeklyDownloading}>
            {weeklyDownloading ? "Preparing PDF..." : "Download Weekly PDF"}
          </button>
        </div>

        {weeklyError && <div className="error-box" style={{ marginTop: 16 }}>{weeklyError}</div>}
      </section>

      <section className="card">
        <h3 style={{ marginBottom: 8 }}>Seasonal Report — Dry vs Rainy</h3>
        <p style={{ marginBottom: 16, color: "var(--text-muted)" }}>
          Long-term seasonal comparison from stored prediction history (FR-9).
        </p>

        {error && <div className="error-box">{error}</div>}

        <div className="toolbar" style={{ marginBottom: 16 }}>
          <button className="btn" onClick={() => downloadSeasonalCsv(city)}>
            Download CSV
          </button>
          <button className="btn btn-secondary" onClick={exportChartPng} disabled={!chartData.length}>
            Export Chart PNG
          </button>
        </div>

        {loading && <div className="empty-box">Loading report...</div>}

        {!loading && report && (
          <>
            <div className="grid grid-2" style={{ marginBottom: 20 }}>
              <div className="card stat-card">
                <h3>Dry Season Avg GHI</h3>
                <strong>{report.summary.dry_season.avg_prediction_wm2} W/m²</strong>
                <p style={{ marginTop: 8, color: "var(--text-muted)" }}>
                  {report.summary.dry_season.sample_count} samples
                </p>
              </div>
              <div className="card stat-card">
                <h3>Rainy Season Avg GHI</h3>
                <strong>{report.summary.rainy_season.avg_prediction_wm2} W/m²</strong>
                <p style={{ marginTop: 8, color: "var(--text-muted)" }}>
                  {report.summary.rainy_season.sample_count} samples
                </p>
              </div>
            </div>

            <div className="card chart-card" ref={chartRef}>
              <h3 style={{ marginBottom: 16 }}>Seasonal Performance Chart</h3>
              {chartData.some((row) => row.avg > 0) ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="season" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="avg" fill="#f59e0b" name="Avg GHI (W/m²)" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-box">No seasonal data yet. Use the dashboard and prediction pages first.</div>
              )}
            </div>

            <p style={{ marginTop: 16, color: "var(--text-muted)" }}>
              {report.record_count} records included · {report.export_hint}
            </p>
          </>
        )}
      </section>
    </div>
  );
}
