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
  return (
    <div className="card kpi-card">
      <div className="kpi-header">
        <h3 className="kpi-title">{title}</h3>
        <div className="kpi-icon" style={{ backgroundColor: `${color}20`, color }}>
          <Icon size={20} />
        </div>
      </div>
      <div className="kpi-body">
        <div className="kpi-value">{value}</div>
        {change && (
          <div className={`kpi-change trend-${trend}`}>
            {trend === 'up' && '↑ '}
            {trend === 'down' && '↓ '}
            {change}
          </div>
        )}
      </div>
    </div>
  );
}
