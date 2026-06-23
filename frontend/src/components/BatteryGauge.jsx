/**
 * Battery State of Charge gauge (FR-8).
 */
export default function BatteryGauge({
  socPct,
  minPct = 20,
  maxPct = 95,
  currentHour = null,
  batteryCapacityKwh = null,
}) {
  const clamped = Math.max(0, Math.min(100, socPct ?? 0));
  const level =
    clamped < minPct ? "critical" : clamped < 40 ? "warning" : clamped > maxPct ? "full" : "normal";

  return (
    <div className="card battery-gauge">
      <div className="battery-gauge-header">
        <h3>Battery SoC</h3>
        <span className={`battery-gauge-level battery-gauge-level--${level}`}>
          {clamped}%
        </span>
      </div>
      <div className="battery-gauge-track">
        <div className="battery-gauge-min" style={{ left: `${minPct}%` }} title={`Min ${minPct}%`} />
        <div className="battery-gauge-max" style={{ left: `${maxPct}%` }} title={`Max ${maxPct}%`} />
        <div
          className={`battery-gauge-fill battery-gauge-fill--${level}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
      <p className="battery-gauge-caption">
        {currentHour ? `Current hour (${currentHour})` : "Current hour"}
        {batteryCapacityKwh != null ? ` · ${batteryCapacityKwh} kWh battery` : ""}
        {" · "}
        Operating limits: {minPct}% min · {maxPct}% max (FR-6)
      </p>
    </div>
  );
}
