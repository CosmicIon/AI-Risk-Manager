'use client';

import { useState } from 'react';
import { Activity, AlertTriangle, MapPin, CreditCard, Filter, ShieldOff, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts';

const TPS_DATA = {
  'FA-1001': [
    { t: '10:00', tps: 11 }, { t: '10:05', tps: 13 }, { t: '10:10', tps: 12 },
    { t: '10:15', tps: 15 }, { t: '10:20', tps: 28 }, { t: '10:25', tps: 67 },
    { t: '10:30', tps: 142 }, { t: '10:35', tps: 128 }, { t: '10:40', tps: 95 },
  ],
  'FA-1002': [
    { t: '09:00', tps: 8 }, { t: '09:15', tps: 9 }, { t: '09:30', tps: 11 },
    { t: '09:45', tps: 18 }, { t: '10:00', tps: 35 }, { t: '10:15', tps: 48 },
    { t: '10:30', tps: 41 }, { t: '10:45', tps: 39 },
  ],
  'FA-1003': [
    { t: '08:00', tps: 200 }, { t: '08:30', tps: 420 }, { t: '09:00', tps: 680 },
    { t: '09:30', tps: 910 }, { t: '10:00', tps: 1240 }, { t: '10:30', tps: 1100 },
    { t: '11:00', tps: 870 },
  ],
};

const MOCK_ALERTS = [
  {
    id: 'FA-1001',
    type: 'Velocity Spike',
    severity: 'Critical',
    entity: 'IP 192.168.1.5',
    time: '10m ago',
    metric: 'TPS',
    current: '142.5',
    baseline: '12.1',
    origin: 'Multiple (VPN detected)',
    cardsUsed: '84',
    baseline_tps: 12.1,
    icon: Activity,
  },
  {
    id: 'FA-1002',
    type: 'High Risk Geography',
    severity: 'High',
    entity: 'Card ending 4412',
    time: '45m ago',
    metric: 'TPS',
    current: '48',
    baseline: '9',
    origin: 'Lagos, NG (flagged)',
    cardsUsed: '12',
    baseline_tps: 9,
    icon: MapPin,
  },
  {
    id: 'FA-1003',
    type: 'Abnormal Volume',
    severity: 'Medium',
    entity: 'Merchant ID 9912',
    time: '2h ago',
    metric: 'Orders/hr',
    current: '1,240',
    baseline: '200',
    origin: 'Domestic',
    cardsUsed: '340',
    baseline_tps: 200,
    icon: TrendingUp,
  },
];

const SEVERITY_COLOR: Record<string, string> = {
  Critical: 'var(--danger)',
  High: 'var(--warning)',
  Medium: 'var(--primary)',
};

const SEVERITY_BADGE: Record<string, string> = {
  Critical: 'badge badge-danger',
  High: 'badge badge-warning',
  Medium: 'badge badge-purple',
};

const tooltipStyle = {
  backgroundColor: '#0f0f14',
  border: '1px solid #1e1e2e',
  borderRadius: '8px',
  fontSize: '0.75rem',
};

export default function FraudAlertsPage() {
  const [selectedId, setSelectedId] = useState('FA-1001');
  const selected = MOCK_ALERTS.find((a) => a.id === selectedId)!;
  const tpsData = TPS_DATA[selectedId as keyof typeof TPS_DATA];

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Fraud Alerts</h1>
          <p className="page-description">Kafka stream-processed anomalies and high-velocity alerts.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 'var(--spacing-5)' }}>
        {/* Alert list */}
        <div className="card" style={{ padding: 'var(--spacing-5)', display: 'flex', flexDirection: 'column', gap: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-4)' }}>
            <h2 className="card-title">Active Alerts</h2>
            <button className="btn btn-outline btn-sm" style={{ gap: '6px' }}>
              <Filter size={12} /> Filter
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-2)' }}>
            {MOCK_ALERTS.map((alert) => {
              const Icon = alert.icon;
              const isActive = alert.id === selectedId;
              return (
                <button
                  key={alert.id}
                  onClick={() => setSelectedId(alert.id)}
                  style={{
                    all: 'unset',
                    cursor: 'pointer',
                    padding: 'var(--spacing-3) var(--spacing-4)',
                    borderRadius: 'var(--radius-lg)',
                    border: isActive
                      ? `1px solid ${SEVERITY_COLOR[alert.severity]}55`
                      : '1px solid var(--border-color)',
                    backgroundColor: isActive ? `${SEVERITY_COLOR[alert.severity]}0d` : 'var(--surface-color-2)',
                    transition: 'all 200ms ease',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Icon size={14} color={SEVERITY_COLOR[alert.severity]} />
                      <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {alert.type}
                      </span>
                    </div>
                    <span className={SEVERITY_BADGE[alert.severity]}>{alert.severity}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{alert.entity}</span>
                    <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 600 }}>{alert.time}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Investigation panel */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-5)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h2 className="card-title">Investigation: {selected.type}</h2>
              <p className="card-description">{selected.entity} — {selected.time}</p>
            </div>
            <span className={SEVERITY_BADGE[selected.severity]}>{selected.severity}</span>
          </div>

          {/* Metric tiles */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--spacing-4)' }}>
            {[
              { label: selected.metric, Icon: Activity, value: selected.current, sub: `Baseline: ${selected.baseline}`, color: SEVERITY_COLOR[selected.severity] },
              { label: 'Origin', Icon: MapPin, value: selected.origin, sub: null, color: 'var(--text-secondary)' },
              { label: 'Cards Used', Icon: CreditCard, value: selected.cardsUsed, sub: 'unique instruments', color: 'var(--text-secondary)' },
            ].map(({ label, Icon, value, sub, color }) => (
              <div key={label} style={{
                padding: 'var(--spacing-4)',
                backgroundColor: 'var(--surface-color-2)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-color)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                  <Icon size={12} color="var(--text-muted)" />
                  <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{label}</span>
                </div>
                <div style={{ fontSize: '1.375rem', fontWeight: 800, color, letterSpacing: '-0.02em', lineHeight: 1.1 }}>{value}</div>
                {sub && <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '4px', fontWeight: 500 }}>{sub}</div>}
              </div>
            ))}
          </div>

          {/* TPS / Volume chart */}
          <div style={{ flex: 1 }}>
            <div style={{ marginBottom: 'var(--spacing-3)' }}>
              <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                {selected.metric} Over Time
              </p>
            </div>
            <div style={{ width: '100%', height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={tpsData} margin={{ top: 4, right: 12, bottom: 0, left: -16 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" vertical={false} />
                  <XAxis dataKey="t" stroke="#55556a" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#55556a" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: '#f0f0fa' }} />
                  <ReferenceLine
                    y={selected.baseline_tps}
                    stroke="#55556a"
                    strokeDasharray="4 3"
                    label={{ value: 'Baseline', position: 'insideTopRight', fontSize: 10, fill: '#55556a' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="tps"
                    name={selected.metric}
                    stroke={SEVERITY_COLOR[selected.severity]}
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: SEVERITY_COLOR[selected.severity], strokeWidth: 0 }}
                    activeDot={{ r: 5, strokeWidth: 0 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 'var(--spacing-3)' }}>
            <button className="btn btn-danger" style={{ flex: 1 }}>
              <ShieldOff size={15} /> Block Entity
            </button>
            <button className="btn btn-outline" style={{ flex: 1 }}>
              Escalate to L2
            </button>
            <button className="btn btn-outline">
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
