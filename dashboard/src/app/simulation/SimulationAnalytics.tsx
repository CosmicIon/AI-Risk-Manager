'use client';

import { useMemo } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, ZAxis,
} from 'recharts';
import { TrendingUp, Target, AlertTriangle } from 'lucide-react';
import type { StreamTransaction } from './page';

interface SimulationStats {
  total_transactions: number;
  total_customers: number;
  total_terminals: number;
  fraud_count: number;
  fraud_rate: number;
  scenario_breakdown: {
    scenario_0_legitimate: number;
    scenario_1_high_amount: number;
    scenario_2_compromised_terminal: number;
    scenario_3_account_takeover: number;
  };
  total_loss_inr: number;
  avg_amount: number;
  median_amount: number;
}

interface Props {
  stats: SimulationStats;
  streamTransactions: StreamTransaction[];
}

const SCENARIO_COLORS = {
  Legitimate: '#34d399',
  'High Amount': '#fbbf24',
  'POS Skimming': '#f87171',
  'Acct Takeover': '#a78bfa',
};

const tooltipStyle = {
  backgroundColor: '#0f0f14',
  border: '1px solid #1e1e2e',
  borderRadius: '8px',
  fontSize: '0.75rem',
};

export default function SimulationAnalytics({ stats, streamTransactions }: Props) {
  // Fraud share donut data
  const donutData = useMemo(() => [
    { name: 'Legitimate', value: stats.scenario_breakdown.scenario_0_legitimate },
    { name: 'High Amount', value: stats.scenario_breakdown.scenario_1_high_amount },
    { name: 'POS Skimming', value: stats.scenario_breakdown.scenario_2_compromised_terminal },
    { name: 'Acct Takeover', value: stats.scenario_breakdown.scenario_3_account_takeover },
  ].filter(d => d.value > 0), [stats]);

  // Scatter data from stream transactions (sample for performance)
  const scatterData = useMemo(() => {
    const txs = streamTransactions.length > 0 ? streamTransactions : [];
    const sampled = txs.slice(0, 100);
    return sampled.map((tx, i) => ({
      x: i,
      y: tx.tx_amount,
      scenario: tx.tx_fraud_scenario,
      fill: tx.tx_fraud_scenario === 0
        ? '#34d399'
        : tx.tx_fraud_scenario === 1
          ? '#fbbf24'
          : tx.tx_fraud_scenario === 2
            ? '#f87171'
            : '#a78bfa',
    }));
  }, [streamTransactions]);

  // Detection performance from stream
  const detection = useMemo(() => {
    if (streamTransactions.length === 0) {
      return { precision: 0, recall: 0, f1: 0, fpCost: 0, fnCost: 0 };
    }

    let tp = 0, fp = 0, fn = 0, tn = 0;
    const THRESHOLD = 0.5;

    for (const tx of streamTransactions) {
      const predicted = tx.ml_risk_score >= THRESHOLD ? 1 : 0;
      const actual = tx.tx_fraud;
      if (predicted === 1 && actual === 1) tp++;
      else if (predicted === 1 && actual === 0) fp++;
      else if (predicted === 0 && actual === 1) fn++;
      else tn++;
    }

    const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
    const recall = tp + fn > 0 ? tp / (tp + fn) : 0;
    const f1 = precision + recall > 0 ? 2 * (precision * recall) / (precision + recall) : 0;

    // Estimate ₹ cost: FP = blocked legit tx average, FN = missed fraud average
    const fpCost = fp * stats.avg_amount * 0.1; // opportunity cost
    const fnCost = fn * stats.avg_amount * 2.5;  // fraud loss

    return { precision, recall, f1, fpCost, fnCost };
  }, [streamTransactions, stats]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-5)' }}>
      {/* Fraud Share Donut */}
      <div className="card" style={{ padding: 'var(--spacing-4)' }}>
        <div className="card-header" style={{ marginBottom: 'var(--spacing-2)' }}>
          <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Target size={16} style={{ color: 'var(--primary)' }} />
            Fraud Share by Scenario
          </h2>
        </div>

        {/* KPI tiles */}
        <div className="sim-kpi-row" style={{ marginBottom: 'var(--spacing-4)' }}>
          <div className="sim-kpi-tile">
            <div className="sim-kpi-label">Total Fraud</div>
            <div className="sim-kpi-number" style={{ color: 'var(--danger)' }}>
              {stats.fraud_count.toLocaleString()}
            </div>
          </div>
          <div className="sim-kpi-tile">
            <div className="sim-kpi-label">Fraud Rate</div>
            <div className="sim-kpi-number" style={{ color: 'var(--warning)' }}>
              {(stats.fraud_rate * 100).toFixed(2)}%
            </div>
          </div>
          <div className="sim-kpi-tile">
            <div className="sim-kpi-label">Total Loss</div>
            <div className="sim-kpi-number" style={{ color: 'var(--purple)', fontSize: '1.125rem' }}>
              ₹{(stats.total_loss_inr / 1e6).toFixed(2)}M
            </div>
          </div>
        </div>

        <div style={{ width: '100%', height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={donutData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={3}
                dataKey="value"
                stroke="none"
              >
                {donutData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={SCENARIO_COLORS[entry.name as keyof typeof SCENARIO_COLORS] || '#555'}
                  />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend
                wrapperStyle={{ fontSize: '0.6875rem', color: 'var(--text-secondary)' }}
                iconType="circle"
                iconSize={8}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detection Performance (from stream) */}
      <div className="card" style={{ padding: 'var(--spacing-4)' }}>
        <div className="card-header" style={{ marginBottom: 'var(--spacing-3)' }}>
          <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={16} style={{ color: 'var(--success)' }} />
            Detection Performance
          </h2>
          <p className="card-description">
            {streamTransactions.length > 0
              ? `Based on ${streamTransactions.length} streamed transactions`
              : 'Start streaming to see live detection metrics'}
          </p>
        </div>

        <div className="sim-kpi-row">
          <div className="sim-kpi-tile">
            <div className="sim-kpi-label">Precision</div>
            <div className="sim-kpi-number" style={{ color: 'var(--primary)' }}>
              {(detection.precision * 100).toFixed(1)}%
            </div>
          </div>
          <div className="sim-kpi-tile">
            <div className="sim-kpi-label">Recall</div>
            <div className="sim-kpi-number" style={{ color: 'var(--success)' }}>
              {(detection.recall * 100).toFixed(1)}%
            </div>
          </div>
          <div className="sim-kpi-tile">
            <div className="sim-kpi-label">F1 Score</div>
            <div className="sim-kpi-number" style={{ color: 'var(--warning)' }}>
              {(detection.f1 * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {streamTransactions.length > 0 && (
          <div style={{ display: 'flex', gap: 'var(--spacing-4)', marginTop: 'var(--spacing-4)' }}>
            <div style={{
              flex: 1,
              padding: 'var(--spacing-3)',
              background: 'var(--danger-bg)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid rgba(248, 113, 113, 0.15)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <AlertTriangle size={12} style={{ color: 'var(--danger)' }} />
                <span style={{ fontSize: '0.625rem', fontWeight: 700, color: 'var(--danger)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
                  FN Cost (Missed Fraud)
                </span>
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 800, color: 'var(--danger)' }}>
                ₹{detection.fnCost.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </div>
            </div>
            <div style={{
              flex: 1,
              padding: 'var(--spacing-3)',
              background: 'var(--warning-bg)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid rgba(251, 191, 36, 0.15)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <AlertTriangle size={12} style={{ color: 'var(--warning)' }} />
                <span style={{ fontSize: '0.625rem', fontWeight: 700, color: 'var(--warning)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
                  FP Cost (False Blocks)
                </span>
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 800, color: 'var(--warning)' }}>
                ₹{detection.fpCost.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </div>
            </div>
          </div>
        )}

        {/* Amount vs Index Scatter (if streaming) */}
        {scatterData.length > 0 && (
          <div style={{ marginTop: 'var(--spacing-4)' }}>
            <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 'var(--spacing-2)' }}>
              Amount Distribution (Recent Stream)
            </p>
            <div style={{ width: '100%', height: 160 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 4, right: 4, bottom: 4, left: -12 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                  <XAxis dataKey="x" name="Index" stroke="#55556a" fontSize={9} tickLine={false} axisLine={false} />
                  <YAxis dataKey="y" name="Amount" stroke="#55556a" fontSize={9} tickLine={false} axisLine={false} />
                  <ZAxis range={[20, 60]} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [`₹${value.toLocaleString('en-IN')}`, 'Amount']}
                  />
                  <Scatter data={scatterData}>
                    {scatterData.map((entry, idx) => (
                      <Cell key={idx} fill={entry.fill} fillOpacity={0.7} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
