/**
 * Prediction page — hourly forecast with microgrid recommendations.
 */
import { useState } from "react";
import {
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
import RecommendationBadge from "../components/RecommendationBadge";

export default function Prediction() {
  // Form state sent to POST /api/predict.
  const [city, setCity] = useState("douala");
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const runPrediction = async () => {
    // Trigger the backend prediction pipeline and store the returned forecast.
    setLoading(true);
    setError("");
    try {
      const data = await api.predict(city, Number(hours));
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Transform prediction rows into chart points with readable hour labels.
  const chartData =
    result?.predictions?.map((item) => ({
      time: new Date(item.datetime).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      prediction: item.prediction,
    })) || [];

  // The first forecast hour drives the summary recommendation badge.
  const current = result?.predictions?.[0];

  return (
    <div>
      <header className="page-header">
        <h2>Solar Prediction</h2>
        <p>Fetch Open-Meteo weather, engineer Model II features, and predict irradiance.</p>
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
            <label>Forecast Hours</label>
            <input
              type="number"
              min="1"
              max="168"
              value={hours}
              onChange={(e) => setHours(e.target.value)}
            />
          </div>
          <button className="btn" onClick={runPrediction} disabled={loading}>
            {loading ? "Predicting..." : "Run Prediction"}
          </button>
        </div>

        {error && <div className="error-box">{error}</div>}

        {/* Show the current microgrid advice after prediction succeeds. */}
        {current && (
          <div style={{ marginBottom: 20 }}>
            <RecommendationBadge
              status={current.microgrid.status}
              recommendation={current.microgrid.recommendation}
              level={current.microgrid.level}
            />
          </div>
        )}

        {/* Forecast chart and table appear only after a successful response. */}
        {result && (
          <>
            <div className="card chart-card" style={{ marginBottom: 20 }}>
              <h3 style={{ marginBottom: 16 }}>Predicted Solar Irradiance</h3>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="time" stroke="#94a3b8" minTickGap={24} />
                  <YAxis stroke="#94a3b8" label={{ value: "W/m²", angle: -90, position: "insideLeft", fill: "#94a3b8" }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="prediction"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    dot={false}
                    name="XGBoost prediction"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Prediction (W/m²)</th>
                    <th>Temp (°C)</th>
                    <th>Humidity (%)</th>
                    <th>Wind (m/s)</th>
                    <th>Rain (mm)</th>
                    <th>Microgrid Status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.predictions.slice(0, 12).map((item) => (
                    <tr key={item.datetime}>
                      <td>{new Date(item.datetime).toLocaleString()}</td>
                      <td>{item.prediction}</td>
                      <td>{item.weather.temperature}</td>
                      <td>{item.weather.humidity}</td>
                      <td>{item.weather.wind_speed}</td>
                      <td>{item.weather.precipitation}</td>
                      <td>{item.microgrid.status}</td>
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
