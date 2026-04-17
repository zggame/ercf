import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DataAccessReferencePage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-12">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
          Reference Note
        </p>
        <h1 className="text-3xl font-semibold text-slate-900">GSE data access research</h1>
        <p className="text-sm leading-6 text-slate-600">
          This in-product note summarizes the access constraints documented during local research
          for the Freddie Mac and Fannie Mae multifamily datasets.
        </p>
      </div>

      <Card className="shadow-sm border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg">Key findings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-6 text-slate-600">
          <p>
            Freddie Mac does not expose a stable unauthenticated direct-download URL for the
            multifamily loan performance release used in this PoC.
          </p>
          <p>
            Fannie Mae access is also portal-gated and commonly depends on authenticated sessions
            or short-lived signed URLs.
          </p>
          <p>
            Because of those constraints, the deployed PoC is designed around curated offline
            artifacts built from local ZIP downloads rather than live downloads in production.
          </p>
        </CardContent>
      </Card>

      <Card className="shadow-sm border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg">Official source pages</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-6 text-slate-600">
          <p>
            Freddie Mac publishes the Multifamily Loan Performance Database through its{" "}
            <a
              href="https://mf.freddiemac.com/investors/performance-lookup"
              className="font-medium text-blue-700 underline underline-offset-4"
              target="_blank"
              rel="noreferrer"
            >
              Securities Performance &amp; Lookup
            </a>{" "}
            page. The MLPD section provides access to the database and the companion{" "}
            <a
              href="https://mf.freddiemac.com/docs/MLPD_data_dictionary.pdf"
              className="font-medium text-blue-700 underline underline-offset-4"
              target="_blank"
              rel="noreferrer"
            >
              data dictionary
            </a>
            , which describes the panel data and snapshot data releases.
          </p>
          <p>
            Fannie Mae publishes the Multifamily Loan Performance Data on{" "}
            <a
              href="https://capitalmarkets.fanniemae.com/credit-risk-transfer/multifamily-credit-risk-transfer/multifamily-loan-performance-data"
              className="font-medium text-blue-700 underline underline-offset-4"
              target="_blank"
              rel="noreferrer"
            >
              its Multifamily Loan Performance Data page
            </a>
            . That page states the dataset is accessible through{" "}
            <a
              href="https://capitalmarkets.fanniemae.com/tools-applications/data-dynamics"
              className="font-medium text-blue-700 underline underline-offset-4"
              target="_blank"
              rel="noreferrer"
            >
              Data Dynamics
            </a>
            , along with the supporting glossary and file-layout materials.
          </p>
        </CardContent>
      </Card>

      <Card className="shadow-sm border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg">Operational implication</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-6 text-slate-600">
          <p>
            The app can stay reliable for reviewers if dataset preparation happens offline and the
            deployed UI remains read-only.
          </p>
          <p>
            The existing dataset-management screen should be treated as an internal preparation
            surface, not a required reviewer workflow.
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
