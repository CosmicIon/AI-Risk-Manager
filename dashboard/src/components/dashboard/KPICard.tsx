import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: LucideIcon;
  color?: string;
}

export default function KPICard({ title, value, change, trend, icon: Icon, color = 'var(--primary)' }: KPICardProps) {
  const trendArrow = trend === 'up' ? '▲' : trend === 'down' ? '▼' : '—';

  return (
    <div className="card kpi-card">
      <div className="kpi-header">
        <p className="kpi-title">{title}</p>
        <div
          className="kpi-icon"
          style={{
            backgroundColor: `${color}18`,
            border: `1px solid ${color}30`,
            color,
          }}
        >
          <Icon size={18} />
        </div>
      </div>
      <div className="kpi-body">
        <div className="kpi-value">{value}</div>
        {change && (
          <div className={`kpi-change trend-${trend}`}>
            <span>{trendArrow}</span>
            <span>{change}</span>
          </div>
        )}
      </div>
    </div>
  );
}
