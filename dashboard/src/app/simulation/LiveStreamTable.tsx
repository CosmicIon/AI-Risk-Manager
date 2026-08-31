'use client';

import { useEffect, useRef } from 'react';
import type { StreamTransaction } from './page';

const MCC_NAMES: Record<string, string> = {
  '5411': 'Grocery',
  '5732': 'Electronics',
  '5651': 'Apparel',
  '5812': 'Dining',
  '4829': 'Transfer',
};

const SCENARIO_LABELS: Record<number, { label: string; badge: string }> = {
  0: { label: 'Legitimate', badge: 'sim-badge-legit' },
  1: { label: 'High Amount', badge: 'sim-badge-s1' },
  2: { label: 'POS Skimming', badge: 'sim-badge-s2' },
  3: { label: 'Acct Takeover', badge: 'sim-badge-s3' },
};

interface Props {
  transactions: StreamTransaction[];
  isStreaming: boolean;
  onNewTransaction: (tx: StreamTransaction) => void;
}

function getRiskColor(score: number): string {
  if (score >= 0.7) return 'var(--danger)';
  if (score >= 0.4) return 'var(--warning)';
  return 'var(--success)';
}

export default function LiveStreamTable({ transactions, isStreaming, onNewTransaction }: Props) {
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // WebSocket connection
  useEffect(() => {
    if (!isStreaming) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    const wsUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1')
      .replace('http://', 'ws://')
      .replace('https://', 'wss://');

    const ws = new WebSocket(`${wsUrl}/simulation/stream/ws`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const tx: StreamTransaction = JSON.parse(event.data);
        onNewTransaction(tx);
      } catch { /* ignore parse errors */ }
    };

    ws.onerror = () => {
      console.warn('WebSocket error — stream may not be available');
    };

    // Send periodic keepalive
    const keepalive = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 10000);

    return () => {
      clearInterval(keepalive);
      ws.close();
      wsRef.current = null;
    };
  }, [isStreaming, onNewTransaction]);

  if (transactions.length === 0) {
    return (
      <div className="sim-empty-state" id="sim-ticker-empty">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
        </svg>
        <p>
          {isStreaming
            ? 'Waiting for transactions…'
            : 'Generate a dataset, then click "Start Live Stream" to see transactions flow in real time.'}
        </p>
      </div>
    );
  }

  return (
    <div className="sim-ticker-container" ref={scrollRef} id="sim-ticker-table">
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>TX ID</th>
              <th>Customer</th>
              <th>Terminal / MCC</th>
              <th style={{ textAlign: 'right' }}>Amount (₹)</th>
              <th>Scenario</th>
              <th>Ground Truth</th>
              <th>ML Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx, i) => {
              const scenario = SCENARIO_LABELS[tx.tx_fraud_scenario] || SCENARIO_LABELS[0];
              const isFraud = tx.tx_fraud === 1;
              const mccName = MCC_NAMES[tx.mcc] || tx.mcc;
              const riskColor = getRiskColor(tx.ml_risk_score);
              const timeStr = tx.tx_datetime
                ? new Date(tx.tx_datetime).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                : '--:--';

              return (
                <tr
                  key={`${tx.transaction_id}-${i}`}
                  className={`sim-ticker-row ${isFraud ? 'fraud' : ''}`}
                  style={{ animationDelay: `${i * 20}ms` }}
                >
                  <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                    {timeStr}
                  </td>
                  <td style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                    {tx.transaction_id.slice(-8)}
                  </td>
                  <td style={{ fontSize: '0.8125rem' }}>
                    {tx.customer_id}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8125rem' }}>{tx.terminal_id}</span>
                    <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginLeft: '6px' }}>
                      {mccName}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={`sim-amount ${isFraud ? 'fraud' : ''}`}>
                      ₹{tx.tx_amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${scenario.badge}`}>
                      {scenario.label}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${isFraud ? 'badge-danger' : 'badge-success'}`}>
                      {isFraud ? 'FRAUD' : 'LEGIT'}
                    </span>
                  </td>
                  <td>
                    <div className="sim-risk-bar">
                      <div
                        className="sim-risk-fill"
                        style={{
                          width: `${Math.max(8, tx.ml_risk_score * 60)}px`,
                          background: riskColor,
                        }}
                      />
                      <span className="sim-risk-value" style={{ color: riskColor }}>
                        {(tx.ml_risk_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td>
                    {tx.ml_risk_score >= 0.5 ? (
                      <span className="badge badge-danger">Blocked</span>
                    ) : (
                      <span className="badge badge-success">Passed</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
