"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { CompareResponse } from "@/types/api";

type CompareDeltaCardsProps = {
  compare: CompareResponse | null;
  loading?: boolean;
};

type DeltaMetric = {
  key: keyof CompareResponse["deltas"];
  label: string;
  format: (value: number) => string;
};

const DELTA_METRICS: DeltaMetric[] = [
  { key: "loan_count", label: "Loan Count Delta", format: formatIntegerDelta },
  { key: "original_upb_total", label: "Original UPB Delta", format: formatMoneyDelta },
  { key: "current_upb_total", label: "Current UPB Delta", format: formatMoneyDelta },
  { key: "wa_dscr", label: "WA DSCR Delta", format: formatRatioDelta },
  { key: "wa_ltv", label: "WA LTV Delta", format: formatPercentDelta },
  {
    key: "wa_estimated_capital_factor",
    label: "WA Capital Factor Delta",
    format: formatPercentDelta,
  },
  {
    key: "total_estimated_capital_amount",
    label: "Est. Capital Delta",
    format: formatMoneyDelta,
  },
];

function formatIntegerDelta(value: number) {
  return `${value >= 0 ? "+" : "-"}${Math.abs(value).toLocaleString()}`;
}

function formatMoneyDelta(value: number) {
  return `${value >= 0 ? "+" : "-"}$${Math.round(Math.abs(value)).toLocaleString()}`;
}

function formatRatioDelta(value: number) {
  return `${value >= 0 ? "+" : "-"}${Math.abs(value).toFixed(2)}x`;
}

function formatPercentDelta(value: number) {
  return `${value >= 0 ? "+" : "-"}${(Math.abs(value) * 100).toFixed(1)}%`;
}

function DeltaSkeleton() {
  return (
    <Card size="sm" className="shadow-sm">
      <CardContent className="p-4">
        <div className="h-3 w-24 rounded-full bg-muted animate-pulse" />
        <div className="mt-3 h-6 w-20 rounded-md bg-muted animate-pulse" />
      </CardContent>
    </Card>
  );
}

export function CompareDeltaCards({ compare, loading = false }: CompareDeltaCardsProps) {
  if (loading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {DELTA_METRICS.map((metric) => (
          <DeltaSkeleton key={metric.key} />
        ))}
      </div>
    );
  }

  if (!compare) {
    return (
      <Card className="shadow-sm border-dashed">
        <CardContent className="p-5 text-sm text-muted-foreground">
          Enable compare mode to see cohort deltas.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">{compare.left.cohort_label}</span>
        <span>vs</span>
        <span className="font-medium text-foreground">{compare.right.cohort_label}</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {DELTA_METRICS.map((metric) => {
          const value = compare.deltas[metric.key];
          return (
            <Card key={metric.key} size="sm" className="shadow-sm">
              <CardContent className="p-4">
                <p className="text-xs font-medium text-muted-foreground">{metric.label}</p>
                <div className="mt-2 text-lg font-semibold text-foreground">
                  {metric.format(value)}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
