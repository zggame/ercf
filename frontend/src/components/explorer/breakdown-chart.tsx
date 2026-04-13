"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { BreakdownResponse } from "@/types/api";

type BreakdownChartProps = {
  breakdown: BreakdownResponse | null;
  loading?: boolean;
};

const DIMENSION_LABELS: Record<string, string> = {
  state: "State",
  property_type: "Property Type",
};

const METRIC_LABELS: Record<string, string> = {
  loan_count: "Loan Count",
  current_upb_total: "Current UPB",
  total_estimated_capital_amount: "Est. Capital Amount",
};

function formatValue(metric: string, value: number) {
  if (metric === "loan_count") {
    return value.toLocaleString();
  }

  return `$${(value / 1_000_000).toFixed(1)}M`;
}

export function BreakdownChart({ breakdown, loading = false }: BreakdownChartProps) {
  if (loading) {
    return (
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Breakdown</CardTitle>
          <CardDescription>Loading configurable breakdown...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-72 rounded-xl bg-muted/50 animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  if (!breakdown || breakdown.rows.length === 0) {
    return (
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Breakdown</CardTitle>
          <CardDescription>No rows match the selected dimension and metric.</CardDescription>
        </CardHeader>
        <CardContent className="p-5 text-sm text-muted-foreground">
          Adjust the breakdown controls to reveal a cohort slice.
        </CardContent>
      </Card>
    );
  }

  const dimensionLabel = DIMENSION_LABELS[breakdown.dimension] ?? breakdown.dimension;
  const metricLabel = METRIC_LABELS[breakdown.metric] ?? breakdown.metric;

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Breakdown by {dimensionLabel}</CardTitle>
        <CardDescription>{metricLabel} grouped by {dimensionLabel.toLowerCase()}.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={breakdown.rows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis
                dataKey="key"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: "#64748b" }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: "#64748b" }}
                tickFormatter={(value) => formatValue(breakdown.metric, value)}
              />
              <Tooltip
                cursor={{ fill: "#f8fafc" }}
                formatter={(value) => formatValue(breakdown.metric, Number(value))}
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #e2e8f0",
                  boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                }}
              />
              <Bar dataKey="value" fill="#7c3aed" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
