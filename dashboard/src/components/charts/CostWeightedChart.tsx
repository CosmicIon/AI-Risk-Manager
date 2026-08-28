'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

const data = [
  { name: 'Mon', precision: 0.92, recall: 0.88, loss: 12000 },
  { name: 'Tue', precision: 0.93, recall: 0.89, loss: 10500 },
  { name: 'Wed', precision: 0.91, recall: 0.90, loss: 9800 },
  { name: 'Thu', precision: 0.94, recall: 0.91, loss: 8500 },
  { name: 'Fri', precision: 0.95, recall: 0.92, loss: 7200 },
  { name: 'Sat', precision: 0.96, recall: 0.93, loss: 6500 },
  { name: 'Sun', precision: 0.97, recall: 0.94, loss: 5100 },
];

export default function CostWeightedChart() {
  return (
      <LineChart width={600} height={300} data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
        <XAxis 
          dataKey="name" 
          stroke="var(--text-muted)" 
          fontSize={12} 
          tickLine={false}
          axisLine={false}
        />
        <YAxis 
          yAxisId="left" 
          stroke="var(--text-muted)" 
          fontSize={12} 
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
        />
        <YAxis 
          yAxisId="right" 
          orientation="right" 
          stroke="var(--text-muted)" 
          fontSize={12} 
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => `₹${value / 1000}k`}
        />
        <Tooltip 
          contentStyle={{ backgroundColor: 'var(--surface-color)', borderColor: 'var(--border-color)', borderRadius: '8px' }}
          itemStyle={{ color: 'var(--text-primary)' }}
        />
        <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
        <Line yAxisId="left" type="monotone" dataKey="precision" name="Precision" stroke="var(--primary)" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
        <Line yAxisId="left" type="monotone" dataKey="recall" name="Recall" stroke="var(--success)" strokeWidth={2} dot={{ r: 4 }} />
        <Line yAxisId="right" type="monotone" dataKey="loss" name="Cost-Weighted Loss" stroke="var(--danger)" strokeWidth={2} strokeDasharray="5 5" dot={false} />
      </LineChart>
  );
}
