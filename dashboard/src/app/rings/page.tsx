'use client';

import ForceGraph from '@/components/graph-viz/ForceGraph';
import { Network, Search, Filter } from 'lucide-react';

export default function RingsPage() {
  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Abuse-Ring Sentinel</h1>
          <p className="page-description text-muted">Neo4j Graph-based community detection and collusive fraud visualization.</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <div className="card" style={{ gridColumn: 'span 3' }}>
          <div className="card-header flex justify-between">
            <h2 className="card-title">Network Visualization</h2>
            <div className="flex gap-2">
              <span className="badge" style={{ backgroundColor: 'var(--primary)', color: 'white' }}>Card</span>
              <span className="badge" style={{ backgroundColor: 'var(--warning)', color: 'white' }}>Device</span>
              <span className="badge" style={{ backgroundColor: 'var(--success)', color: 'white' }}>Account</span>
            </div>
          </div>
          <div style={{ backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', height: '500px', overflow: 'hidden' }}>
            <ForceGraph />
          </div>
        </div>

        <div className="flex-col gap-6" style={{ display: 'flex' }}>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Detected Rings</h2>
            </div>
            
            <div className="table-controls" style={{ marginBottom: '1rem' }}>
              <div className="search-box w-full">
                <Search size={14} className="search-icon" />
                <input type="text" placeholder="Search Ring ID..." className="input search-input-sm" style={{ padding: '0.25rem 0.5rem 0.25rem 2rem' }} />
              </div>
            </div>

            <div className="flex-col gap-3">
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', cursor: 'pointer', borderLeft: '3px solid var(--danger)' }}>
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-primary">Ring-092A</span>
                  <span className="badge badge-danger">92% Risk</span>
                </div>
                <div className="text-muted" style={{ fontSize: '0.75rem' }}>14 Nodes • 28 Edges</div>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--surface-hover)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', cursor: 'pointer', borderLeft: '3px solid var(--warning)' }}>
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-primary">Ring-011B</span>
                  <span className="badge badge-warning">64% Risk</span>
                </div>
                <div className="text-muted" style={{ fontSize: '0.75rem' }}>7 Nodes • 12 Edges</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
