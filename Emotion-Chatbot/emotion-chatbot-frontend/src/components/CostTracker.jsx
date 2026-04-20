/**
 * CostTracker: Displays API usage and cost information (Stage 5)
 */

import { Wallet, AlertTriangle, Info } from 'lucide-react';

function CostTracker({ costData, sessionId }) {
  if (!costData) {
    return null;
  }

  const {
    current_cost = 0,
    max_cost = 100,
    usage_percent = 0,
    utterance_count = 0,
    is_over_limit = false,
  } = costData;

  const getUsageColor = () => {
    if (is_over_limit) return '#dc2626'; // Red
    if (usage_percent >= 75) return '#ea580c'; // Orange
    if (usage_percent >= 50) return '#eab308'; // Yellow
    return '#16a34a'; // Green
  };

  const getUsageLevel = () => {
    if (is_over_limit) return 'Over limit';
    if (usage_percent >= 75) return 'High usage';
    if (usage_percent >= 50) return 'Moderate usage';
    return 'Low usage';
  };

  return (
    <div className="cost-tracker-widget">
      <div className="cost-header">
        <span className="cost-title"><Wallet size={14} aria-hidden="true" /> API Usage</span>
        <span className="cost-level" style={{ color: getUsageColor() }}>
          {getUsageLevel()}
        </span>
      </div>

      <div className="cost-bar-container">
        <div className="cost-bar-background">
          <div
            className="cost-bar-fill"
            style={{
              width: `${Math.min(usage_percent, 100)}%`,
              backgroundColor: getUsageColor(),
            }}
          />
        </div>
        <span className="cost-bar-label">{Math.round(usage_percent)}%</span>
      </div>

      <div className="cost-details">
        <div className="cost-detail-row">
          <span className="cost-detail-label">Current cost:</span>
          <span className="cost-detail-value">{current_cost.toFixed(2)} units</span>
        </div>
        <div className="cost-detail-row">
          <span className="cost-detail-label">Max budget:</span>
          <span className="cost-detail-value">{max_cost.toFixed(2)} units</span>
        </div>
        <div className="cost-detail-row">
          <span className="cost-detail-label">Utterances:</span>
          <span className="cost-detail-value">{utterance_count}</span>
        </div>
      </div>

      {is_over_limit && (
        <div className="cost-warning">
          <p><AlertTriangle size={13} aria-hidden="true" /> Cost limit exceeded. Further requests may be throttled.</p>
        </div>
      )}

      {usage_percent >= 75 && !is_over_limit && (
        <div className="cost-caution">
          <p><Info size={13} aria-hidden="true" /> You're using {Math.round(usage_percent)}% of your budget. Consider using Conservative mode.</p>
        </div>
      )}
    </div>
  );
}

export default CostTracker;
