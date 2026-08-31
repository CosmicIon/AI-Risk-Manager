'use client';

import { Sliders, Play, Pause, Crosshair } from 'lucide-react';

interface SimConfig {
  n_customers: number;
  n_terminals: number;
  nb_days: number;
  radius: number;
  scenario_1_enabled: boolean;
  scenario_2_enabled: boolean;
  scenario_3_enabled: boolean;
}

interface Props {
  config: SimConfig;
  onConfigChange: (config: SimConfig) => void;
  onGenerate: () => void;
  onStreamToggle: () => void;
  isGenerating: boolean;
  isStreaming: boolean;
  hasData: boolean;
}

export default function SimulationControls({
  config,
  onConfigChange,
  onGenerate,
  onStreamToggle,
  isGenerating,
  isStreaming,
  hasData,
}: Props) {
  const update = (key: keyof SimConfig, value: number | boolean) => {
    onConfigChange({ ...config, [key]: value });
  };

  return (
    <div className="card" id="sim-controls-card" style={{ padding: 'var(--spacing-5)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sliders size={16} style={{ color: 'var(--text-muted)' }} />
          <span className="card-title">Configuration</span>
        </div>
      </div>

      {/* Parameter Sliders */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-5)', marginBottom: 'var(--spacing-5)' }}>
        {/* Customers */}
        <div className="sim-param-group">
          <div className="sim-param-label">
            <span>Customers (N<sub>c</sub>)</span>
            <span className="sim-param-value">{config.n_customers.toLocaleString()}</span>
          </div>
          <input
            id="sim-slider-customers"
            type="range"
            className="sim-slider"
            min={1000}
            max={20000}
            step={500}
            value={config.n_customers}
            onChange={(e) => update('n_customers', parseInt(e.target.value))}
          />
        </div>

        {/* Terminals */}
        <div className="sim-param-group">
          <div className="sim-param-label">
            <span>Terminals (N<sub>t</sub>)</span>
            <span className="sim-param-value">{config.n_terminals.toLocaleString()}</span>
          </div>
          <input
            id="sim-slider-terminals"
            type="range"
            className="sim-slider"
            min={100}
            max={2000}
            step={50}
            value={config.n_terminals}
            onChange={(e) => update('n_terminals', parseInt(e.target.value))}
          />
        </div>

        {/* Days */}
        <div className="sim-param-group">
          <div className="sim-param-label">
            <span>Timespan (Days)</span>
            <span className="sim-param-value">{config.nb_days}</span>
          </div>
          <input
            id="sim-slider-days"
            type="range"
            className="sim-slider"
            min={7}
            max={180}
            step={1}
            value={config.nb_days}
            onChange={(e) => update('nb_days', parseInt(e.target.value))}
          />
        </div>

        {/* Radius */}
        <div className="sim-param-group">
          <div className="sim-param-label">
            <span>Radius (r)</span>
            <span className="sim-param-value">{config.radius.toFixed(1)} km</span>
          </div>
          <input
            id="sim-slider-radius"
            type="range"
            className="sim-slider"
            min={1.0}
            max={15.0}
            step={0.5}
            value={config.radius}
            onChange={(e) => update('radius', parseFloat(e.target.value))}
          />
        </div>
      </div>

      {/* Scenario Toggles + Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--spacing-3)' }}>
        <div className="sim-scenario-toggles">
          <button
            id="sim-toggle-s1"
            className={`sim-toggle ${config.scenario_1_enabled ? 'active' : ''}`}
            onClick={() => update('scenario_1_enabled', !config.scenario_1_enabled)}
          >
            <span className="sim-toggle-dot s1" />
            S1 — High Amount
          </button>
          <button
            id="sim-toggle-s2"
            className={`sim-toggle ${config.scenario_2_enabled ? 'active' : ''}`}
            onClick={() => update('scenario_2_enabled', !config.scenario_2_enabled)}
          >
            <span className="sim-toggle-dot s2" />
            S2 — POS Skimming
          </button>
          <button
            id="sim-toggle-s3"
            className={`sim-toggle ${config.scenario_3_enabled ? 'active' : ''}`}
            onClick={() => update('scenario_3_enabled', !config.scenario_3_enabled)}
          >
            <span className="sim-toggle-dot s3" />
            S3 — Account Takeover
          </button>
        </div>

        <div className="sim-actions">
          <button
            id="sim-btn-generate"
            className="btn btn-generate"
            onClick={onGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <span className="sim-spinner" />
                Generating…
              </>
            ) : (
              <>
                <Crosshair size={15} />
                Generate Dataset
              </>
            )}
          </button>

          <button
            id="sim-btn-stream"
            className={`btn btn-outline btn-stream ${isStreaming ? 'active' : ''}`}
            onClick={onStreamToggle}
            disabled={!hasData}
          >
            {isStreaming ? (
              <>
                <Pause size={15} />
                Pause Stream
              </>
            ) : (
              <>
                <Play size={15} />
                Start Live Stream
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
