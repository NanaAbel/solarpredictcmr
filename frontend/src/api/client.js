/**
 * API client for communicating with the FastAPI backend.
 */
const API_BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options = {}) {
  let response;
  try {
    // All frontend API calls pass through this single helper.
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch {
    // Network errors usually mean the FastAPI server is not running.
    throw new Error(
      "Cannot reach the backend. Start it first: cd backend && python -m uvicorn app.main:app --reload --port 8000"
    );
  }

  if (!response.ok) {
    // FastAPI errors can be strings or validation arrays; normalize both.
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = error.detail;
    let message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : response.statusText;

    if (response.status >= 500 && message === "Internal Server Error") {
      // Replace generic server errors with an action-oriented message.
      message =
        "Backend unavailable. Make sure FastAPI is running on port 8000, then refresh this page.";
    }

    throw new Error(message || "Request failed");
  }

  return response.json();
}

export const api = {
  // Simple API health and city metadata.
  health: () => request("/health"),
  cities: () => request("/cities"),

  /** Live dashboard cards + microgrid recommendation. */
  dashboard: (city = "douala", microgridSettings = null) => {
    const params = new URLSearchParams({ city });
    if (microgridSettings) {
      params.set("battery_capacity_kwh", String(microgridSettings.battery_capacity_kwh));
      params.set("daily_load_kwh", String(microgridSettings.daily_load_kwh));
      params.set("panel_area_m2", String(microgridSettings.panel_area_m2));
      params.set("panel_efficiency", String(microgridSettings.panel_efficiency));
    }
    return request(`/dashboard?${params}`);
  },

  /** Run solar irradiance prediction for a city. */
  predict: (city, hours = 24) =>
    request("/predict", {
      method: "POST",
      body: JSON.stringify({ city, hours }),
    }),

  /** Retrieve stored prediction history. */
  history: (city, limit = 100) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (city) params.set("city", city);
    return request(`/history?${params}`);
  },

  /** Rule-based microgrid recommendation for an irradiance value. */
  microgridRecommendation: (prediction) =>
    request(`/microgrid/recommendation?prediction=${prediction}`),

  /** Run full microgrid optimization simulation. */
  optimizeMicrogrid: (payload) =>
    request("/microgrid/optimize", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** FR-9 seasonal performance report. */
  seasonalReport: (city = "douala") => request(`/reports/seasonal?city=${city}`),
};

/** FR-9: trigger CSV download in the browser. */
export async function downloadSeasonalCsv(city = "douala") {
  const response = await fetch(`${API_BASE}/reports/seasonal/csv?city=${city}`);
  if (!response.ok) {
    throw new Error("CSV export failed");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `solarpredict_${city}_seasonal_report.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

/** Weekly solar + microgrid PDF download. */
export async function downloadWeeklyPdf(city = "douala", microgridSettings = null) {
  const params = new URLSearchParams({ city });
  if (microgridSettings) {
    params.set("battery_capacity_kwh", String(microgridSettings.battery_capacity_kwh));
    params.set("daily_load_kwh", String(microgridSettings.daily_load_kwh));
    params.set("panel_area_m2", String(microgridSettings.panel_area_m2));
    params.set("panel_efficiency", String(microgridSettings.panel_efficiency));
  }
  const response = await fetch(`${API_BASE}/reports/weekly/pdf?${params}`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "PDF export failed" }));
    throw new Error(
      typeof error.detail === "string" ? error.detail : "Weekly report download failed"
    );
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `solarpredict_${city}_weekly_report.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}
