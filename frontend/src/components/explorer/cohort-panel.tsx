"use client";

import { AlertCircle, Filter, Layers3, MapPinned, Table2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  CohortExplorerResponse,
  CohortRequest,
  FixedChartSeries,
} from "@/types/api";
import { SummaryCards } from "./summary-cards";
import { FixedCharts } from "./fixed-charts";
import { BreakdownChart } from "./breakdown-chart";
import { DrilldownTable } from "./drilldown-table";

type CohortPanelProps = {
  title: string;
  description: string;
  request: CohortRequest;
  onChange: (request: CohortRequest) => void;
  data: CohortExplorerResponse | null;
  loading?: boolean;
  error?: string | null;
  tone?: "primary" | "secondary";
};

const SOURCE_LABELS: Record<CohortRequest["source"], string> = {
  freddie_mac: "Freddie Mac",
  fannie_mae: "Fannie Mae",
};

const SNAPSHOT_PLACEHOLDERS: Record<CohortRequest["source"], string> = {
  freddie_mac: "2025Q3",
  fannie_mae: "202509",
};

const BREAKDOWN_DIMENSION_OPTIONS: Array<{ value: CohortRequest["breakdown_dimension"]; label: string }> = [
  { value: "state", label: "State" },
  { value: "property_type", label: "Property type" },
];

const BREAKDOWN_METRIC_OPTIONS: Array<{ value: CohortRequest["breakdown_metric"]; label: string }> = [
  { value: "loan_count", label: "Loan count" },
  { value: "current_upb_total", label: "Current UPB" },
  { value: "total_estimated_capital_amount", label: "Est. capital amount" },
];

function parseListInput(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatListInput(values: string[] | undefined) {
  return values?.join(", ") ?? "";
}

function cohortLabel(request: CohortRequest) {
  return `${SOURCE_LABELS[request.source]} ${request.snapshot}`;
}

function updateFilters(
  request: CohortRequest,
  key: "state" | "property_type",
  value: string
) {
  return {
    ...request,
    filters: {
      ...request.filters,
      [key]: parseListInput(value),
    },
  };
}

function SectionIcon({ icon: Icon }: { icon: typeof Layers3 }) {
  return <Icon className="h-4 w-4 text-muted-foreground" />;
}

export function CohortPanel({
  title,
  description,
  request,
  onChange,
  data,
  loading = false,
  error = null,
  tone = "primary",
}: CohortPanelProps) {
  const headerClassName =
    tone === "primary" ? "border-blue-100 bg-blue-50/60" : "border-emerald-100 bg-emerald-50/60";

  const updateRequest = (patch: Partial<CohortRequest>) => {
    onChange({ ...request, ...patch });
  };

  const updateSource = (source: CohortRequest["source"]) => {
    onChange({
      ...request,
      source,
    });
  };

  const chartData = data?.fixed_charts ?? ({} as Record<string, FixedChartSeries>);
  const breakdown = data?.breakdown ?? null;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
            {data ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                {data.cohort_label}
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-sm text-slate-600">{description}</p>
        </div>
        <div className={`rounded-full border px-3 py-1 text-xs font-medium ${headerClassName}`}>
          {cohortLabel(request)}
        </div>
      </div>

      <Card className={`shadow-sm ${tone === "primary" ? "border-blue-100" : "border-emerald-100"}`}>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Cohort controls</CardTitle>
          <CardDescription>
            Choose the source snapshot, narrow the cohort, and change the breakdown slice.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <SectionIcon icon={MapPinned} />
                Source
              </Label>
              <select
                className="h-8 w-full rounded-lg border border-input bg-background px-3 text-sm shadow-sm outline-none"
                value={request.source}
                onChange={(event) => updateSource(event.target.value as CohortRequest["source"])}
                disabled={loading}
              >
                {Object.entries(SOURCE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <SectionIcon icon={Layers3} />
                Snapshot key
              </Label>
              <Input
                placeholder={SNAPSHOT_PLACEHOLDERS[request.source]}
                value={request.snapshot}
                onChange={(event) => updateRequest({ snapshot: event.target.value })}
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                Freeform snapshot key. Example values are shown as placeholders, but any backend
                snapshot key can be entered.
              </p>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-2">
              <Label>State filter</Label>
              <Input
                placeholder="CA, TX"
                value={formatListInput(request.filters.state)}
                onChange={(event) => onChange(updateFilters(request, "state", event.target.value))}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Property type filter</Label>
              <Input
                placeholder="Multifamily, Seniors Housing"
                value={formatListInput(request.filters.property_type)}
                onChange={(event) =>
                  onChange(updateFilters(request, "property_type", event.target.value))
                }
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                Breakdown metric
              </Label>
              <select
                className="h-8 w-full rounded-lg border border-input bg-background px-3 text-sm shadow-sm outline-none"
                value={request.breakdown_metric}
                onChange={(event) =>
                  updateRequest({
                    breakdown_metric: event.target.value as CohortRequest["breakdown_metric"],
                  })
                }
                disabled={loading}
              >
                {BREAKDOWN_METRIC_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Breakdown dimension</Label>
              <select
                className="h-8 w-full rounded-lg border border-input bg-background px-3 text-sm shadow-sm outline-none"
                value={request.breakdown_dimension}
                onChange={(event) =>
                  updateRequest({
                    breakdown_dimension: event.target.value as CohortRequest["breakdown_dimension"],
                  })
                }
                disabled={loading}
              >
                {BREAKDOWN_DIMENSION_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end text-xs text-muted-foreground">
              Comma-separated filters keep the controls simple while still matching the backend
              cohort contract.
            </div>
          </div>
        </CardContent>
      </Card>

      {error ? (
        <Card className="border-destructive/30 bg-destructive/5 shadow-sm">
          <CardContent className="flex items-start gap-3 p-4 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </CardContent>
        </Card>
      ) : null}

      <Separator />

      <SummaryCards summary={data?.summary ?? null} loading={loading} />

      <FixedCharts fixedCharts={chartData} loading={loading} />

      <BreakdownChart breakdown={breakdown} loading={loading} />

      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <Table2 className="h-4 w-4 text-muted-foreground" />
          Drilldown
        </div>
        <DrilldownTable rows={data?.drilldown_rows ?? null} loading={loading} />
      </div>
    </section>
  );
}
