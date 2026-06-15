/**
 * Prediction History — SQLite records with new schema columns.
 */
import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function History() {
  const [city, setCity] = useState("");
  const [records, setRecords] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.history(city || undefined, 100);
      setRecords(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [city]);

  return (
    <div>
      <header className="page-header">
        <h2>Prediction History</h2>
        <p>Stored predictions from SQLite (temperature, humidity, wind, rain, prediction).</p>
      </header>

      <div className="card">
        <div className="toolbar">
          <div className="field">
            <label>Filter by City</label>
            <select value={city} onChange={(e) => setCity(e.target.value)}>
              <option value="">All Cities</option>
              <option value="douala">Douala</option>
              <option value="maroua">Maroua</option>
            </select>
          </div>
          <button className="btn btn-secondary" onClick={loadHistory}>
            Refresh
          </button>
        </div>

        {error && <div className="error-box">{error}</div>}
        {loading && <div className="empty-box">Loading history...</div>}

        {!loading && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>City</th>
                  <th>Temperature</th>
                  <th>Humidity</th>
                  <th>Wind Speed</th>
                  <th>Precipitation</th>
                  <th>Prediction</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {records.map((row) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>{row.city}</td>
                    <td>{row.temperature}°C</td>
                    <td>{row.humidity}%</td>
                    <td>{row.wind_speed} m/s</td>
                    <td>{row.precipitation} mm</td>
                    <td>{row.prediction} W/m²</td>
                    <td>{new Date(row.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && !records.length && (
          <div className="empty-box" style={{ marginTop: 12 }}>
            No prediction records found.
          </div>
        )}
      </div>
    </div>
  );
}
