"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const data = [
  {
    name: "2021",
    Revenue: 3200000,
    EBITDA: 1200000,
    "Net Income": 800000,
  },
  {
    name: "2022",
    Revenue: 3800000,
    EBITDA: 1500000,
    "Net Income": 950000,
  },
  {
    name: "2023",
    Revenue: 4200000,
    EBITDA: 1800000,
    "Net Income": 1100000,
  },
];

const formatYAxis = (value) => {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value}`;
};

export function FinancialMetricsChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        margin={{
          top: 20,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis tickFormatter={formatYAxis} />
        <Tooltip
          formatter={(value) => [`$${(value / 1000000).toFixed(2)}M`, ""]}
          labelFormatter={(label) => `Year: ${label}`}
        />
        <Legend />
        <Bar dataKey="Revenue" fill="#8884d8" />
        <Bar dataKey="EBITDA" fill="#82ca9d" />
        <Bar dataKey="Net Income" fill="#ffc658" />
      </BarChart>
    </ResponsiveContainer>
  );
}