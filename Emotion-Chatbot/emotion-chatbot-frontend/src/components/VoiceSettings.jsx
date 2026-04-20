/**
 * VoiceSettings: Configuration panel for voice optimization (Stage 5)
 * Allows users to adjust silence timeout, cost tracking, and other parameters
 */

import { X, Turtle, Gauge, Rocket, Wallet } from 'lucide-react';

function VoiceSettings({ settings, onSettingsChange, onClose }) {
  const handleSilenceChange = (ms) => {
    const bounded = Math.max(700, Math.min(1200, parseInt(ms) || 1000));
    onSettingsChange({
      ...settings,
      silenceTimeoutMs: bounded,
    });
  };

  const handlePresetChange = (preset) => {
    const presets = {
      conservative: { silenceTimeoutMs: 1200 },
      balanced: { silenceTimeoutMs: 1000 },
      aggressive: { silenceTimeoutMs: 700 },
    };
    if (presets[preset]) {
      onSettingsChange({
        ...settings,
        ...presets[preset],
        preset,
      });
    }
  };

  return (
    <div className="voice-settings-panel">
      <div className="settings-header">
        <h3>Voice Settings (Stage 5)</h3>
        <button
          type="button"
          className="settings-close"
          onClick={onClose}
          aria-label="Close settings"
        >
          <X size={16} aria-hidden="true" />
        </button>
      </div>

      <div className="settings-section">
        <label className="settings-label">
          <span>Silence Detection Timeout (ms)</span>
          <span className="settings-hint">When to finalize utterance after silence</span>
        </label>
        <div className="settings-control">
          <input
            type="range"
            min="700"
            max="1200"
            step="50"
            value={settings.silenceTimeoutMs || 1000}
            onChange={(e) => handleSilenceChange(e.target.value)}
            className="settings-slider"
          />
          <span className="settings-value">{settings.silenceTimeoutMs || 1000}ms</span>
        </div>
        <div className="settings-presets">
          <button
            type="button"
            className={`preset-button ${settings.preset === 'conservative' ? 'active' : ''}`}
            onClick={() => handlePresetChange('conservative')}
            title="Slower, more accurate (1200ms)"
          >
            <Turtle size={14} aria-hidden="true" /> Conservative (1200ms)
          </button>
          <button
            type="button"
            className={`preset-button ${settings.preset === 'balanced' || !settings.preset ? 'active' : ''}`}
            onClick={() => handlePresetChange('balanced')}
            title="Default balance (1000ms)"
          >
            <Gauge size={14} aria-hidden="true" /> Balanced (1000ms)
          </button>
          <button
            type="button"
            className={`preset-button ${settings.preset === 'aggressive' ? 'active' : ''}`}
            onClick={() => handlePresetChange('aggressive')}
            title="Faster, more responsive (700ms)"
          >
            <Rocket size={14} aria-hidden="true" /> Aggressive (700ms)
          </button>
        </div>
      </div>

      <div className="settings-section">
        <div className="settings-info">
          <h4>What this does:</h4>
          <ul>
            <li><strong>Conservative (1200ms):</strong> Waits longer for natural speech pauses. Better accuracy, slower response.</li>
            <li><strong>Balanced (1000ms):</strong> Default setting. Good mix of speed and accuracy.</li>
            <li><strong>Aggressive (700ms):</strong> Responds faster to breaks in speech. More API calls, quicker feedback.</li>
          </ul>
        </div>
      </div>

      <div className="settings-section">
        <div className="settings-info info-cost">
          <h4><Wallet size={14} aria-hidden="true" /> Cost Optimization Tips:</h4>
          <ul>
            <li>Use Conservative mode to reduce API calls</li>
            <li>Let full sentences finish before pausing</li>
            <li>Avoid speaking very quickly (causes premature finalization)</li>
            <li>Current setting: ~{Math.round((1200 / (settings.silenceTimeoutMs || 1000)) * 100)}% of max calls</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default VoiceSettings;
