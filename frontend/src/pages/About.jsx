/**
 * About page — project documentation for the Final Year Project.
 * Static content describing the system, tech stack, and prediction workflow.
 */
export default function About() {
  return (
    <div>
      <header className="page-header">
        <h2>About SolarPredict</h2>
        <p>
          Final Year Project: Solar Energy Forecasting and Microgrid Optimization
          System for Cameroon.
        </p>
      </header>

      <section className="grid grid-2">
        {/* Project purpose and scope */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Project Overview</h3>
          <p style={{ lineHeight: 1.7 }}>
            SolarPredict forecasts hourly solar irradiance for Douala and Maroua
            using weather data from the Open-Meteo API and an XGBoost Model II
            pipeline trained without solar leakage features. The platform also
            supports microgrid optimization using predicted generation, battery
            storage, and load profiles.
          </p>
        </div>

        {/* Technologies used in this application */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Tech Stack</h3>
          <ul style={{ color: "var(--text-muted)", lineHeight: 1.9 }}>
            <li>Frontend: React + Vite + Recharts</li>
            <li>Backend: FastAPI</li>
            <li>Machine Learning: XGBoost (Model II)</li>
            <li>Database: SQLite</li>
            <li>Weather API: Open-Meteo</li>
          </ul>
        </div>

        {/* End-to-end prediction pipeline steps */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Prediction Workflow</h3>
          <ol style={{ color: "var(--text-muted)", lineHeight: 1.9, paddingLeft: 18 }}>
            <li>User selects Douala or Maroua.</li>
            <li>FastAPI fetches hourly weather from Open-Meteo.</li>
            <li>Backend extracts T2M, RH2M, WS10M, and PRECTOTCORR.</li>
            <li>Model II features are generated automatically.</li>
            <li>XGBoost predicts ALLSKY_SFC_SW_DWN irradiance.</li>
            <li>Results are stored in SQLite and shown in the dashboard.</li>
          </ol>
        </div>

        {/* Microgrid recommendation rules */}
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Microgrid Rules</h3>
          <ul style={{ color: "var(--text-muted)", lineHeight: 1.9 }}>
            <li>&gt; 700 W/m² — High Solar Energy: charge batteries, prioritize solar</li>
            <li>400–700 W/m² — Moderate: hybrid operation mode</li>
            <li>&lt; 400 W/m² — Low: use battery reserves or grid support</li>
          </ul>
        </div>
      </section>
    </div>
  );
}
