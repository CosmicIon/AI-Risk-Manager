import KPICard from '@/components/dashboard/KPICard';
import { CostWeightedChart, CaseDistributionChart } from '@/components/charts/ClientCharts';
import { Briefcase, IndianRupee, ShieldAlert, Timer } from 'lucide-react';
import '../components/dashboard/dashboard.css';

export default function DashboardHome() {
  return (
    <div className="page-wrapper">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard Overview</h1>
          <p className="page-description">Real-time metrics and system health monitoring.</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-outline">Export Report</button>
          <button className="btn btn-primary">Refresh Data</button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="dashboard-grid">
        <KPICard
          title="Total Active Cases"
          value="1,248"
          change="12% from last week"
          trend="up"
          icon={Briefcase}
          color="var(--primary)"
        />
        <KPICard
          title="Chargeback Win Rate"
          value="82.4%"
          change="3.2% from last week"
          trend="up"
          icon={ShieldAlert}
          color="var(--success)"
        />
        <KPICard
          title="Total ₹ Saved"
          value="₹14.2M"
          change="₹1.2M this month"
          trend="up"
          icon={IndianRupee}
          color="var(--warning)"
        />
        <KPICard
          title="Pending Reviews"
          value="45"
          change="12 approaching deadline"
          trend="down"
          icon={Timer}
          color="var(--danger)"
        />
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Model Performance & Cost-Weighted Loss</h2>
            <p className="card-description">Tracking precision, recall, and total financial loss prevented.</p>
          </div>
          <div className="chart-container">
            <CostWeightedChart />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Case Distribution</h2>
            <p className="card-description">Active cases broken down by source.</p>
          </div>
          <div className="chart-container">
            <CaseDistributionChart />
          </div>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Recent Activity</h2>
          <p className="card-description">Latest alerts, model evaluations, and system updates.</p>
        </div>
        <div className="activity-feed">
          <div className="activity-item">
            <div className="activity-icon" style={{ backgroundColor: 'var(--danger-bg)', color: 'var(--danger)' }}>
              <ShieldAlert size={16} />
            </div>
            <div className="activity-content">
              <h4>Fraud Ring Detected</h4>
              <p>Abuse-Ring Sentinel identified a new community of 12 suspicious seller accounts.</p>
            </div>
            <div className="activity-time">10m ago</div>
          </div>
          <div className="activity-item">
            <div className="activity-icon" style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}>
              <Briefcase size={16} />
            </div>
            <div className="activity-content">
              <h4>Chargeback Case Won</h4>
              <p>Case #CB-9921 resolved in merchant's favor. ₹45,000 recovered.</p>
            </div>
            <div className="activity-time">1h ago</div>
          </div>
          <div className="activity-item">
            <div className="activity-icon" style={{ backgroundColor: 'var(--warning-bg)', color: 'var(--warning)' }}>
              <Timer size={16} />
            </div>
            <div className="activity-content">
              <h4>Deadline Approaching</h4>
              <p>5 chargeback cases require review within the next 24 hours.</p>
            </div>
            <div className="activity-time">3h ago</div>
          </div>
        </div>
      </div>
    </div>
  );
}
