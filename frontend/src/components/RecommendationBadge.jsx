/**
 * Microgrid recommendation badge with color by energy level.
 */
export default function RecommendationBadge({ status, recommendation, level }) {
  // level controls the CSS color: high, moderate, or low.
  return (
    <div className={`recommendation-card recommendation-card--${level}`}>
      <div className="recommendation-status">{status}</div>
      <p className="recommendation-text">{recommendation}</p>
    </div>
  );
}
