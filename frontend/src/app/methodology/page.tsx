import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Info } from "lucide-react";

export default function MethodologyPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
        <div className="flex gap-3">
          <Info className="w-6 h-6 text-amber-600 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-semibold text-amber-900 mb-1">Analytical notice</h3>
            <p className="text-amber-800 text-sm leading-relaxed">
              This application is a multifamily ERCF-style PoC. It combines a stable loan-level
              calculator contract, curated Freddie Mac and Fannie Mae portfolio cohorts, and
              documented mapping assumptions. It is not an official regulatory filing engine.
            </p>
          </div>
        </div>
      </div>

      <section className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Current calculation path</h2>
          <p className="text-slate-600">
            The current PoC exposes the core multiplier trace that drives both the single-loan
            calculator and the curated explorer summaries.
          </p>
        </div>

        <Card className="shadow-sm border-slate-200">
          <CardHeader className="bg-slate-50 border-b border-slate-100">
            <CardTitle className="text-lg font-mono">Formula</CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="bg-slate-900 text-slate-50 p-4 rounded-lg font-mono text-sm overflow-x-auto">
              final_factor = base_weight * ltv_multiplier * dscr_multiplier * property_multiplier *
              affordability_multiplier
              <br />
              capital_amount = current_upb * final_factor
            </div>
            <p className="text-sm text-slate-600">
              The API stays stable around the current multiplier trace:
              <code className="ml-1 rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">
                base_weight
              </code>
              ,
              <code className="ml-1 rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">
                ltv_multiplier
              </code>
              ,
              <code className="ml-1 rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">
                dscr_multiplier
              </code>
              ,
              <code className="ml-1 rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">
                property_multiplier
              </code>
              , and
              <code className="ml-1 rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">
                affordability_multiplier
              </code>
              .
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Inputs and mapping</h3>
          <p className="text-slate-600">
            Freddie Mac and Fannie Mae expose similar business concepts through different raw field
            names. The PoC normalizes those concepts into one cohort contract for the explorer while
            keeping the loan-level calculator focused on the current core proxy inputs.
          </p>
        </div>

        <Card className="shadow-sm border-slate-200 overflow-hidden">
          <Table>
            <TableHeader className="bg-slate-50">
              <TableRow>
                <TableHead className="w-[180px]">Area</TableHead>
                <TableHead>What the PoC uses today</TableHead>
                <TableHead>Why it matters</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium align-top">Loan calculator</TableCell>
                <TableCell className="align-top">
                  Current UPB, original UPB, LTV, DSCR, property type, affordability flag, and
                  data-quality-sensitive optional fields.
                </TableCell>
                <TableCell className="align-top">
                  These drive the multiplier trace returned by
                  <code className="ml-1 rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">
                    /api/calculate
                  </code>
                  .
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium align-top">Curated explorer</TableCell>
                <TableCell className="align-top">
                  Source, snapshot, state, property type, current and original UPB, DSCR, LTV, and
                  estimated capital outputs for each curated cohort row.
                </TableCell>
                <TableCell className="align-top">
                  These fields power the summary cards, fixed charts, breakdown chart, compare
                  deltas, and drilldown table.
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium align-top">Source-specific adapters</TableCell>
                <TableCell className="align-top">
                  Freddie Mac and Fannie Mae are mapped independently before they enter the shared
                  cohort contract.
                </TableCell>
                <TableCell className="align-top">
                  The two GSE datasets are conceptually similar but structurally different, so one
                  raw parser is not enough.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Card>
      </section>

      <section className="space-y-4">
        <div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Deployment posture</h3>
          <p className="text-slate-600">
            The deployed reviewer experience is intended to be read-only and based on curated local
            artifacts. The compare panel in the explorer is part of that reviewer workflow. The
            dataset-management screen remains an internal preparation surface, not a required PoC
            path for reviewers.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4 border-b border-slate-100">
              <CardTitle className="text-base">Compare mode</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600">
              The explorer supports an optional compare panel for cohort-vs-cohort analysis. This
              methodology page describes the shared analytical framing behind those outputs rather
              than a separate alternate rule set.
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4 border-b border-slate-100">
              <CardTitle className="text-base">Curated artifacts</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600">
              The PoC is intended to run from prebuilt local snapshots so it does not depend on
              portal credentials, registration flows, or expiring signed URLs at runtime.
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="space-y-3">
        <h3 className="text-xl font-bold text-slate-900">References</h3>
        <div className="flex flex-col gap-3 text-sm">
          <Link
            href="/references/data-access"
            className="text-blue-700 underline underline-offset-4"
          >
            Data access research
          </Link>
          <Link
            href="/references/dataset-findings"
            className="text-blue-700 underline underline-offset-4"
          >
            Dataset findings
          </Link>
        </div>
      </section>
    </div>
  );
}
