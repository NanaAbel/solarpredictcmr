/**
 * API client for communicating with the FastAPI backend.
 */
const API_BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch {
    throw new Error(
      "Cannot reach the backend. Start it first: cd backend && python -m uvicorn app.main:app --reload --port 8000"
    );
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = error.detail;
    let message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : response.statusText;

    if (response.status >= 500 && message === "Internal Server Error") {
      message =
        "Backend unavailable. Make sure FastAPI is running on port 8000, then refresh this page.";
    }

    throw new Error(message || "Request failed");
  }

  return response.json();
}

export const api = {
  health: () => request("/health"),
  cities: () => request("/cities"),

  /** Live dashboard cards + microgrid recommendation. */
  dashboard: (city = "douala") => request(`/dashboard?city=${city}`),

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
};
