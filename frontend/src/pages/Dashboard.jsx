/**
 * Dashboard — live weather cards, prediction, and microgrid recommendation.
 */
import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import StatCard from "../components/StatCard";
import RecommendationBadge from "../components/RecommendationBadge";

export default function Dashboard() {
  // Page state: selected city, API response, error text, and loading flag.
  const [city, setCity] = useState("douala");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadDashboard = useCallback(async () => {
    // Refresh the live dashboard from FastAPI whenever the city changes.
    setLoading(true);
    setError("");
    try {
      const response = await api.dashboard(city);
      setData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [city]);

  useEffect(() => {
    // Load data automatically when the page opens or loadDashboard changes.
    loadDashboard();
  }, [loadDashboard]);

  // Convert backend aggregate data into the shape required by Recharts.
  const chartData = data
    ? Object.entries(data.average_prediction_by_city || {}).map(([name, value]) => ({
        city: name.charAt(0).toUpperCase() + name.slice(1),
        prediction: value,
      }))
    : [];

  return (
    <div>
      <header className="page-header page-header--row">
        <div>
          <h2>Dashboard</h2>
          <p>Live weather, solar prediction, and microgrid recommendations.</p>
        </div>
        <div className="toolbar toolbar--inline">
          <div className="field">
            <label>City</label>
            <select value={city} onChange={(e) => setCity(e.target.value)}>
              <option value="douala">Douala</option>
              <option value="maroua">Maroua</option>
            </select>
          </div>
          <button className="btn btn-secondary" onClick={loadDashboard} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </header>

      {error && <div className="error-box">{error}</div>}

      {/* Required dashboard cards: current weather, prediction, and advice. */}
      <section className="grid grid-3">
        <StatCard label="Current Temperature" value={data?.temperature ?? "—"} unit="°C" icon="🌡" />
        <StatCard label="Humidity" value={data?.humidity ?? "—"} unit="%" icon="💧" />
        <StatCard label="Wind Speed" value={data?.wind_speed ?? "—"} unit=" m/s" icon="🌬" />
        <StatCard label="Precipitation" value={data?.precipitation ?? "—"} unit=" mm" icon="🌧" />
        <StatCard
          label="Predicted Solar Irradiance"
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

      {/* Metadata section only appears after the first successful API response. */}
      {data && (
        <section className="grid grid-2" style={{ marginTop: 20 }}>
          <div className="card">
            <h3 style={{ marginBottom: 8 }}>Last Updated</h3>
            <p style={{ color: "var(--text-muted)" }}>
              {new Date(data.timestamp).toLocaleString()} — {data.city}
            </p>
            <p style={{ color: "var(--text-muted)", marginTop: 8 }}>
              Total predictions stored: {data.total_predictions}
            </p>
          </div>
        </section>
      )}

      {/* Historical analytics: city averages and latest saved predictions. */}
      <section className="grid grid-2" style={{ marginTop: 20 }}>
        <div className="card chart-card">
          <h3 style={{ marginBottom: 16 }}>Average Prediction by City</h3>
          {chartData.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="city" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Bar dataKey="prediction" fill="#f59e0b" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-box">No historical data yet.</div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 16 }}>Latest Predictions</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>City</th>
                  <th>Time</th>
                  <th>Prediction</th>
                  <th>Temp</th>
                </tr>
              </thead>
              <tbody>
                {(data?.latest_predictions || []).map((item) => (
                  <tr key={`${item.city}-${item.timestamp}`}>
                    <td>{item.city}</td>
                    <td>{new Date(item.timestamp).toLocaleString()}</td>
                    <td>{item.prediction} W/m²</td>
                    <td>{item.temperature}°C</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
