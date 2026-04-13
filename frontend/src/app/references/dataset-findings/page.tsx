import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DatasetFindingsReferencePage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6 pb-12">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
          Reference Note
        </p>
        <h1 className="text-3xl font-semibold text-slate-900">GSE dataset findings</h1>
        <p className="text-sm leading-6 text-slate-600">
          This in-product note summarizes how the local Freddie Mac and Fannie Mae files are
          structured and what that means for the curated PoC datasets.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg">Freddie Mac</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-6 text-slate-600">
            <p>
              The Freddie ZIP is one logical panel dataset split across an older file and a newer
              file, with the same schema and overlapping loan IDs across time.
            </p>
            <p>
              For the PoC, recent-period analysis can rely on the newer window, while full
              historical analysis would require concatenating both files before any snapshot
              reduction.
            </p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg">Fannie Mae</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-6 text-slate-600">
            <p>
              The main multifamily file is the base canonical source. The separate DSCR file is a
              supplemental yearly enrichment table, not a duplicate of the main dataset.
            </p>
            <p>
              The main file already includes underwritten DSCR, which is sufficient for basic PoC
              mapping without requiring the annual DSCR table on day one.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-sm border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg">Cross-source implication</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-6 text-slate-600">
          <p>
            Freddie Mac and Fannie Mae share many business concepts, but not raw column names or
            release structure. The PoC therefore uses source-specific mapping into one canonical
            analytical shape.
          </p>
        </CardContent>
      </Card>

      <Link
        href="/methodology"
        className="inline-flex text-sm font-medium text-blue-700 underline underline-offset-4"
      >
        Back to methodology
      </Link>
    </div>
  );
}
