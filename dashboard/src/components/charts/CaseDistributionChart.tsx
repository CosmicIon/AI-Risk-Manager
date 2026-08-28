'use client';

import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const data = [
  { name: 'Chargebacks', value: 45 },
  { name: 'Returns',     value: 30 },
  { name: 'Fraud Alerts', value: 15 },
  { name: 'Abuse Rings', value: 10 },
];

const COLORS = ['#4f7cff', '#fbbf24', '#f87171', '#a78bfa'];

const tooltipStyle = {
  backgroundColor: '#0f0f14',
  border: '1px solid #1e1e2e',
  borderRadius: '8px',
  fontSize: '0.8125rem',
};

export default function CaseDistributionChart() {
  return (
    <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
      <PieChart width={300} height={280}>
        <Pie
          data={data}
          cx="50%"
          cy="44%"
          innerRadius={68}
          outerRadius={100}
          paddingAngle={4}
          dataKey="value"
          stroke="none"
        >
          {data.map((_, index) => (
            <Cell
              key={`cell-${index}`}
              fill={COLORS[index % COLORS.length]}
              style={{ filter: `drop-shadow(0 0 4px ${COLORS[index % COLORS.length]}66)` }}
            />
          ))}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: '#f0f0fa' }} />
        <Legend
          wrapperStyle={{ fontSize: '11px', color: '#8888aa', paddingTop: '4px' }}
          iconSize={8}
          iconType="circle"
        />
      </PieChart>
    </div>
  );
}
