# CHAPTER FOUR

# IMPLEMENTATION, TESTING AND RESULTS

## 4.1 Introduction

This chapter presents the implementation of **SolarPredict**, a solar energy forecasting and microgrid optimization system for Douala and Maroua in Cameroon. The system was implemented as a full-stack web application made up of a Python FastAPI backend, a React/Vite frontend, SQLite storage, trained XGBoost machine learning models, and live weather data from Open-Meteo.

The implementation follows the system design by separating the project into independent layers. The frontend handles user interaction and visualization, the backend exposes prediction and microgrid APIs, the machine learning layer performs solar irradiance prediction, and the database stores prediction history for later analysis and reporting.

**Screenshot to add here**

Insert a screenshot of the project folder structure from VS Code Explorer.

Caption:

**Figure 4.1: SolarPredict project folder structure in Visual Studio Code**

Suggested screenshot area:

- Open VS Code.
- Expand `backend`, `frontend`, `Model`, `Data`, and `training`.
- Make sure files like `main.py`, `schemas.py`, `Dashboard.jsx`, `Prediction.jsx`, `Microgrid.jsx`, and `Reports.jsx` are visible.

## 4.2 Development Environment

The system was developed using the following tools and technologies:

| Component | Technology Used | Purpose |
|---|---|---|
| Frontend | React, Vite, Recharts | User interface, charts, dashboards, forms and reports |
| Backend | FastAPI, Uvicorn | REST API for prediction, dashboard, history, reports and microgrid optimization |
| Machine Learning | XGBoost, joblib, pandas, NumPy | Loading and running trained solar irradiance prediction models |
| Database | SQLite | Storing prediction history |
| Weather API | Open-Meteo | Fetching live hourly weather forecasts |
| Reporting | ReportLab | Generating weekly PDF reports |
| Deployment | Vercel configuration | Frontend/backend deployment configuration |
| IDE | Visual Studio Code | Code development and project management |

The backend dependencies are stored in `backend/requirements.txt`, while the frontend dependencies are stored in `frontend/package.json`.

**Screenshot to add here**

Insert a screenshot showing `backend/requirements.txt` and `frontend/package.json`.

Caption:

**Figure 4.2: Backend and frontend dependency files**

## 4.3 System Folder Structure

The project is organized into separate folders for source code, data, models, training notebooks and documentation.

```text
SolarPredict/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── schemas.py
│   │   ├── weather.py
│   │   ├── features.py
│   │   ├── model_loader.py
│   │   ├── database.py
│   │   ├── microgrid.py
│   │   └── services/
│   │       ├── alert_service.py
│   │       ├── analytics_service.py
│   │       ├── microgrid_recommendation.py
│   │       ├── report_service.py
│   │       └── weekly_report_service.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/
│   │   ├── pages/
│   │   ├── utils/
│   │   └── styles/
│   ├── package.json
│   └── vite.config.js
│
├── Model/
│   ├── douala_xgb_model_ii.pkl
│   └── maroua_xgb_model_ii.pkl
│
├── Data/
│   ├── Raw/
│   └── Processed/
│
├── training/
│   ├── Model_training_Douala_Model_II.ipynb
│   ├── Model_training_Maroua_Model_II.ipynb
│   └── model_ii_comparison_summary.csv
│
└── docs/
```

The `backend/app` folder contains all server-side logic. The `frontend/src` folder contains all user interface pages and components. The `Model` folder contains the trained XGBoost models used during prediction. The `Data` and `training` folders contain the data science process used to train and evaluate the models.

## 4.4 Backend Implementation

### 4.4.1 FastAPI Application Entry Point

The backend starts from `backend/app/main.py`. This file creates the FastAPI application, enables CORS, initializes the database, preloads the trained models and defines all API endpoints.

Important backend endpoints include:

| Endpoint | Method | Function |
|---|---|---|
| `/api/health` | GET | Checks if the backend is running |
| `/api/cities` | GET | Returns supported cities |
| `/api/dashboard` | GET | Returns enhanced dashboard data |
| `/api/dashboard/basic` | GET | Returns a lightweight dashboard response |
| `/api/predict` | POST | Runs solar irradiance prediction |
| `/api/history` | GET | Returns saved prediction history |
| `/api/microgrid/recommendation` | GET | Returns rule-based advice for one irradiance value |
| `/api/microgrid/optimize` | POST | Runs battery/grid simulation |
| `/api/reports/seasonal` | GET | Returns dry vs rainy season report |
| `/api/reports/seasonal/csv` | GET | Exports seasonal report as CSV |
| `/api/reports/weekly/pdf` | GET | Exports weekly solar and microgrid report as PDF |

The FastAPI backend is started with:

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

**Screenshot to add here**

Take a screenshot of the terminal showing Uvicorn running successfully.

Caption:

**Figure 4.3: FastAPI backend server running on port 8000**

**Screenshot to add here**

Open `http://127.0.0.1:8000/docs` and take a screenshot of the Swagger API documentation.

Caption:

**Figure 4.4: FastAPI Swagger documentation showing SolarPredict API endpoints**

### 4.4.2 Configuration Module

The `config.py` file stores project-wide constants such as model paths, supported cities, model features, microgrid limits and alert thresholds.

The two supported cities are Douala and Maroua. Each city has its own latitude, longitude, timezone and trained model file.

Key configuration values include:

- `CITIES`: stores Douala and Maroua metadata.
- `MODEL_II_FEATURES`: stores the 21 features expected by the XGBoost model.
- `TARGET`: stores the target variable, `ALLSKY_SFC_SW_DWN`.
- `BATTERY_SOC_MIN_PCT`: minimum battery state of charge, 20%.
- `BATTERY_SOC_MAX_PCT`: maximum battery state of charge, 95%.
- `ALERT_SOLAR_THRESHOLD_KWH_M2`: low solar alert threshold.
- `DEFAULT_BATTERY_CAPACITY_KWH`: default battery capacity.

**Screenshot to add here**

Take a screenshot of `backend/app/config.py` showing `CITIES`, `MODEL_II_FEATURES`, and the microgrid constants.

Caption:

**Figure 4.5: Configuration file showing supported cities, model features and microgrid constants**

### 4.4.3 API Schemas and Validation

The `schemas.py` file defines Pydantic models for request and response validation. Pydantic ensures that invalid inputs are rejected before the backend processes them.

For example, the `PredictionRequest` schema requires:

```python
city: str
hours: int = Field(default=24, ge=1, le=168)
```

This means the user must provide a city, and the number of forecast hours must be between 1 and 168.

The `MicrogridRequest` schema validates:

- battery capacity must be greater than 0,
- daily load must be greater than 0,
- panel area must be greater than 0,
- panel efficiency must be greater than 0 and less than or equal to 1.

**Screenshot to add here**

Take a screenshot of `backend/app/schemas.py` showing `PredictionRequest`, `MicrogridRequest`, `MicrogridResponse`, and `EnhancedDashboardResponse`.

Caption:

**Figure 4.6: Pydantic schemas used for request and response validation**

### 4.4.4 Weather Data Collection

The `weather.py` file connects the backend to the Open-Meteo API. It fetches hourly weather data for the selected city and prepares the raw weather values used by the model.

The weather variables collected are:

- temperature at 2 metres,
- relative humidity,
- wind speed at 10 metres,
- precipitation,
- shortwave radiation for reference comparison.

The function `fetch_hourly_weather()` returns both display weather data and machine-learning feature data. It also uses a short cache so that repeated dashboard refreshes do not unnecessarily call the external API.

**Screenshot to add here**

Take a screenshot of `backend/app/weather.py` showing the Open-Meteo request parameters and feature generation call.

Caption:

**Figure 4.7: Weather API implementation using Open-Meteo**

### 4.4.5 Feature Engineering Implementation

The file `features.py` converts weather and time data into the 21 Model II features required by the trained XGBoost model.

The feature groups are:

| Feature Group | Examples | Purpose |
|---|---|---|
| Calendar features | `YEAR`, `MO`, `DY`, `HR` | Capture time information |
| Weather features | `T2M`, `RH2M`, `PRECTOTCORR`, `WS10M` | Capture live weather conditions |
| Cyclic features | `hour_sin`, `hour_cos`, `month_sin`, `month_cos` | Represent daily and seasonal cycles |
| Binary features | `is_daytime`, `is_rainy` | Capture daylight and rainfall states |
| Transformed features | `rain_log1p`, `ws10m_log1p` | Reduce skewness in rain and wind data |
| Seasonal features | `season_dry`, `season_rainy` | Capture local climate seasons |

The function `build_model_ii_row()` creates one row of features, while `build_feature_dataframe()` converts multiple rows into a pandas DataFrame in the exact order required by the trained model.

**Screenshot to add here**

Take a screenshot of `backend/app/features.py` showing `build_model_ii_row()` and `build_feature_dataframe()`.

Caption:

**Figure 4.8: Model II feature engineering implementation**

### 4.4.6 Model Loading and Prediction

The `model_loader.py` file loads the trained XGBoost models using `joblib`. Each city uses a separate trained model:

- `douala_xgb_model_ii.pkl`
- `maroua_xgb_model_ii.pkl`

The function `get_model()` loads and caches a model in memory. The function `predict()` runs inference and clamps negative predictions to zero because solar irradiance cannot be physically negative.

**Screenshot to add here**

Take a screenshot of `backend/app/model_loader.py` and the `Model` folder showing the two XGBoost model files.

Caption:

**Figure 4.9: XGBoost model loading and city-specific model files**

### 4.4.7 Database Implementation

SQLite is used to store prediction history. The database logic is implemented in `database.py`.

The main table is `predictions`.

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| city | TEXT | City name |
| temperature | REAL | Temperature input |
| humidity | REAL | Humidity input |
| wind_speed | REAL | Wind speed input |
| precipitation | REAL | Rainfall input |
| prediction | REAL | Predicted solar irradiance |
| timestamp | TEXT | Forecast timestamp |

The database functions include:

- `init_db()`: creates or migrates the database table.
- `save_predictions()`: saves prediction results.
- `get_prediction_history()`: retrieves stored predictions.
- `get_latest_prediction()`: gets the most recent prediction.
- `get_dashboard_stats()`: computes dashboard summary statistics.

**Screenshot to add here**

Open DB Browser for SQLite or run `python backend/inspect_db.py`, then take a screenshot of the `predictions` table schema.

Caption:

**Figure 4.10: SQLite predictions table structure**

**Screenshot to add here**

Take a screenshot of the `Browse Data` tab showing saved prediction rows.

Caption:

**Figure 4.11: Stored prediction records in the SQLite database**

### 4.4.8 Microgrid Optimization

The microgrid simulation is implemented in `microgrid.py`. It converts predicted solar irradiance into available solar energy and simulates battery charging, battery discharging, grid import and grid export.

The solar energy conversion formula is:

```text
Solar Energy (kWh) = Irradiance (W/m²) × Panel Area (m²) × Panel Efficiency / 1000
```

The battery state of charge is limited between:

- minimum SoC: 20%,
- maximum SoC: 95%.

The simulation uses this logic:

1. If solar generation is greater than load, the surplus charges the battery.
2. If the battery reaches its maximum limit, remaining energy is exported to the grid.
3. If solar generation is less than load, the battery discharges.
4. If the battery reaches its minimum limit, remaining demand is imported from the grid.

**Screenshot to add here**

Take a screenshot of `backend/app/microgrid.py` showing `simulate_microgrid()` and the SoC limits logic.

Caption:

**Figure 4.12: Microgrid battery and grid simulation algorithm**

### 4.4.9 Alert System

The alert system is implemented in `alert_service.py`. It checks whether the next 6 hours of predicted solar energy are below the threshold and whether the battery state of charge is below 40%.

An alert is triggered when:

```text
6-hour solar energy < 0.5 kWh/m² AND battery SoC < 40%
```

When this condition is true, the system displays a critical alert and recommends load shedding priorities.

**Screenshot to add here**

Take a screenshot of `backend/app/services/alert_service.py`.

Caption:

**Figure 4.13: Alert service implementation for low solar and low battery conditions**

### 4.4.10 Report Generation

The reporting functionality is implemented in:

- `report_service.py`: seasonal dry vs rainy CSV reports.
- `weekly_report_service.py`: 7-day solar and microgrid PDF reports.

The weekly report uses ReportLab to generate a PDF containing:

- average GHI,
- peak GHI,
- total panel energy,
- grid import/export,
- battery use,
- self-sufficiency,
- hourly solar forecast table,
- hourly microgrid schedule table.

**Screenshot to add here**

Take a screenshot of `backend/app/services/weekly_report_service.py` showing `build_weekly_report_pdf()`.

Caption:

**Figure 4.14: Weekly PDF report generation using ReportLab**

## 4.5 Frontend Implementation

### 4.5.1 React Application Routing

The React application starts from `main.jsx` and uses `App.jsx` for routing. The pages are wrapped in a shared layout component.

The main routes are:

| Route | Page | Purpose |
|---|---|---|
| `/` | Dashboard | Shows live forecast, battery SoC, alert, metrics and seasonal analytics |
| `/prediction` | Prediction | Runs hourly solar irradiance forecasts |
| `/history` | History | Displays stored SQLite prediction records |
| `/microgrid` | Microgrid | Runs battery/grid optimization |
| `/reports` | Reports | Exports seasonal CSV and weekly PDF reports |
| `/about` | About | Describes the project |

**Screenshot to add here**

Take a screenshot of `frontend/src/App.jsx` showing the route definitions.

Caption:

**Figure 4.15: React route configuration for SolarPredict pages**

### 4.5.2 API Client

The frontend communicates with the backend through `frontend/src/api/client.js`. This file centralizes all API calls so that components do not call `fetch()` directly.

The API client contains functions for:

- dashboard data,
- prediction,
- history,
- microgrid optimization,
- seasonal report,
- CSV download,
- weekly PDF download.

**Screenshot to add here**

Take a screenshot of `frontend/src/api/client.js` showing the `api` object and download functions.

Caption:

**Figure 4.16: Frontend API client used to communicate with FastAPI**

### 4.5.3 Layout and Navigation

The `Layout.jsx` component provides the sidebar navigation. It contains links to Dashboard, Prediction, History, Microgrid, Reports and About pages. The `Outlet` component from React Router displays the active page.

**Screenshot to add here**

Run the frontend and take a screenshot showing the sidebar navigation.

Caption:

**Figure 4.17: SolarPredict sidebar navigation layout**

### 4.5.4 Dashboard Page

The Dashboard page is implemented in `Dashboard.jsx`. It provides an enhanced overview of the system.

The dashboard displays:

- current temperature,
- humidity,
- wind speed,
- precipitation,
- current GHI prediction,
- microgrid recommendation,
- alert status,
- 24-hour GHI prediction chart,
- battery state of charge gauge,
- dry vs rainy season comparison,
- model performance metrics,
- microgrid schedule.

**Screenshot to add here**

Take a full-page screenshot of the Dashboard page after data loads.

Caption:

**Figure 4.18: Enhanced dashboard showing live weather, GHI prediction and microgrid status**

**Screenshot to add here**

Take a closer screenshot of the 24-hour GHI chart and Battery SoC gauge.

Caption:

**Figure 4.19: 24-hour GHI forecast and battery state of charge gauge**

**Screenshot to add here**

Take a screenshot of the alert banner if it appears. If no critical alert appears, screenshot the normal alert status.

Caption:

**Figure 4.20: Solar and battery alert status on the dashboard**

### 4.5.5 Prediction Page

The Prediction page is implemented in `Prediction.jsx`. It allows the user to select a city and forecast duration, then request hourly solar irradiance prediction from the backend.

Input fields:

- city: Douala or Maroua,
- forecast hours: 1 to 168.

Output:

- XGBoost prediction chart,
- microgrid recommendation,
- hourly table showing prediction, temperature, humidity, wind speed, precipitation and microgrid status.

**Input screenshot to add here**

Take a screenshot before clicking **Run Prediction**, showing selected city and forecast hours.

Caption:

**Figure 4.21: Prediction input form for city and forecast duration**

**Output screenshot to add here**

Click **Run Prediction** and take a screenshot showing the chart and prediction table.

Caption:

**Figure 4.22: Prediction output showing hourly solar irradiance forecast**

### 4.5.6 History Page

The History page is implemented in `History.jsx`. It displays saved prediction records from the SQLite database. The user can filter records by city.

**Screenshot to add here**

Open the History page and take a screenshot showing saved records.

Caption:

**Figure 4.23: Prediction history retrieved from SQLite**

### 4.5.7 Microgrid Page

The Microgrid page is implemented in `Microgrid.jsx`. It allows the user to input:

- city,
- battery capacity,
- daily load,
- panel area.

The system then runs a 24-hour microgrid simulation and displays:

- predicted solar energy,
- grid import,
- grid export,
- self-sufficiency,
- battery SoC,
- hourly energy balance chart,
- microgrid schedule table.

**Input screenshot to add here**

Take a screenshot of the Microgrid page before running optimization.

Caption:

**Figure 4.24: Microgrid optimization input parameters**

**Output screenshot to add here**

Click **Optimize Microgrid** and take a screenshot of the summary cards and energy balance chart.

Caption:

**Figure 4.25: Microgrid optimization output showing energy balance**

**Output screenshot to add here**

Take a screenshot of the microgrid schedule table showing hourly SoC and recommendation.

Caption:

**Figure 4.26: Hourly microgrid schedule with battery SoC and operational status**

### 4.5.8 Reports Page

The Reports page is implemented in `Reports.jsx`. It provides two reporting features:

1. Weekly PDF report download.
2. Seasonal dry vs rainy report with CSV and chart export.

The weekly PDF report uses the current microgrid settings to generate a 7-day solar and battery/grid report. The seasonal report compares dry season and rainy season performance using stored predictions.

**Screenshot to add here**

Open the Reports page and take a screenshot showing the Weekly Report and Seasonal Report sections.

Caption:

**Figure 4.27: Reports page with weekly PDF and seasonal report options**

**Screenshot to add here**

Click **Download Weekly PDF**, open the downloaded PDF, and take a screenshot of the generated report.

Caption:

**Figure 4.28: Generated weekly solar and microgrid PDF report**

**Screenshot to add here**

Take a screenshot of the seasonal performance chart.

Caption:

**Figure 4.29: Seasonal dry versus rainy performance chart**

## 4.6 Machine Learning Model Implementation

The machine learning component uses XGBoost Model II. Model II was selected because it avoids solar leakage by excluding direct solar variables such as `ALLSKY_SFC_SW_DNI` and `ALLSKY_SFC_SW_DIFF`. Instead, it uses weather and time-based features that can be obtained from forecast data.

The model was trained and evaluated using:

- Random Forest,
- XGBoost,
- LSTM.

The final comparison showed that XGBoost had the best overall performance because it achieved the best R² and RMSE values for both Douala and Maroua.

| City | Best Model | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| Douala | XGBoost | 24.83 | 53.32 | 0.9503 |
| Maroua | XGBoost | 26.55 | 60.20 | 0.9657 |

Although Random Forest had slightly lower MAE, the difference was very small. XGBoost was selected because it produced lower RMSE and higher R², meaning it reduced larger prediction errors and explained more variation in the target variable.

**Screenshot to add here**

Open `training/model_ii_comparison_summary.csv` or the model comparison notebook and take a screenshot of the model comparison results.

Caption:

**Figure 4.30: Model II comparison results showing XGBoost as the selected model**

## 4.7 Input Specification

The main input data for the application comes from two sources: user input and Open-Meteo weather input.

### 4.7.1 User Inputs

| Module | Input | Example |
|---|---|---|
| Dashboard | City, battery capacity, daily load, panel area, panel efficiency | Douala, 20 kWh, 35 kWh/day |
| Prediction | City, forecast hours | Maroua, 24 hours |
| Microgrid | City, battery capacity, daily load, panel area | Douala, 20 kWh, 35 kWh/day, 12 m² |
| Reports | City, saved microgrid settings | Douala |

**Screenshot to add here**

Add screenshots of sample input forms:

- Prediction page form.
- Microgrid page form.
- Reports city selector.

Caption:

**Figure 4.31: Sample input forms used in SolarPredict**

### 4.7.2 Weather Inputs

The weather inputs used by the machine learning model are:

- temperature,
- relative humidity,
- precipitation,
- wind speed,
- hour,
- month,
- day,
- seasonal indicators.

These values are transformed into the 21 Model II features before prediction.

## 4.8 Output Specification

The system produces several outputs:

| Module | Output |
|---|---|
| Dashboard | Current weather, GHI prediction, alert, battery SoC, model metrics, seasonal analytics |
| Prediction | Hourly solar irradiance chart and prediction table |
| History | Stored prediction records |
| Microgrid | Solar generation, grid import/export, battery SoC, self-sufficiency |
| Reports | Seasonal CSV, chart PNG, weekly PDF report |

**Screenshot to add here**

Add screenshots of the major outputs:

- Dashboard output.
- Prediction output.
- Microgrid output.
- Reports output.
- History table.

Caption:

**Figure 4.32: Representative output screens of SolarPredict**

## 4.9 Testing

Testing was carried out to verify the backend, frontend, prediction workflow and report generation.

### 4.9.1 Backend Tests

Backend tests to perform:

| Test | Expected Result |
|---|---|
| Open `/api/health` | Returns `status: ok` and supported cities |
| Open `/api/cities` | Returns Douala and Maroua metadata |
| Run `/api/dashboard?city=douala` | Returns enhanced dashboard payload |
| Run `/api/predict` with valid city and hours | Returns hourly predictions |
| Run `/api/predict` with invalid city | Returns error message |
| Run `/api/microgrid/recommendation?prediction=500` | Returns Moderate Solar Energy |
| Run `/api/reports/seasonal?city=douala` | Returns seasonal report |
| Download `/api/reports/weekly/pdf` | Returns PDF file |

**Screenshot to add here**

Use Swagger UI to test `/api/health`, `/api/predict`, `/api/microgrid/optimize`, and `/api/reports/weekly/pdf`.

Caption:

**Figure 4.33: API testing using FastAPI Swagger UI**

### 4.9.2 Frontend Tests

Frontend tests to perform:

| Test | Expected Result |
|---|---|
| Open dashboard | Dashboard loads without error |
| Switch city | Data reloads for selected city |
| Run prediction | Chart and table appear |
| Open history | Stored records are displayed |
| Run microgrid optimization | Energy balance and SoC schedule appear |
| Download seasonal CSV | CSV file downloads |
| Download weekly PDF | PDF file downloads |

**Screenshot to add here**

Take screenshots of successful frontend tests after performing each main operation.

Caption:

**Figure 4.34: Frontend functional testing of SolarPredict modules**

### 4.9.3 Build Test

The frontend production build can be tested with:

```powershell
cd frontend
npm run build
```

Expected result:

```text
✓ built successfully
```

The backend can be syntax-checked with:

```powershell
python -m compileall -q backend/app
```

Expected result: no error output.

**Screenshot to add here**

Take a screenshot of the successful `npm run build` command and backend compile command.

Caption:

**Figure 4.35: Successful frontend and backend build verification**

## 4.10 Deployment Configuration

The project includes a `vercel.json` file for deployment. The configuration defines the frontend as a Vite application and the backend as a FastAPI service.

The frontend build command is:

```text
cd frontend && npm run build
```

The backend entry point is:

```text
backend/app/main.py
```

The model files are included through:

```json
"includeFiles": ["Model/**"]
```

This ensures that the trained XGBoost model files are available to the deployed backend.

**Screenshot to add here**

Take a screenshot of `vercel.json`.

Caption:

**Figure 4.36: Vercel deployment configuration for frontend and backend**

## 4.11 Chapter Summary

This chapter described the implementation of SolarPredict as a complete solar forecasting and microgrid decision-support system. The backend was implemented using FastAPI and includes endpoints for prediction, dashboard analytics, history, reports and microgrid optimization. The frontend was implemented using React and provides pages for dashboard visualization, prediction, history, microgrid simulation, reports and project information.

The machine learning model was implemented using XGBoost Model II, which uses weather and time-based features to predict solar irradiance. SQLite was used to store prediction history, while ReportLab was used to generate weekly PDF reports. The system also includes alert generation, seasonal comparison and battery state-of-charge simulation.

The implementation satisfies the required input and output specification by providing screenshots of sample inputs, expected outputs and representative modules of the system.

## 4.12 Screenshot Checklist

Use this checklist while preparing the final report:

- [ ] Project folder structure in VS Code.
- [ ] Backend server running in terminal.
- [ ] FastAPI Swagger UI.
- [ ] `config.py` showing cities and model features.
- [ ] `schemas.py` showing validation models.
- [ ] `weather.py` showing Open-Meteo integration.
- [ ] `features.py` showing feature engineering.
- [ ] `model_loader.py` and model files.
- [ ] SQLite database schema.
- [ ] SQLite saved prediction rows.
- [ ] `microgrid.py` battery/grid algorithm.
- [ ] Dashboard full page.
- [ ] Dashboard 24-hour GHI chart and battery gauge.
- [ ] Alert banner.
- [ ] Prediction input form.
- [ ] Prediction output chart and table.
- [ ] History table.
- [ ] Microgrid input form.
- [ ] Microgrid output cards and chart.
- [ ] Microgrid schedule table.
- [ ] Reports page.
- [ ] Generated weekly PDF report.
- [ ] Seasonal performance chart.
- [ ] Model comparison result table.
- [ ] Swagger API tests.
- [ ] Successful build/compile terminal.
- [ ] Vercel deployment configuration.

