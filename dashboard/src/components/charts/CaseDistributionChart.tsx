'use client';

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend
} from 'recharts';

const data = [
  { name: 'Chargebacks', value: 45 },
  { name: 'Returns', value: 30 },
  { name: 'Fraud Alerts', value: 15 },
  { name: 'Abuse Rings', value: 10 },
];

const COLORS = ['#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function CaseDistributionChart() {
  return (
      <PieChart width={300} height={300}>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={5}
          dataKey="value"
          stroke="none"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip 
          contentStyle={{ backgroundColor: 'var(--surface-color)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
          itemStyle={{ color: 'var(--text-primary)' }}
        />
        <Legend wrapperStyle={{ fontSize: '12px' }} />
      </PieChart>
  );
}
