'use client';

import { Activity, AlertTriangle, MapPin, CreditCard, Filter } from 'lucide-react';

const MOCK_ALERTS = [
  { id: 'FA-1001', type: 'Velocity Spike', severity: 'Critical', entity: 'IP 192.168.1.5', time: '10m ago' },
  { id: 'FA-1002', type: 'High Risk Geography', severity: 'High', entity: 'Card ending 4412', time: '45m ago' },
  { id: 'FA-1003', type: 'Abnormal Volume', severity: 'Medium', entity: 'Merchant ID 9912', time: '2h ago' },
];

export default function FraudAlertsPage() {
  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Fraud Alerts</h1>
          <p className="page-description text-muted">Kafka stream-processed anomalies and high-velocity alerts.</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="card">
          <div className="card-header flex justify-between">
            <h2 className="card-title">Active Alerts</h2>
            <button className="btn btn-outline btn-sm"><Filter size={14} /></button>
          </div>
          <div className="flex-col gap-4">
            {MOCK_ALERTS.map(alert => (
              <div key={alert.id} style={{ padding: '0.75rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--bg-color)', marginBottom: '0.75rem' }}>
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={16} color={alert.severity === 'Critical' ? 'var(--danger)' : alert.severity === 'High' ? 'var(--warning)' : 'var(--primary)'} />
                    <span className="font-bold">{alert.type}</span>
                  </div>
                  <span className="text-muted" style={{ fontSize: '0.75rem' }}>{alert.time}</span>
                </div>
                <div className="text-secondary" style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>{alert.entity}</div>
                <button className="btn btn-outline w-full btn-sm">Investigate</button>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <h2 className="card-title">Alert Investigation: Velocity Spike</h2>
          </div>
          
          <div className="grid grid-cols-3 gap-4" style={{ marginBottom: '1.5rem' }}>
            <div style={{ padding: '1rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
              <div className="text-muted" style={{ fontSize: '0.75rem', marginBottom: '0.25rem' }}><Activity size={12} className="inline-icon"/> Current TPS</div>
              <div className="font-bold" style={{ fontSize: '1.5rem', color: 'var(--danger)' }}>142.5</div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>Baseline: 12.1</div>
            </div>
            <div style={{ padding: '1rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
              <div className="text-muted" style={{ fontSize: '0.75rem', marginBottom: '0.25rem' }}><MapPin size={12} className="inline-icon"/> Origin</div>
              <div className="font-bold" style={{ fontSize: '1.1rem' }}>Multiple (VPN detected)</div>
            </div>
            <div style={{ padding: '1rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
              <div className="text-muted" style={{ fontSize: '0.75rem', marginBottom: '0.25rem' }}><CreditCard size={12} className="inline-icon"/> Cards Used</div>
              <div className="font-bold" style={{ fontSize: '1.5rem' }}>84</div>
            </div>
          </div>
          
          <div style={{ height: '300px', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span className="text-muted">TPS Chart Placeholder</span>
          </div>
        </div>
      </div>
    </div>
  );
}
