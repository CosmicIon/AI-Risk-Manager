import { ArrowLeft, CheckCircle, Clock, FileText, CheckSquare, Square, ThumbsUp, ThumbsDown } from 'lucide-react';
import Link from 'next/link';

export default async function ChargebackDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div className="page-wrapper">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link href="/chargebacks" className="btn btn-outline" style={{ padding: '0.5rem' }}>
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h1 className="page-title">Case {id}</h1>
            <p className="page-description text-muted">ARN: 31525367890123456789012 • Amount: ₹45,000</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 font-medium" style={{ color: 'var(--danger)' }}>
            <Clock size={16} />
            Deadline: 24h
          </div>
          <button className="btn btn-danger"><ThumbsDown size={16} /> Reject</button>
          <button className="btn btn-success" style={{ backgroundColor: 'var(--success)', color: 'white' }}><ThumbsUp size={16} /> Approve & Submit</button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="flex-col gap-6" style={{ gridColumn: 'span 2', display: 'flex' }}>
          
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Evidence Assembly</h2>
              <p className="card-description">Auto-gathered evidence items for the representment package.</p>
            </div>
            <div className="evidence-list">
              <div className="flex justify-between items-center" style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)' }}>
                <div className="flex items-center gap-3">
                  <CheckSquare size={18} color="var(--success)" />
                  <span className="font-medium">Transaction Receipt (Receipt_9921.pdf)</span>
                </div>
                <span className="badge badge-success">Found</span>
              </div>
              <div className="flex justify-between items-center" style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)' }}>
                <div className="flex items-center gap-3">
                  <CheckSquare size={18} color="var(--success)" />
                  <span className="font-medium">Proof of Delivery (FedEx Tracking)</span>
                </div>
                <span className="badge badge-success">Found</span>
              </div>
              <div className="flex justify-between items-center" style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)' }}>
                <div className="flex items-center gap-3">
                  <CheckSquare size={18} color="var(--success)" />
                  <span className="font-medium">Customer Communications (Email Thread)</span>
                </div>
                <span className="badge badge-success">Found</span>
              </div>
              <div className="flex justify-between items-center" style={{ padding: '0.75rem 0' }}>
                <div className="flex items-center gap-3">
                  <Square size={18} color="var(--text-muted)" />
                  <span className="font-medium">Usage Logs (SaaS Login Data)</span>
                </div>
                <span className="badge badge-neutral">Not Applicable</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header flex justify-between items-center">
              <div>
                <h2 className="card-title">Generated Narrative</h2>
                <p className="card-description">AI-generated defense narrative for the issuer.</p>
              </div>
              <button className="btn btn-outline btn-sm"><FileText size={14} /> Edit</button>
            </div>
            <div style={{ backgroundColor: 'var(--bg-color)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '0.875rem', lineHeight: '1.6' }}>
              <p>To whom it may concern,</p>
              <br/>
              <p>We are responding to the chargeback filed for ARN 31525367890123456789012 for the amount of ₹45,000 under Reason Code 10.4 (Other Fraud - Card Absent Environment).</p>
              <br/>
              <p>We submit that this transaction was authorized by the cardholder. We have included the signed transaction receipt and proof of delivery via FedEx tracking demonstrating the merchandise was delivered to the cardholder's verified billing address on record.</p>
              <br/>
              <p>We respectfully request that this chargeback be reversed.</p>
            </div>
          </div>

        </div>

        <div className="flex-col gap-6" style={{ display: 'flex' }}>
          
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Confidence Score</h2>
            </div>
            <div className="flex-col items-center justify-center gap-2" style={{ padding: '1rem 0' }}>
              <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--success)', textAlign: 'center' }}>88%</div>
              <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>High Win Probability</p>
            </div>
            
            <div style={{ marginTop: '1rem' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Top Driving Features (SHAP)</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span>Proof of Delivery present</span>
                  <span style={{ color: 'var(--success)' }}>+24%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span>AVS Match (Y)</span>
                  <span style={{ color: 'var(--success)' }}>+15%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span>Past Chargeback History</span>
                  <span style={{ color: 'var(--danger)' }}>-8%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Similar Historical Cases</h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <Link href="/chargebacks/CB-7732" style={{ color: 'var(--primary)', fontSize: '0.875rem', fontWeight: 500 }}>CB-7732</Link>
                  <span className="badge badge-success">Won</span>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Reason 10.4 • 91% similarity</p>
              </div>
              <div style={{ paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <Link href="/chargebacks/CB-7120" style={{ color: 'var(--primary)', fontSize: '0.875rem', fontWeight: 500 }}>CB-7120</Link>
                  <span className="badge badge-danger">Lost</span>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Reason 10.4 • 84% similarity</p>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
