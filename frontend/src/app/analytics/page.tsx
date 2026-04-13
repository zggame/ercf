"use client";

import axios from "axios";
import { useEffect, useState } from "react";
import { AlertCircle, ArrowRightLeft, ChartColumn, Layers3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { CompareDeltaCards } from "@/components/explorer/compare-delta-cards";
import { CohortPanel } from "@/components/explorer/cohort-panel";
import type {
  CohortExplorerResponse,
  CohortRequest,
  CompareResponse,
} from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PRIMARY_DEFAULT: CohortRequest = {
  source: "freddie_mac",
  snapshot: "2025Q3",
  filters: {
    state: [],
    property_type: [],
  },
  breakdown_dimension: "state",
  breakdown_metric: "current_upb_total",
};

const COMPARE_DEFAULT: CohortRequest = {
  source: "fannie_mae",
  snapshot: "202509",
  filters: {
    state: [],
    property_type: [],
  },
  breakdown_dimension: "state",
  breakdown_metric: "current_upb_total",
};

function extractErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return "The explorer request was rejected by the backend.";
    }
  }

  return error instanceof Error ? error.message : "Unable to load the dataset explorer.";
}

export default function AnalyticsPage() {
  const [compareEnabled, setCompareEnabled] = useState(false);
  const [primaryRequest, setPrimaryRequest] = useState<CohortRequest>(PRIMARY_DEFAULT);
  const [compareRequest, setCompareRequest] = useState<CohortRequest>(COMPARE_DEFAULT);
  const [primaryData, setPrimaryData] = useState<CohortExplorerResponse | null>(null);
  const [compareData, setCompareData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const requestSignature = JSON.stringify({
    compareEnabled,
    primaryRequest,
    compareRequest,
  });

  useEffect(() => {
    let cancelled = false;

    const loadExplorer = async () => {
      setLoading(true);
      setError(null);

      try {
        if (compareEnabled) {
          const response = await axios.post<CompareResponse>(
            `${API_URL}/api/explorer/compare`,
            {
              left: primaryRequest,
              right: compareRequest,
            }
          );

          if (cancelled) {
            return;
          }

          setCompareData(response.data);
          setPrimaryData(response.data.left);
        } else {
          const response = await axios.post<CohortExplorerResponse>(
            `${API_URL}/api/explorer/cohort`,
            primaryRequest
          );

          if (cancelled) {
            return;
          }

          setPrimaryData(response.data);
          setCompareData(null);
        }
      } catch (requestError) {
        if (cancelled) {
          return;
        }

        setPrimaryData(null);
        setCompareData(null);
        setError(extractErrorMessage(requestError));
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    const timeout = window.setTimeout(loadExplorer, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timeout);
    };
  }, [requestSignature, compareEnabled, compareRequest, primaryRequest]);

  const panelGridClassName = compareEnabled
    ? "grid grid-cols-1 gap-6 xl:grid-cols-2"
    : "grid grid-cols-1 gap-6";

  const primaryPanelData = compareEnabled ? compareData?.left ?? null : primaryData;
  const secondaryPanelData = compareEnabled ? compareData?.right ?? null : null;

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-6">
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
              <Layers3 className="h-3.5 w-3.5" />
              Dataset Explorer
            </div>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                Cohort explorer with an optional compare panel
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                Explore curated Freddie Mac and Fannie Mae cohorts, inspect the fixed chart set,
                and switch on compare mode when you want symmetric side-by-side analysis.
              </p>
            </div>
          </div>

          <Button
            type="button"
            variant={compareEnabled ? "secondary" : "outline"}
            className="gap-2"
            onClick={() => setCompareEnabled((current) => !current)}
          >
            <ArrowRightLeft className="h-4 w-4" />
            {compareEnabled ? "Hide compare" : "Enable compare"}
          </Button>
        </div>

        <Separator className="my-5" />

        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-slate-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                <ChartColumn className="h-4 w-4" />
                Explorer scope
              </div>
              <p className="mt-2 text-sm text-slate-700">
                Summary cards, fixed charts, one breakdown chart, and a drilldown table.
              </p>
            </CardContent>
          </Card>
          <Card className="border-slate-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                <Layers3 className="h-4 w-4" />
                Default cohort
              </div>
              <p className="mt-2 text-sm text-slate-700">
                Freddie Mac 2025Q3 is loaded first so the explorer opens with a single panel.
              </p>
            </CardContent>
          </Card>
          <Card className="border-slate-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                <ArrowRightLeft className="h-4 w-4" />
                Compare mode
              </div>
              <p className="mt-2 text-sm text-slate-700">
                The second panel stays hidden until you enable compare.
              </p>
            </CardContent>
          </Card>
        </div>

        {error ? (
          <Card className="mt-4 border-destructive/30 bg-destructive/5 shadow-sm">
            <CardContent className="flex items-start gap-3 p-4 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </CardContent>
          </Card>
        ) : null}

        {compareEnabled ? (
          <div className="mt-5">
            <CompareDeltaCards compare={compareData} loading={loading} />
          </div>
        ) : (
          <div className="mt-5 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            Compare mode is optional. Enable it to load a second cohort and surface the delta
            cards above the panels.
          </div>
        )}
      </section>

      <div className={panelGridClassName}>
        <CohortPanel
          title="Primary Cohort"
          description="The main explorer panel. Use it to inspect one curated dataset at a time."
          request={primaryRequest}
          onChange={setPrimaryRequest}
          data={primaryPanelData}
          loading={loading}
          error={error}
          tone="primary"
        />

        {compareEnabled ? (
          <CohortPanel
            title="Comparison Cohort"
            description="Use the same controls to keep the two panels directly comparable."
            request={compareRequest}
            onChange={setCompareRequest}
            data={secondaryPanelData}
            loading={loading}
            error={error}
            tone="secondary"
          />
        ) : null}
      </div>
    </div>
  );
}
