'use client';

import { Activity, Download, ChevronDown } from 'lucide-react';

export default function EvaluationPage() {
  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Model Evaluation</h1>
          <p className="page-description text-muted">Offline metrics, ROC curves, and drift detection (PSI).</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <div className="card" style={{ gridColumn: 'span 3' }}>
          <div className="card-header flex justify-between items-center">
            <h2 className="card-title">Champion vs Challenger: return_risk_model</h2>
            <button className="btn btn-outline btn-sm">Select Model <ChevronDown size={14} /></button>
          </div>
          
          <div className="table-wrapper" style={{ marginBottom: '1.5rem' }}>
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Champion (v2.1)</th>
                  <th>Challenger (v2.2)</th>
                  <th>Diff</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="font-medium text-muted">ROC AUC</td>
                  <td>0.892</td>
                  <td>0.915</td>
                  <td className="text-success font-bold">+0.023</td>
                </tr>
                <tr>
                  <td className="font-medium text-muted">Precision @ 90% Recall</td>
                  <td>0.824</td>
                  <td>0.851</td>
                  <td className="text-success font-bold">+0.027</td>
                </tr>
                <tr>
                  <td className="font-medium text-muted">F1 Score</td>
                  <td>0.841</td>
                  <td>0.866</td>
                  <td className="text-success font-bold">+0.025</td>
                </tr>
                <tr>
                  <td className="font-medium text-muted">Inference Latency (P99)</td>
                  <td>45ms</td>
                  <td>62ms</td>
                  <td className="text-danger font-bold">+17ms</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="flex gap-4">
            <div style={{ flex: 1, height: '250px', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span className="text-muted">ROC Curve Chart</span>
            </div>
            <div style={{ flex: 1, height: '250px', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span className="text-muted">Calibration Curve Chart</span>
            </div>
          </div>
        </div>

        <div className="flex-col gap-6" style={{ display: 'flex' }}>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Feature Drift (PSI)</h2>
            </div>
            
            <div className="flex-col gap-2">
              <div className="flex justify-between items-center" style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                <span className="text-muted" style={{ fontSize: '0.875rem' }}>account_age_days</span>
                <span className="badge badge-success">0.02</span>
              </div>
              <div className="flex justify-between items-center" style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                <span className="text-muted" style={{ fontSize: '0.875rem' }}>transaction_amount</span>
                <span className="badge badge-success">0.04</span>
              </div>
              <div className="flex justify-between items-center" style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                <span className="text-muted" style={{ fontSize: '0.875rem' }}>ip_distance_km</span>
                <span className="badge badge-warning">0.14</span>
              </div>
              <div className="flex justify-between items-center" style={{ padding: '0.5rem 0' }}>
                <span className="text-muted" style={{ fontSize: '0.875rem' }}>device_velocity_24h</span>
                <span className="badge badge-danger">0.28</span>
              </div>
            </div>
          </div>
          
          <button className="btn btn-primary w-full"><Download size={16} /> Download Report (PDF)</button>
        </div>
      </div>
    </div>
  );
}
