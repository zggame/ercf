import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Info } from "lucide-react";

export default function MethodologyPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div className="border-l-4 border-amber-500 bg-amber-50 p-6 rounded-r-lg">
        <div className="flex gap-3">
          <Info className="w-6 h-6 text-amber-600 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-semibold text-amber-900 mb-1">Important Analytical Notice</h3>
            <p className="text-amber-800 text-sm leading-relaxed">
              This tool provides an <strong>analytical approximation</strong> for multifamily ERCF-style capital analysis.
              It utilizes configurable proxies, estimated multipliers, and simplified risk-weight logic. It should not be treated as an official regulatory capital filing engine.
            </p>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Calculation Methodology</h2>
        <p className="text-slate-600 mb-6">Overview of how the proxy capital factor is derived from loan attributes.</p>

        <Card className="shadow-sm border-slate-200 mb-8">
          <CardHeader className="bg-slate-50 border-b border-slate-100">
            <CardTitle className="text-lg font-mono">Formula</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="bg-slate-900 text-slate-50 p-4 rounded-lg font-mono text-sm overflow-x-auto">
              Final Capital Factor = Base Weight × LTV Multiplier × DSCR Multiplier × Property Multiplier × Affordability Multiplier
              <br /><br />
              Capital Amount = Current UPB × Final Capital Factor
            </div>
          </CardContent>
        </Card>

        <h3 className="text-xl font-bold text-slate-900 mb-4">Assumption Thresholds (Configurable)</h3>
        <Card className="shadow-sm border-slate-200 overflow-hidden">
          <Table>
            <TableHeader className="bg-slate-50">
              <TableRow>
                <TableHead className="w-[200px]">Parameter</TableHead>
                <TableHead>Band / Condition</TableHead>
                <TableHead className="text-right">Multiplier</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium">Base Risk Weight</TableCell>
                <TableCell>Default Starting Value</TableCell>
                <TableCell className="text-right font-mono">0.50</TableCell>
              </TableRow>
              <TableRow>
                <TableCell rowSpan={5} className="font-medium align-top border-b">LTV Multiplier</TableCell>
                <TableCell>≤ 60%</TableCell>
                <TableCell className="text-right font-mono">0.80</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>60% - 70%</TableCell>
                <TableCell className="text-right font-mono">1.00</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>70% - 80%</TableCell>
                <TableCell className="text-right font-mono">1.20</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>80% - 100%</TableCell>
                <TableCell className="text-right font-mono">1.50</TableCell>
              </TableRow>
              <TableRow className="border-b">
                <TableCell>&gt; 100%</TableCell>
                <TableCell className="text-right font-mono">2.00</TableCell>
              </TableRow>
              <TableRow>
                <TableCell rowSpan={4} className="font-medium align-top border-b">DSCR Multiplier</TableCell>
                <TableCell>≤ 1.00x</TableCell>
                <TableCell className="text-right font-mono">1.50</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>1.00x - 1.25x</TableCell>
                <TableCell className="text-right font-mono">1.20</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>1.25x - 1.50x</TableCell>
                <TableCell className="text-right font-mono">1.00</TableCell>
              </TableRow>
              <TableRow className="border-b">
                <TableCell>&gt; 1.50x</TableCell>
                <TableCell className="text-right font-mono">0.80</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Property Type</TableCell>
                <TableCell>Seniors / Student / Manufactured</TableCell>
                <TableCell className="text-right font-mono">1.05 - 1.15</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Affordability</TableCell>
                <TableCell>Mission-Driven Flag = True</TableCell>
                <TableCell className="text-right font-mono">0.90</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </Card>
      </div>

      <div className="pt-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Data Quality & Inferences</h2>
        <p className="text-slate-600 mb-6">How public dataset mappings handle missing or proxy fields.</p>

        <div className="space-y-4">
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4">
              <CardTitle className="text-base">Inferred Fields</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              When exact regulatory fields (e.g., underwritten NOI, exact valuation date) are missing from public datasets, the engine relies on LTV and DSCR proxies provided in the dataset or calculated from current UPB and original value.
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4">
              <CardTitle className="text-base">Data Quality Score</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              A basic heuristic (0-100) assigned per loan. A score of 100 indicates all primary fields (UPB, LTV, DSCR, Property Type, Occupancy, Value) are present. Deductions occur for missing non-critical fields where default multipliers are applied.
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="pt-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Confidence Scoring & Result Suppression</h2>
        <p className="text-slate-600 mb-6">How the loan-level ERCF rule evaluates input completeness and suppresses uncertain results.</p>

        <div className="space-y-4">
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4">
              <CardTitle className="text-base">Confidence Score</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              The confidence score (0-100) reflects how many rule-critical loan inputs are present. 
              Missing fields such as rate_type, payment_performance, original_loan_amount, interest_only, 
              original_term_months, and amortization_term_months reduce the score by configured penalties.
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4">
              <CardTitle className="text-base">Result Suppression</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              When the confidence score falls below the configured threshold (default: 70), the loan-level 
              ERCF result is suppressed and marked unavailable. The legacy proxy results remain accessible 
              regardless of confidence. Subsidy treatment and floor logic only apply when results are available.
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4">
              <CardTitle className="text-base">Subsidy Multiplier</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              Loans with qualifying government subsidy types (LIHTC, Section 8, Section 515, etc.) receive 
              a subsidy multiplier based on the share of qualifying units. A 100% qualifying share yields 
              a 0.6 multiplier; partial shares scale proportionally.
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="py-4">
              <CardTitle className="text-base">Risk Weight Floor</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600">
              The loan-level ERCF rule enforces a minimum 20% risk weight floor. When the calculated 
              adjusted risk weight falls below this threshold, the floor is applied and flagged in the result.
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
