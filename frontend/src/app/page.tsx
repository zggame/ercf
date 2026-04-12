import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Calculator, Database, ShieldAlert, LineChart } from "lucide-react";

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Hero Section */}
      <section className="bg-white rounded-2xl p-8 sm:p-12 border border-slate-200 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
          <LineChart className="w-64 h-64" />
        </div>
        <div className="relative z-10 max-w-2xl">
          <div className="inline-block px-3 py-1 mb-4 text-xs font-semibold text-blue-700 bg-blue-100 rounded-full">
            Internal Strategy Tool
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 mb-4">
            Multifamily ERCF <br/> Capital Analytics
          </h1>
          <p className="text-lg text-slate-600 mb-8">
            Calculate loan-level capital results and analyze public GSE multifamily portfolios using configurable FHFA ERCF-style methodology.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link href="/calculator">
              <Button size="lg" className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 shadow-sm gap-2">
                <Calculator className="w-4 h-4" />
                Analyze a Loan
              </Button>
            </Link>
            <Link href="/dataset">
              <Button size="lg" variant="outline" className="w-full sm:w-auto shadow-sm gap-2">
                <Database className="w-4 h-4" />
                Load Public Data
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="shadow-sm border-slate-200 transition-all hover:shadow-md">
          <CardHeader>
            <Calculator className="w-8 h-8 text-blue-600 mb-2" />
            <CardTitle>Single Loan Engine</CardTitle>
            <CardDescription>Evaluate individual multifamily assets</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600">
            Input detailed loan attributes including balance, LTV, DSCR, and property type to estimate ERCF-style capital requirements and view intermediate risk multipliers.
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200 transition-all hover:shadow-md">
          <CardHeader>
            <Database className="w-8 h-8 text-blue-600 mb-2" />
            <CardTitle>Portfolio Scaling</CardTitle>
            <CardDescription>GSE public dataset ingestion</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600">
            Load and map Fannie Mae and Freddie Mac multifamily loan performance datasets to a canonical schema for bulk capital calculation.
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200 transition-all hover:shadow-md">
          <CardHeader>
            <LineChart className="w-8 h-8 text-blue-600 mb-2" />
            <CardTitle>Analytics & Statistics</CardTitle>
            <CardDescription>Distributions and key observations</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600">
            Visualize capital factors across origination years, property types, and credit risk bands to identify strategic opportunities in the multifamily sector.
          </CardContent>
        </Card>
      </section>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-amber-800">
          <strong>Important notice:</strong> This application is an analytical approximation for multifamily ERCF-style capital analysis. It utilizes estimated proxies and configurable assumptions. It must not be treated as an official regulatory capital filing engine. See the <Link href="/methodology" className="underline font-medium">Methodology</Link> page for full details on field lineage and formula derivation.
        </div>
      </div>
    </div>
  );
}
