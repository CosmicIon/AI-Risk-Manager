'use client';

import { useState, useCallback } from 'react';
import { FlaskConical, Zap, Radio } from 'lucide-react';
import SimulationControls from './SimulationControls';
import SpatialMap from './SpatialMap';
import LiveStreamTable from './LiveStreamTable';
import SimulationAnalytics from './SimulationAnalytics';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface SimulationStats {
  total_transactions: number;
  total_customers: number;
  total_terminals: number;
  nb_days: number;
  fraud_count: number;
  fraud_rate: number;
  scenario_breakdown: {
    scenario_0_legitimate: number;
    scenario_1_high_amount: number;
    scenario_2_compromised_terminal: number;
    scenario_3_account_takeover: number;
  };
  total_loss_inr: number;
  train_count: number;
  holdout_count: number;
  avg_amount: number;
  median_amount: number;
  generated_at: string;
  customer_coordinates: Array<{ x: number; y: number; customer_id: string }>;
  terminal_coordinates: Array<{ x: number; y: number; terminal_id: string; mcc: string }>;
  compromised_terminals: string[];
  compromised_customers: string[];
}

interface SimConfig {
  n_customers: number;
  n_terminals: number;
  nb_days: number;
  radius: number;
  scenario_1_enabled: boolean;
  scenario_2_enabled: boolean;
  scenario_3_enabled: boolean;
}

export interface StreamTransaction {
  transaction_id: string;
  tx_datetime: string;
  customer_id: string;
  terminal_id: string;
  tx_amount: number;
  mcc: string;
  payment_method: string;
  device_fingerprint: string;
  ip_address: string;
  tx_fraud: number;
  tx_fraud_scenario: number;
  ml_risk_score: number;
  stream_index?: number;
  stream_total?: number;
}

export default function SimulationStudioPage() {
  const [config, setConfig] = useState<SimConfig>({
    n_customers: 5000,
    n_terminals: 500,
    nb_days: 90,
    radius: 5.0,
    scenario_1_enabled: true,
    scenario_2_enabled: true,
    scenario_3_enabled: true,
  });

  const [stats, setStats] = useState<SimulationStats | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamTransactions, setStreamTransactions] = useState<StreamTransaction[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = useCallback(async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/simulation/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: SimulationStats = await res.json();
      setStats(data);
      setStreamTransactions([]);
    } catch (e: any) {
      setError(e.message || 'Failed to generate dataset');
    } finally {
      setIsGenerating(false);
    }
  }, [config]);

  const handleStreamToggle = useCallback(async () => {
    if (isStreaming) {
      // Stop stream
      try {
        await fetch(`${API_BASE}/simulation/stream/stop`, { method: 'POST' });
      } catch { /* ignore */ }
      setIsStreaming(false);
    } else {
      // Start stream
      try {
        const res = await fetch(`${API_BASE}/simulation/stream/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tps_rate: 10 }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setIsStreaming(true);
      } catch (e: any) {
        setError(e.message || 'Failed to start stream');
      }
    }
  }, [isStreaming]);

  const handleNewTransaction = useCallback((tx: StreamTransaction) => {
    setStreamTransactions(prev => {
      const next = [tx, ...prev];
      return next.length > 200 ? next.slice(0, 200) : next;
    });
  }, []);

  return (
    <div className="page-wrapper">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FlaskConical size={22} style={{ color: 'var(--primary)', filter: 'drop-shadow(0 0 8px rgba(79,124,255,0.5))' }} />
            Simulation Studio
          </h1>
          <p className="page-description">
            Fraud Detection Handbook — Interactive Transaction & Fraud Simulator
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-4)' }}>
          {isStreaming && (
            <div className="sim-stream-indicator">
              <span className="sim-stream-dot live" />
              <span style={{ color: 'var(--success)' }}>LIVE</span>
            </div>
          )}
          {stats && (
            <span className="badge badge-neutral">
              {stats.total_transactions.toLocaleString()} tx
            </span>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div style={{
          padding: 'var(--spacing-3) var(--spacing-4)',
          background: 'var(--danger-bg)',
          border: '1px solid rgba(248, 113, 113, 0.2)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--danger)',
          fontSize: '0.8125rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span>{error}</span>
          <button onClick={() => setError(null)} style={{ all: 'unset', cursor: 'pointer', fontWeight: 700 }}>✕</button>
        </div>
      )}

      {/* Control Deck */}
      <SimulationControls
        config={config}
        onConfigChange={setConfig}
        onGenerate={handleGenerate}
        onStreamToggle={handleStreamToggle}
        isGenerating={isGenerating}
        isStreaming={isStreaming}
        hasData={!!stats}
      />

      {/* Main Grid: Spatial Map + Analytics */}
      {stats && (
        <div className="sim-main-grid">
          <div className="card" style={{ padding: 'var(--spacing-4)' }}>
            <div className="card-header" style={{ marginBottom: 'var(--spacing-3)' }}>
              <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Radio size={16} style={{ color: 'var(--primary)' }} />
                Spatial Grid (100×100 km)
              </h2>
              <p className="card-description">Customer-terminal spatial association</p>
            </div>
            <SpatialMap
              customerCoords={stats.customer_coordinates}
              terminalCoords={stats.terminal_coordinates}
              compromisedTerminals={stats.compromised_terminals}
              compromisedCustomers={stats.compromised_customers}
            />
          </div>

          <SimulationAnalytics
            stats={stats}
            streamTransactions={streamTransactions}
          />
        </div>
      )}

      {/* Live Stream Table */}
      <div className="card" style={{ padding: 'var(--spacing-4)' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-3)' }}>
          <div>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={16} style={{ color: 'var(--warning)' }} />
              Live Transaction Feed
            </h2>
            <p className="card-description">
              {isStreaming
                ? `Streaming at 10 TPS — ${streamTransactions.length} received`
                : 'Start stream to see real-time transactions'}
            </p>
          </div>
          {isStreaming && (
            <span className="badge badge-success" style={{ animation: 'pulse-dot 2s ease-in-out infinite' }}>
              STREAMING
            </span>
          )}
        </div>
        <LiveStreamTable
          transactions={streamTransactions}
          isStreaming={isStreaming}
          onNewTransaction={handleNewTransaction}
        />
      </div>
    </div>
  );
}
