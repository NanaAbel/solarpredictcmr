/**
 * Reusable dashboard metric card.
 */
export default function StatCard({ label, value, unit = "", icon, variant = "default" }) {
  return (
    <div className={`card stat-card stat-card--${variant}`}>
      <div className="stat-card-header">
        {icon && <span className="stat-icon">{icon}</span>}
        <h3>{label}</h3>
      </div>
      <strong>
        {value}
        {unit && <span className="stat-unit">{unit}</span>}
      </strong>
    </div>
  );
}
