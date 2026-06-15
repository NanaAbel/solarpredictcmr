# SolarPredict — Solar Energy Forecasting & Microgrid Optimization

Final Year Project for predicting solar irradiance in **Douala** and **Maroua** (Cameroon) using **XGBoost Model II**, **Open-Meteo** weather data, and rule-based **microgrid recommendations**.

## Folder Structure

```
SolarPredict/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI routes
│   │   ├── config.py               # Cities, model paths, features
│   │   ├── database.py             # SQLite (predictions table)
│   │   ├── features.py             # Model II feature engineering
│   │   ├── weather.py              # Open-Meteo API client
│   │   ├── model_loader.py         # XGBoost .pkl loader
│   │   ├── microgrid.py            # Battery/grid simulation
│   │   ├── schemas.py              # Pydantic models
│   │   └── services/
│   │       └── microgrid_recommendation.py  # Irradiance rules
│   ├── requirements.txt
│   └── solar_predict.db            # SQLite database (auto-created)
├── frontend/
│   ├── src/
│   │   ├── api/client.js           # API integration
│   │   ├── components/
│   │   │   ├── Layout.jsx          # Sidebar shell
│   │   │   ├── StatCard.jsx        # Reusable metric card
│   │   │   └── RecommendationBadge.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Live weather + recommendation cards
│   │   │   ├── Prediction.jsx      # Hourly forecast
│   │   │   ├── History.jsx         # SQLite history
│   │   │   ├── Microgrid.jsx       # Optimization
│   │   │   └── About.jsx
│   │   └── styles/index.css
│   ├── package.json
│   └── vite.config.js
├── Model/
│   ├── douala_xgb_model_ii.pkl
│   └── maroua_xgb_model_ii.pkl
└── Data/                           # Training datasets
```

## Database Schema

**Table: `predictions`**

| Column        | Type    | Description                    |
|---------------|---------|--------------------------------|
| id            | INTEGER | Primary key                    |
| city          | TEXT    | douala or maroua               |
| temperature   | REAL    | °C (T2M)                       |
| humidity      | REAL    | % (RH2M)                       |
| wind_speed    | REAL    | m/s (WS10M)                    |
| precipitation | REAL    | mm (PRECTOTCORR)               |
| prediction    | REAL    | Solar irradiance W/m²          |
| timestamp     | TEXT    | ISO datetime of forecast hour  |

## Microgrid Recommendation Rules

| Prediction (W/m²) | Status                 | Recommendation                              |
|-------------------|------------------------|---------------------------------------------|
| > 700             | High Solar Energy      | Charge batteries and prioritize solar generation |
| 400 – 700         | Moderate Solar Energy  | Hybrid operation mode                       |
| < 400             | Low Solar Energy       | Use battery reserves or grid support        |

## API Endpoints

| Method | Endpoint                      | Description                          |
|--------|-------------------------------|--------------------------------------|
| GET    | `/api/health`                 | Health check                         |
| GET    | `/api/cities`                 | Supported cities                     |
| GET    | `/api/dashboard?city=douala`  | Live dashboard cards                 |
| POST   | `/api/predict`                | Hourly irradiance forecast           |
| GET    | `/api/history`                | Prediction history from SQLite       |
| GET    | `/api/microgrid/recommendation?prediction=500` | Rule lookup           |
| POST   | `/api/microgrid/optimize`     | Full microgrid simulation            |

## How to Run

### 1. Backend (FastAPI)

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 2. Frontend (React + Vite)

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

> If `npm` is not found, add Node.js to PATH: `C:\Program Files\nodejs`

### 3. Usage Flow

1. Open the **Dashboard** — see live temperature, humidity, wind, rain, prediction, and microgrid recommendation.
2. Go to **Prediction** — run a multi-hour forecast for Douala or Maroua.
3. View **History** — all saved SQLite records.
4. Use **Microgrid** — simulate battery/grid operation with hourly recommendations.

## Tech Stack

- **Frontend:** React, Vite, Recharts
- **Backend:** FastAPI, httpx, joblib, XGBoost
- **Database:** SQLite
- **Weather:** Open-Meteo API
- **ML:** XGBoost Model II (21 features, no solar leakage)
