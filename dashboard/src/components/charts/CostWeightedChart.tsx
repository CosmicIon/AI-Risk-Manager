'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
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

const tooltipStyle = {
  backgroundColor: '#0f0f14',
  border: '1px solid #1e1e2e',
  borderRadius: '8px',
  fontSize: '0.8125rem',
};

export default function CostWeightedChart() {
  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" vertical={false} />
          <XAxis
            dataKey="name"
            stroke="#55556a"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            dy={4}
          />
          <YAxis
            yAxisId="left"
            stroke="#55556a"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#55556a"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `₹${v / 1000}k`}
          />
          <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: '#f0f0fa' }} />
          <Legend
            wrapperStyle={{ fontSize: '11px', paddingTop: '12px', color: '#8888aa' }}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="precision"
            name="Precision"
            stroke="#4f7cff"
            strokeWidth={2}
            dot={{ r: 3, fill: '#4f7cff', strokeWidth: 0 }}
            activeDot={{ r: 5, strokeWidth: 0 }}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="recall"
            name="Recall"
            stroke="#34d399"
            strokeWidth={2}
            dot={{ r: 3, fill: '#34d399', strokeWidth: 0 }}
            activeDot={{ r: 5, strokeWidth: 0 }}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="loss"
            name="Cost-Weighted Loss"
            stroke="#f87171"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            activeDot={{ r: 5, strokeWidth: 0 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
