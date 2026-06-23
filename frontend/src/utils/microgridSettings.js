/** Shared microgrid inputs — synced between Dashboard and Microgrid pages. */

export const MICROGRID_SETTINGS_KEY = "solarpredict_microgrid_settings";

export const DEFAULT_MICROGRID_SETTINGS = {
  battery_capacity_kwh: 20,
  daily_load_kwh: 35,
  panel_area_m2: 12,
  panel_efficiency: 0.18,
};

export function loadMicrogridSettings() {
  try {
    const raw = localStorage.getItem(MICROGRID_SETTINGS_KEY);
    if (!raw) return { ...DEFAULT_MICROGRID_SETTINGS };
    return { ...DEFAULT_MICROGRID_SETTINGS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_MICROGRID_SETTINGS };
  }
}

export function saveMicrogridSettings(settings) {
  const merged = { ...DEFAULT_MICROGRID_SETTINGS, ...settings };
  localStorage.setItem(MICROGRID_SETTINGS_KEY, JSON.stringify(merged));
  window.dispatchEvent(new CustomEvent("microgrid-settings-changed", { detail: merged }));
  return merged;
}

export function settingsToQueryParams(settings) {
  const params = new URLSearchParams();
  params.set("battery_capacity_kwh", String(settings.battery_capacity_kwh));
  params.set("daily_load_kwh", String(settings.daily_load_kwh));
  params.set("panel_area_m2", String(settings.panel_area_m2));
  params.set("panel_efficiency", String(settings.panel_efficiency));
  return params.toString();
}
