"use client";

import { useRef, useState } from "react";
import { AlertCircle, Check, ChevronDown, Layers3, MapPinned, Table2, X } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

const SNAPSHOT_OPTIONS: Record<CohortRequest["source"], Array<{ value: string; label: string }>> = {
  freddie_mac: [{ value: "2025Q3", label: "2025Q3" }],
  fannie_mae: [{ value: "202509", label: "202509" }],
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

const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DC","DE","FL","GA","HI","ID","IL","IN",
  "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH",
  "NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT",
  "VT","VA","WA","WV","WI","WY",
];

const PROPERTY_TYPES = [
  "Multifamily",
  "Seniors Housing",
  "Student Housing",
  "Manufactured Housing",
];

function cohortLabel(request: CohortRequest) {
  return `${SOURCE_LABELS[request.source]} ${request.snapshot}`;
}

function SectionIcon({ icon: Icon }: { icon: typeof Layers3 }) {
  return <Icon className="h-4 w-4 text-muted-foreground" />;
}

/* ─── Multi-select dropdown ──────────────────────────────────────────────── */

type MultiSelectProps = {
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
  placeholder: string;
  disabled?: boolean;
};

function MultiSelect({ options, selected, onChange, placeholder, disabled = false }: MultiSelectProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const toggle = (value: string) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value));
    } else {
      onChange([...selected, value]);
    }
  };

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        className="flex h-8 w-full items-center justify-between rounded-lg border border-input bg-background px-3 text-sm shadow-sm outline-none disabled:cursor-not-allowed disabled:opacity-50"
        onClick={() => setOpen((o) => !o)}
        onBlur={(e) => {
          if (!containerRef.current?.contains(e.relatedTarget as Node)) setOpen(false);
        }}
        disabled={disabled}
      >
        <span className="truncate text-left">
          {selected.length === 0 ? (
            <span className="text-muted-foreground">{placeholder}</span>
          ) : (
            <span className="flex items-center gap-1 overflow-hidden">
              {selected.slice(0, 3).map((v) => (
                <span key={v} className="inline-flex items-center gap-0.5 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-700">
                  {v}
                </span>
              ))}
              {selected.length > 3 && (
                <span className="text-xs text-muted-foreground">+{selected.length - 3}</span>
              )}
            </span>
          )}
        </span>
        <span className="flex items-center gap-1 shrink-0">
          {selected.length > 0 && (
            <span
              role="button"
              tabIndex={0}
              className="rounded-full p-0.5 hover:bg-muted"
              onMouseDown={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onChange([]);
              }}
            >
              <X className="h-3 w-3 text-muted-foreground" />
            </span>
          )}
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </span>
      </button>

      {open && (
        <div
          className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-lg border border-slate-200 bg-white p-1 shadow-lg"
          onMouseDown={(e) => e.preventDefault()}
        >
          {options.map((option) => {
            const isSelected = selected.includes(option);
            return (
              <button
                key={option}
                type="button"
                className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${
                  isSelected ? "bg-slate-100 font-medium" : "hover:bg-muted"
                }`}
                onClick={() => toggle(option)}
              >
                <span className={`flex h-4 w-4 items-center justify-center rounded border ${
                  isSelected ? "border-blue-600 bg-blue-600 text-white" : "border-input"
                }`}>
                  {isSelected && <Check className="h-3 w-3" />}
                </span>
                {option}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── Cohort panel ───────────────────────────────────────────────────────── */

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
  const snapshotOptions = SNAPSHOT_OPTIONS[request.source];
  const headerClassName =
    tone === "primary" ? "border-blue-100 bg-blue-50/60" : "border-emerald-100 bg-emerald-50/60";

  const updateRequest = (patch: Partial<CohortRequest>) => {
    onChange({ ...request, ...patch });
  };

  const updateSource = (source: CohortRequest["source"]) => {
    const nextSnapshot = SNAPSHOT_OPTIONS[source][0]?.value ?? request.snapshot;
    onChange({
      ...request,
      source,
      snapshot: nextSnapshot,
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

      <Card className={`overflow-visible shadow-sm ${tone === "primary" ? "border-blue-100" : "border-emerald-100"}`}>
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
                Snapshot
              </Label>
              <select
                className="h-8 w-full rounded-lg border border-input bg-background px-3 text-sm shadow-sm outline-none"
                value={request.snapshot}
                onChange={(event) => updateRequest({ snapshot: event.target.value })}
                disabled={loading}
              >
                {snapshotOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label>State filter</Label>
              <MultiSelect
                options={US_STATES}
                selected={(request.filters.state as string[]) ?? []}
                onChange={(next) =>
                  onChange({ ...request, filters: { ...request.filters, state: next } })
                }
                placeholder="All states"
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label>Property type filter</Label>
              <MultiSelect
                options={PROPERTY_TYPES}
                selected={(request.filters.property_type as string[]) ?? []}
                onChange={(next) =>
                  onChange({ ...request, filters: { ...request.filters, property_type: next } })
                }
                placeholder="All types"
                disabled={loading}
              />
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

      {tone === "primary" && (
        <div className="flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
          <div className="flex items-center gap-2">
            <Label className="text-xs font-medium text-slate-600 whitespace-nowrap">Dimension</Label>
            <select
              className="h-7 rounded-md border border-input bg-background px-2 text-xs shadow-sm outline-none"
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
          <div className="flex items-center gap-2">
            <Label className="text-xs font-medium text-slate-600 whitespace-nowrap">Metric</Label>
            <select
              className="h-7 rounded-md border border-input bg-background px-2 text-xs shadow-sm outline-none"
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
      )}

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
