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
import type { FixedChartSeries } from "@/types/api";

type FixedChartsProps = {
  fixedCharts: Record<string, FixedChartSeries> | null;
  loading?: boolean;
};

type ChartConfig = {
  key: string;
  title: string;
  description: string;
  barColor: string;
};

const CHARTS: ChartConfig[] = [
  {
    key: "capital_factor_bands",
    title: "Capital Factor Distribution",
    description: "Loan count by estimated capital factor band.",
    barColor: "#2563eb",
  },
  {
    key: "property_type_mix",
    title: "Property Type Mix",
    description: "Loan counts by property type.",
    barColor: "#0f766e",
  },
  {
    key: "state_mix",
    title: "State Mix",
    description: "Loan counts by state.",
    barColor: "#d97706",
  },
];

function emptyMessage(title: string) {
  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-5 text-sm text-muted-foreground">
        No rows match the current cohort filters.
      </CardContent>
    </Card>
  );
}

function ChartCard({ config, series }: { config: ChartConfig; series?: FixedChartSeries }) {
  if (!series || series.points.length === 0) {
    return emptyMessage(config.title);
  }

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{config.title}</CardTitle>
        <CardDescription>{config.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={series.points} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis
                dataKey="label"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: "#64748b" }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: "#64748b" }}
              />
              <Tooltip
                cursor={{ fill: "#f8fafc" }}
                contentStyle={{
                  borderRadius: 8,
                  border: "1px solid #e2e8f0",
                  boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                }}
              />
              <Bar dataKey="value" fill={config.barColor} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

export function FixedCharts({ fixedCharts, loading = false }: FixedChartsProps) {
  if (loading) {
    return (
      <div className="grid gap-4 xl:grid-cols-3">
        {CHARTS.map((config) => (
          <Card key={config.key} className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">{config.title}</CardTitle>
              <CardDescription>{config.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 rounded-xl bg-muted/50 animate-pulse" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {CHARTS.map((config) => (
        <ChartCard key={config.key} config={config} series={fixedCharts?.[config.key]} />
      ))}
    </div>
  );
}
