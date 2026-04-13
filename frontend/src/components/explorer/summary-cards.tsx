"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { CohortSummary } from "@/types/api";

type SummaryCardsProps = {
  summary: CohortSummary | null;
  loading?: boolean;
};

type MetricCard = {
  key: keyof CohortSummary;
  label: string;
  format: (value: number) => string;
  accent?: string;
};

const METRICS: MetricCard[] = [
  {
    key: "loan_count",
    label: "Loan Count",
    format: (value) => `${value.toLocaleString()}`,
  },
  {
    key: "original_upb_total",
    label: "Original UPB",
    format: formatMillions,
  },
  {
    key: "current_upb_total",
    label: "Current UPB",
    format: formatMillions,
  },
  {
    key: "wa_dscr",
    label: "WA DSCR",
    format: (value) => `${value.toFixed(2)}x`,
    accent: "text-sky-700",
  },
  {
    key: "wa_ltv",
    label: "WA LTV",
    format: (value) => `${(value * 100).toFixed(1)}%`,
    accent: "text-amber-700",
  },
  {
    key: "wa_estimated_capital_factor",
    label: "WA Capital Factor",
    format: (value) => `${(value * 100).toFixed(1)}%`,
    accent: "text-blue-700",
  },
  {
    key: "total_estimated_capital_amount",
    label: "Est. Total Capital",
    format: formatMillions,
    accent: "text-emerald-700",
  },
];

function formatMillions(value: number) {
  return `$${(value / 1_000_000).toFixed(1)}M`;
}

function SkeletonCard({ label }: { label: string }) {
  return (
    <Card size="sm" className="shadow-sm">
      <CardContent className="p-4">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <div className="mt-3 h-7 w-24 rounded-md bg-muted animate-pulse" />
      </CardContent>
    </Card>
  );
}

export function SummaryCards({ summary, loading = false }: SummaryCardsProps) {
  if (loading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {METRICS.map((metric) => (
          <SkeletonCard key={metric.key} label={metric.label} />
        ))}
      </div>
    );
  }

  if (!summary) {
    return (
      <Card className="shadow-sm border-dashed">
        <CardContent className="p-5 text-sm text-muted-foreground">
          No cohort data is loaded yet. Adjust the filters above to fetch a cohort.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {METRICS.map((metric) => {
        const value = summary[metric.key];
        return (
          <Card key={metric.key} size="sm" className="shadow-sm">
            <CardContent className="p-4">
              <p className="text-xs font-medium text-muted-foreground">{metric.label}</p>
              <div className={`mt-2 text-lg font-semibold ${metric.accent ?? "text-foreground"}`}>
                {metric.format(value)}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
