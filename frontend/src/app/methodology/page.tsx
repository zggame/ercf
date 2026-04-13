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
            <h3 className="text-lg font-semibold text-amber-900 mb-1">Refined-methodology notice</h3>
            <p className="text-amber-800 text-sm leading-relaxed">
              This PoC explains the refined ERCF-style loan trace only. It uses curated Freddie Mac and Fannie Mae datasets, source-specific field mapping, and documented caveats. It is not an official regulatory filing engine.
            </p>
          </div>
        </div>
      </div>

      <section className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Refined ERCF-Style Methodology</h2>
          <p className="text-slate-600">
            The calculator keeps a stable request and response contract, but the narrative on this page is intentionally scoped to the refined rule path. The result trace combines a source-aware base risk weight, additive multipliers, a confidence gate, and a floor on the final loan-level risk weight.
          </p>
        </div>

        <Card className="shadow-sm border-slate-200">
          <CardHeader className="bg-slate-50 border-b border-slate-100">
            <CardTitle className="text-lg font-mono">Refined flow</CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="bg-slate-900 text-slate-50 p-4 rounded-lg font-mono text-sm overflow-x-auto">
              final_risk_weight = max(base_risk_weight * combined_multiplier, floor_value)
              <br />
              capital_amount = current_upb * final_risk_weight
            </div>
            <p className="text-sm text-slate-600">
              If confidence falls below the configured threshold, the refined result is suppressed and the contract still returns the trace fields needed for debugging and review. The legacy capital-factor fields remain in the API for compatibility, but the product copy on this page stays centered on the refined ERCF-style logic.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Source-specific mapping</h3>
          <p className="text-slate-600">
            Freddie Mac and Fannie Mae expose similar loan concepts through different file layouts. The PoC uses source-specific adapters to normalize those fields into one canonical schema before the refined trace is computed.
          </p>
        </div>

        <Card className="shadow-sm border-slate-200 overflow-hidden">
          <Table>
            <TableHeader className="bg-slate-50">
              <TableRow>
                <TableHead className="w-[180px]">Source</TableHead>
                <TableHead>Canonical fields used</TableHead>
                <TableHead>Mapping notes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium align-top">Freddie Mac</TableCell>
                <TableCell className="align-top">
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">rate_dcr</code>,{" "}
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">rate_ltv</code>,{" "}
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">amt_upb_endg</code>,{" "}
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">code_st</code>, quartered panel rows
                </TableCell>
                <TableCell className="align-top">
                  The recent Freddie split-file release is treated as one curated panel, with the newer window preferred for current-period views and the older window retained when a historical panel is needed.
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium align-top">Fannie Mae</TableCell>
                <TableCell className="align-top">
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">Underwritten DSCR</code>,{" "}
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">Loan Acquisition LTV</code>,{" "}
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">UPB - Current</code>,{" "}
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">Original UPB</code>,{" "}
                  <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">Property State</code>
                </TableCell>
                <TableCell className="align-top">
                  The main multifamily file is the canonical source. The annual DSCR file is an optional enrichment table, not a launch dependency.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Card>
      </section>

      <section className="space-y-4">
        <div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Curated dataset inputs</h3>
          <p className="text-slate-600">
            The deployed PoC is designed around curated offline snapshots, not live portal ingestion. That keeps the review experience deterministic and avoids depending on credentials, expiring URLs, or registration flows at runtime.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4 border-b border-slate-100">
              <CardTitle className="text-base">Freddie Mac snapshot</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600 space-y-2">
              <p>Use the curated Freddie snapshot prepared from the local ZIP artifacts.</p>
              <p>The access research notes that the public download flow is form-gated and session-scoped, so the PoC should not rely on live downloads in the product runtime.</p>
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4 border-b border-slate-100">
              <CardTitle className="text-base">Fannie Mae snapshot</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600 space-y-2">
              <p>Use the curated Fannie main multifamily file as the base snapshot, with the supplemental DSCR file available only as enrichment.</p>
              <p>The research note documents authenticated portal access and short-lived signed URLs, which is why the deployed PoC stays read-only and offline.</p>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Caveats</h3>
          <p className="text-slate-600">
            The refined trace is intentionally opinionated. The caveats below explain where the PoC uses documented assumptions instead of source-native fields.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4 border-b border-slate-100">
              <CardTitle className="text-base">Confidence gating</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600">
              When rule-critical inputs are missing, the confidence score can suppress the refined result. The trace still exposes the missing and inferred inputs so reviewers can see why the result was withheld.
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4 border-b border-slate-100">
              <CardTitle className="text-base">Derived fields</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600">
              Some public fields map imperfectly to ERCF-style concepts. Where a source does not provide an exact match, the PoC uses the documented proxy or a canonicalized source-specific equivalent instead of inventing a new input.
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4 border-b border-slate-100">
              <CardTitle className="text-base">No comparison mode</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600">
              This page does not describe a base-vs-refined switch or compare workflow. The product semantics are refined-only.
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4 border-b border-slate-100">
              <CardTitle className="text-base">Read-only deployment</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600">
              The deployed PoC should not require portal credentials, upload workflows, or live dataset refreshes. Those mechanics stay in offline research and preparation steps.
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="space-y-3">
        <h3 className="text-xl font-bold text-slate-900">References</h3>
        <div className="flex flex-col gap-3 text-sm">
          <a href="/docs/gse-data/data-access-research.md" className="text-blue-700 underline underline-offset-4">
            Data access research
          </a>
          <a href="/docs/gse-data/dataset-findings.md" className="text-blue-700 underline underline-offset-4">
            Dataset findings
          </a>
        </div>
      </section>
    </div>
  );
}
