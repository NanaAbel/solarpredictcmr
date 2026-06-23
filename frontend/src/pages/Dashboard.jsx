/**
 * FR-8 Dashboard — GHI chart, SoC gauge, microgrid schedule, metrics, alerts.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import AlertBanner from "../components/AlertBanner";
import BatteryGauge from "../components/BatteryGauge";
import RecommendationBadge from "../components/RecommendationBadge";
import StatCard from "../components/StatCard";
import { loadMicrogridSettings } from "../utils/microgridSettings";

export default function Dashboard() {
  const [city, setCity] = useState("douala");
  const [microgridSettings, setMicrogridSettings] = useState(loadMicrogridSettings);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const hasLoadedRef = useRef(false);

  const loadDashboard = useCallback(async () => {
    if (hasLoadedRef.current) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError("");
    try {
      const response = await api.dashboard(city, microgridSettings);
      setData(response);
      hasLoadedRef.current = true;
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [city, microgridSettings]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    const syncSettings = () => setMicrogridSettings(loadMicrogridSettings());
    window.addEventListener("microgrid-settings-changed", syncSettings);
    window.addEventListener("storage", syncSettings);
    return () => {
      window.removeEventListener("microgrid-settings-changed", syncSettings);
      window.removeEventListener("storage", syncSettings);
    };
  }, []);

  const ghiChartData =
    data?.forecast_24h?.map((item) => ({
      time: new Date(item.datetime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      ghi: item.prediction,
    })) || [];

  const seasonalChartData = data?.seasonal_comparison
    ? [
        { season: "Dry", avg: data.seasonal_comparison.dry_season.avg_prediction_wm2 },
        { season: "Rainy", avg: data.seasonal_comparison.rainy_season.avg_prediction_wm2 },
      ]
    : [];

  return (
    <div>
      <header className="page-header page-header--row">
        <div>
          <h2>Dashboard</h2>
          <p>24 h GHI forecast, microgrid schedule, alerts, and seasonal analytics (FR-8).</p>
        </div>
        <div className="toolbar toolbar--inline">
          <div className="field">
            <label>Location (FR-10)</label>
            <select value={city} onChange={(e) => setCity(e.target.value)}>
              <option value="douala">Douala</option>
              <option value="maroua">Maroua</option>
            </select>
          </div>
          <button className="btn btn-secondary" onClick={loadDashboard} disabled={loading || refreshing}>
            {loading || refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </header>

      {error && <div className="error-box">{error}</div>}

      {data?.alert && <AlertBanner alert={data.alert} />}

      <section className="grid grid-3">
        <StatCard label="Current Temperature" value={data?.temperature ?? "—"} unit="°C" icon="🌡" />
        <StatCard label="Humidity" value={data?.humidity ?? "—"} unit="%" icon="💧" />
        <StatCard label="Wind Speed" value={data?.wind_speed ?? "—"} unit=" m/s" icon="🌬" />
        <StatCard label="Precipitation" value={data?.precipitation ?? "—"} unit=" mm" icon="🌧" />
        <StatCard
          label="Current GHI"
          value={data?.prediction ?? "—"}
          unit=" W/m²"
          icon="☀"
          variant="accent"
        />
        {data ? (
          <RecommendationBadge
            status={data.microgrid_status}
            recommendation={data.microgrid_recommendation}
            level={data.microgrid_level}
          />
        ) : (
          <div className="card stat-card">
            <h3>Microgrid Recommendation</h3>
            <strong>—</strong>
          </div>
        )}
      </section>

      <section className="grid grid-2" style={{ marginTop: 20 }}>
        <div className="card chart-card">
          <h3 style={{ marginBottom: 16 }}>24-Hour GHI Prediction Chart</h3>
          {ghiChartData.length ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={ghiChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="time" stroke="#94a3b8" minTickGap={24} />
                <YAxis stroke="#94a3b8" label={{ value: "W/m²", angle: -90, position: "insideLeft", fill: "#94a3b8" }} />
                <Tooltip />
                <Line type="monotone" dataKey="ghi" stroke="#f59e0b" strokeWidth={3} dot={false} name="GHI" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-box">No forecast data.</div>
          )}
        </div>

        <BatteryGauge
          socPct={data?.current_battery_soc_pct}
          minPct={20}
          maxPct={95}
          currentHour={
            data?.microgrid_schedule?.[0]?.datetime
              ? new Date(data.microgrid_schedule[0].datetime).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : null
          }
          batteryCapacityKwh={microgridSettings.battery_capacity_kwh}
        />
      </section>

      <section className="grid grid-2" style={{ marginTop: 20 }}>
        <div className="card chart-card">
          <h3 style={{ marginBottom: 16 }}>Seasonal Comparison (Dry vs Rainy)</h3>
          {seasonalChartData.some((row) => row.avg > 0) ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={seasonalChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="season" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                <Bar dataKey="avg" fill="#38bdf8" name="Avg GHI (W/m²)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-box">Run predictions to build seasonal history.</div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Model Performance Metrics</h3>
          {data?.model_metrics ? (
            <ul className="metrics-list">
              <li><span>Model</span><strong>{data.model_metrics.model_name}</strong></li>
              <li><span>Samples</span><strong>{data.model_metrics.sample_count}</strong></li>
              <li><span>Mean GHI</span><strong>{data.model_metrics.mean_prediction_wm2} W/m²</strong></li>
              <li><span>Min / Max</span><strong>{data.model_metrics.min_prediction_wm2} / {data.model_metrics.max_prediction_wm2} W/m²</strong></li>
              <li><span>Std Dev</span><strong>{data.model_metrics.std_prediction_wm2} W/m²</strong></li>
            </ul>
          ) : (
            <div className="empty-box">No metrics yet.</div>
          )}
          {data?.model_metrics?.note && (
            <p style={{ marginTop: 12, fontSize: "0.85rem", color: "var(--text-muted)" }}>
              {data.model_metrics.note}
            </p>
          )}
        </div>
      </section>

      <section className="card" style={{ marginTop: 20 }}>
        <h3 style={{ marginBottom: 16 }}>Microgrid Schedule (24 h, SoC 20–95%)</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Hour</th>
                <th>GHI (W/m²)</th>
                <th>Solar (kWh)</th>
                <th>Load (kWh)</th>
                <th>SoC (%)</th>
                <th>Charge</th>
                <th>Discharge</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(data?.microgrid_schedule || []).slice(0, 24).map((row) => (
                <tr key={row.datetime}>
                  <td>{new Date(row.datetime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                  <td>{row.prediction}</td>
                  <td>{row.solar_generation_kwh}</td>
                  <td>{row.load_kwh}</td>
                  <td>{row.battery_soc_pct}%</td>
                  <td>{row.charge_kwh}</td>
                  <td>{row.discharge_kwh}</td>
                  <td>{row.microgrid_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {data && (
        <section className="card" style={{ marginTop: 20 }}>
          <p style={{ color: "var(--text-muted)" }}>
            Last updated: {new Date(data.timestamp).toLocaleString()} — {data.city} ·{" "}
            {data.total_predictions} predictions stored
          </p>
        </section>
      )}
    </div>
  );
}
