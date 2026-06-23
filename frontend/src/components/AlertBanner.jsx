/**
 * Alert status banner (FR-7).
 */
export default function AlertBanner({ alert }) {
  if (!alert) return null;

  return (
    <div className={`alert-banner alert-banner--${alert.severity}`}>
      <div className="alert-banner-title">
        {alert.active ? "⚠ Active Alert" : alert.severity === "warning" ? "Watch" : "Alert Status"}
      </div>
      <p>{alert.message}</p>
      <div className="alert-banner-meta">
        <span>6 h solar: {alert.solar_6h_kwh_m2} kWh/m²</span>
        <span>Battery: {alert.battery_soc_pct}%</span>
      </div>
      {alert.load_shedding_priority?.length > 0 && (
        <div className="alert-banner-priority">
          <strong>Load shedding priority:</strong>
          <ol>
            {alert.load_shedding_priority.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
