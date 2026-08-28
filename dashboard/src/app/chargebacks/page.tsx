import Link from 'next/link';
import { Filter, Search, SlidersHorizontal, ArrowUpDown } from 'lucide-react';

const MOCK_CHARGEBACKS = [
  { id: 'CB-9921', arn: '31525367890123456789012', amount: '₹45,000', reasonCode: '10.4', status: 'Requires Review', deadline: '24h', winProb: 88 },
  { id: 'CB-9922', arn: '31525367890123456789013', amount: '₹12,500', reasonCode: '10.4', status: 'Requires Review', deadline: '48h', winProb: 65 },
  { id: 'CB-9923', arn: '31525367890123456789014', amount: '₹8,200', reasonCode: '13.1', status: 'Requires Review', deadline: '3d', winProb: 92 },
  { id: 'CB-9924', arn: '31525367890123456789015', amount: '₹150,000', reasonCode: '10.4', status: 'Submitted', deadline: '5d', winProb: 75 },
  { id: 'CB-9925', arn: '31525367890123456789016', amount: '₹3,400', reasonCode: '13.1', status: 'Won', deadline: '-', winProb: 95 },
];

export default function ChargebacksPage() {
  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Chargebacks</h1>
          <p className="page-description">Manage and review active chargeback cases.</p>
        </div>
        <button className="btn btn-primary">Export CSV</button>
      </div>

      <div className="card">
        <div className="table-controls">
          <div className="search-box">
            <Search size={18} className="search-icon" />
            <input type="text" placeholder="Search ARN, Case ID..." className="input search-input-sm" />
          </div>
          <div className="flex gap-2">
            <button className="btn btn-outline"><Filter size={16} /> Status</button>
            <button className="btn btn-outline"><SlidersHorizontal size={16} /> More Filters</button>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Case ID</th>
                <th>ARN</th>
                <th>Amount</th>
                <th>Reason</th>
                <th>Win Prob</th>
                <th>Deadline <ArrowUpDown size={12} className="inline-icon" /></th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_CHARGEBACKS.map(cb => (
                <tr key={cb.id}>
                  <td className="font-medium text-primary">
                    <Link href={`/chargebacks/${cb.id}`}>{cb.id}</Link>
                  </td>
                  <td className="text-muted">{cb.arn}</td>
                  <td className="font-medium">{cb.amount}</td>
                  <td><span className="badge badge-neutral">{cb.reasonCode}</span></td>
                  <td>
                    <div className="prob-bar">
                      <div className="prob-fill" style={{ width: `${cb.winProb}%`, backgroundColor: cb.winProb > 80 ? 'var(--success)' : cb.winProb > 50 ? 'var(--warning)' : 'var(--danger)' }}></div>
                      <span>{cb.winProb}%</span>
                    </div>
                  </td>
                  <td>
                    <span className={cb.deadline.includes('h') ? 'text-danger font-bold' : ''}>
                      {cb.deadline}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${cb.status === 'Requires Review' ? 'badge-warning' : cb.status === 'Won' ? 'badge-success' : 'badge-neutral'}`}>
                      {cb.status}
                    </span>
                  </td>
                  <td>
                    <Link href={`/chargebacks/${cb.id}`} className="btn btn-outline btn-sm">Review</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
