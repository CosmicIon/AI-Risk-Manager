'use client';

import { Settings, Save, Search, Filter } from 'lucide-react';

const MOCK_RETURNS = [
  { id: 'RET-001', customer: 'CUST-8812', amount: '₹12,000', score: 0.85, tier: 'High Risk', decision: 'Manual Review' },
  { id: 'RET-002', customer: 'CUST-1921', amount: '₹1,500', score: 0.12, tier: 'Low Risk', decision: 'Auto Approve' },
  { id: 'RET-003', customer: 'CUST-3310', amount: '₹8,500', score: 0.92, tier: 'High Risk', decision: 'Auto Deny' },
  { id: 'RET-004', customer: 'CUST-9912', amount: '₹4,200', score: 0.45, tier: 'Medium Risk', decision: 'Manual Review' },
];

export default function ReturnsPage() {
  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Return Abuse Scoring</h1>
          <p className="page-description text-muted">Real-time ML risk scoring and policy enforcement for e-commerce returns.</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <h2 className="card-title">Recent Return Decisions</h2>
          </div>
          
          <div className="table-controls">
            <div className="search-box">
              <Search size={18} className="search-icon" />
              <input type="text" placeholder="Search Return ID or Customer..." className="input search-input-sm" />
            </div>
            <button className="btn btn-outline"><Filter size={16} /> Filter</button>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Return ID</th>
                  <th>Customer</th>
                  <th>Amount</th>
                  <th>Risk Score</th>
                  <th>Tier</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_RETURNS.map(ret => (
                  <tr key={ret.id}>
                    <td className="font-medium text-primary">{ret.id}</td>
                    <td className="text-muted">{ret.customer}</td>
                    <td className="font-medium">{ret.amount}</td>
                    <td>
                      <span style={{ color: ret.score > 0.8 ? 'var(--danger)' : ret.score > 0.4 ? 'var(--warning)' : 'var(--success)', fontWeight: 600 }}>
                        {ret.score.toFixed(2)}
                      </span>
                    </td>
                    <td>{ret.tier}</td>
                    <td>
                      <span className={`badge ${ret.decision === 'Auto Approve' ? 'badge-success' : ret.decision === 'Auto Deny' ? 'badge-danger' : 'badge-warning'}`}>
                        {ret.decision}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-header flex justify-between items-center">
            <h2 className="card-title">Policy Configuration</h2>
            <Settings size={18} className="text-muted" />
          </div>
          <div className="flex-col gap-4">
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Auto-Approve Threshold</span>
                <span className="text-primary font-bold">0.30</span>
              </label>
              <input type="range" min="0" max="1" step="0.01" defaultValue="0.30" className="w-full" />
              <p className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>Scores below this threshold are automatically approved.</p>
            </div>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Auto-Deny Threshold</span>
                <span className="text-danger font-bold">0.90</span>
              </label>
              <input type="range" min="0" max="1" step="0.01" defaultValue="0.90" className="w-full" />
              <p className="text-muted" style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>Scores above this threshold are automatically denied.</p>
            </div>
            <button className="btn btn-primary w-full" style={{ marginTop: '1rem' }}><Save size={16} /> Save Policy</button>
          </div>
        </div>
      </div>
    </div>
  );
}
