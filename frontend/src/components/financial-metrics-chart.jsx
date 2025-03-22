import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export const FinancialMetricsChart = ({ data = [] }) => {
  // If no data is provided, use placeholder data
  const chartData =
    data && data.length > 0
      ? data
      : [
          {
            year: 2021,
            revenue: 10000000,
            ebitda: 1500000,
            netIncome: 800000,
          },
          {
            year: 2022,
            revenue: 11000000,
            ebitda: 1800000,
            netIncome: 900000,
          },
          {
            year: 2023,
            revenue: 12000000,
            ebitda: 2200000,
            netIncome: 1100000,
          },
        ];

  // Format the values to show in millions or thousands
  const formatYAxis = (value) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value;
  };

  const formatTooltip = (value) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(2)}K`;
    }
    return `$${value}`;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={chartData}
        margin={{
          top: 20,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="year" />
        <YAxis tickFormatter={formatYAxis} />
        <Tooltip
          formatter={(value, name) => {
            return [formatTooltip(value), name];
          }}
        />
        <Legend />
        <Bar dataKey="revenue" name="Revenue" fill="#2563EB" />
        <Bar dataKey="ebitda" name="EBITDA" fill="#10B981" />
        <Bar dataKey="netIncome" name="Net Income" fill="#F59E0B" />
      </BarChart>
    </ResponsiveContainer>
  );
};
