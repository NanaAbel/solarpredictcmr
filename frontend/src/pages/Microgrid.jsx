/**
 * Microgrid Optimization — simulation with irradiance-based recommendations.
 */
import { useState } from "react";
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
import { api } from "../api/client";
import RecommendationBadge from "../components/RecommendationBadge";
import StatCard from "../components/StatCard";

export default function Microgrid() {
  const [city, setCity] = useState("douala");
  const [batteryCapacity, setBatteryCapacity] = useState(20);
  const [dailyLoad, setDailyLoad] = useState(35);
  const [panelArea, setPanelArea] = useState(12);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const optimize = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.optimizeMicrogrid({
        city,
        battery_capacity_kwh: Number(batteryCapacity),
        daily_load_kwh: Number(dailyLoad),
        panel_area_m2: Number(panelArea),
        panel_efficiency: 0.18,
        hours: 24,
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData =
    result?.schedule?.map((item) => ({
      hour: new Date(item.datetime).toLocaleTimeString([], { hour: "2-digit" }),
      solar: item.solar_generation_kwh,
      load: item.load_kwh,
      import: item.grid_import_kwh,
      export: item.grid_export_kwh,
    })) || [];

  return (
    <div>
      <header className="page-header">
        <h2>Microgrid Optimization</h2>
        <p>Optimize battery and grid usage based on predicted solar irradiance.</p>
      </header>

      <div className="card">
        <div className="toolbar">
          <div className="field">
            <label>City</label>
            <select value={city} onChange={(e) => setCity(e.target.value)}>
              <option value="douala">Douala</option>
              <option value="maroua">Maroua</option>
            </select>
          </div>
          <div className="field">
            <label>Battery Capacity (kWh)</label>
            <input type="number" min="1" value={batteryCapacity} onChange={(e) => setBatteryCapacity(e.target.value)} />
          </div>
          <div className="field">
            <label>Daily Load (kWh)</label>
            <input type="number" min="1" value={dailyLoad} onChange={(e) => setDailyLoad(e.target.value)} />
          </div>
          <div className="field">
            <label>Panel Area (m²)</label>
            <input type="number" min="1" value={panelArea} onChange={(e) => setPanelArea(e.target.value)} />
          </div>
          <button className="btn" onClick={optimize} disabled={loading}>
            {loading ? "Optimizing..." : "Optimize Microgrid"}
          </button>
        </div>

        {error && <div className="error-box">{error}</div>}

        {result && (
          <>
            <RecommendationBadge
              status={result.current_microgrid_status}
              recommendation={result.current_microgrid_recommendation}
              level={
                result.current_microgrid_status.includes("High")
                  ? "high"
                  : result.current_microgrid_status.includes("Moderate")
                    ? "moderate"
                    : "low"
              }
            />

            <section className="grid grid-4" style={{ margin: "20px 0" }}>
              <StatCard label="Predicted Solar" value={result.predicted_solar_kwh} unit=" kWh" />
              <StatCard label="Grid Import" value={result.grid_import_kwh} unit=" kWh" />
              <StatCard label="Grid Export" value={result.grid_export_kwh} unit=" kWh" />
              <StatCard label="Self-Sufficiency" value={result.self_sufficiency_pct} unit="%" />
            </section>

            <div className="card chart-card">
              <h3 style={{ marginBottom: 16 }}>Hourly Energy Balance</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="hour" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="solar" fill="#f59e0b" name="Solar Gen" />
                  <Bar dataKey="load" fill="#38bdf8" name="Load" />
                  <Bar dataKey="import" fill="#ef4444" name="Grid Import" />
                  <Bar dataKey="export" fill="#22c55e" name="Grid Export" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="table-wrap" style={{ marginTop: 20 }}>
              <table>
                <thead>
                  <tr>
                    <th>Hour</th>
                    <th>Prediction</th>
                    <th>Status</th>
                    <th>Recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {result.schedule.slice(0, 12).map((row) => (
                    <tr key={row.datetime}>
                      <td>{new Date(row.datetime).toLocaleTimeString()}</td>
                      <td>{row.prediction} W/m²</td>
                      <td>{row.microgrid_status}</td>
                      <td>{row.microgrid_recommendation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
