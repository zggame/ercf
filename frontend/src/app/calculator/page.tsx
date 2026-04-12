"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Calculator as CalcIcon, AlertCircle, TrendingUp, DollarSign } from "lucide-react";
import axios from "axios";
import type { EngineResult } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CalculatorPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EngineResult | null>(null);

  const [formData, setFormData] = useState({
    loan_id: "LOAN-1001",
    original_upb: 10000000,
    current_upb: 9500000,
    property_type: "Multifamily",
    dscr: 1.35,
    ltv: 0.65,
    is_affordable: false,
    state: "NY"
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const value = e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value;
    setFormData({ ...formData, [e.target.name]: value });
  };

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const payload = {
        ...formData,
        original_upb: Number(formData.original_upb),
        current_upb: Number(formData.current_upb),
        dscr: Number(formData.dscr),
        ltv: Number(formData.ltv)
      };
      const res = await axios.post<EngineResult>(`${API_URL}/api/calculate`, payload);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Failed to calculate.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
      {/* Left: Input Form */}
      <div className="lg:col-span-5 space-y-6">
        <Card className="shadow-sm border-slate-200">
          <CardHeader className="bg-slate-50 border-b border-slate-100">
            <CardTitle className="flex items-center gap-2">
              <CalcIcon className="w-5 h-5 text-blue-600" />
              Loan Attributes
            </CardTitle>
            <CardDescription>Input multifamily metrics to estimate capital</CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="loan_id">Loan ID</Label>
              <Input id="loan_id" name="loan_id" value={formData.loan_id} onChange={handleChange} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="original_upb">Original UPB ($)</Label>
                <Input id="original_upb" name="original_upb" type="number" value={formData.original_upb} onChange={handleChange} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="current_upb">Current UPB ($)</Label>
                <Input id="current_upb" name="current_upb" type="number" value={formData.current_upb} onChange={handleChange} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="ltv">LTV (Decimal)</Label>
                <Input id="ltv" name="ltv" type="number" step="0.01" value={formData.ltv} onChange={handleChange} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="dscr">DSCR</Label>
                <Input id="dscr" name="dscr" type="number" step="0.01" value={formData.dscr} onChange={handleChange} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="property_type">Property Type</Label>
              <select
                id="property_type"
                name="property_type"
                value={formData.property_type}
                onChange={handleChange}
                className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2"
              >
                <option value="Multifamily">Multifamily</option>
                <option value="Seniors Housing">Seniors Housing</option>
                <option value="Student Housing">Student Housing</option>
                <option value="Manufactured Housing">Manufactured Housing</option>
              </select>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="is_affordable"
                name="is_affordable"
                checked={formData.is_affordable}
                onChange={handleChange}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-600"
              />
              <Label htmlFor="is_affordable" className="font-normal cursor-pointer">Affordable / Mission-Driven Flag</Label>
            </div>
          </CardContent>
          <CardFooter className="bg-slate-50 border-t border-slate-100 p-4">
            <Button className="w-full bg-blue-600 hover:bg-blue-700" onClick={handleCalculate} disabled={loading}>
              {loading ? "Calculating..." : "Run Capital Engine"}
            </Button>
          </CardFooter>
        </Card>
      </div>

      {/* Right: Results Summary */}
      <div className="lg:col-span-7 space-y-6">
        {result ? (
          <>
            <Card className="shadow-sm border-slate-200 bg-gradient-to-br from-white to-slate-50">
              <CardHeader>
                <CardTitle className="text-xl">Calculation Results</CardTitle>
                <CardDescription>Estimated ERCF proxy metrics for {result.loan_id}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-6 mb-8">
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
                    <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                      <TrendingUp className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-500 font-medium">Estimated Capital Factor</p>
                      <p className="text-3xl font-bold text-slate-900 mt-1">
                        {(result.estimated_capital_factor * 100).toFixed(2)}%
                      </p>
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
                    <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                      <DollarSign className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-500 font-medium">Capital Amount</p>
                      <p className="text-3xl font-bold text-slate-900 mt-1">
                        ${result.estimated_capital_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </p>
                    </div>
                  </div>
                </div>

                <Separator className="my-6" />

                <h4 className="font-semibold text-slate-800 mb-4">Risk Multiplier Trace</h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-600">Base Risk Weight</span>
                    <span className="font-mono font-medium">{result.base_weight.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-600">LTV Multiplier</span>
                    <span className="font-mono font-medium">{result.ltv_multiplier.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-600">DSCR Multiplier</span>
                    <span className="font-mono font-medium">{result.dscr_multiplier.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-600">Property Type Multiplier</span>
                    <span className="font-mono font-medium">{result.property_multiplier.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-600">Affordability Multiplier</span>
                    <span className="font-mono font-medium">{result.affordability_multiplier.toFixed(2)}</span>
                  </div>
                </div>

                <div className="mt-8 p-4 bg-amber-50 rounded-lg border border-amber-200 flex gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                  <div>
                    <h5 className="text-sm font-semibold text-amber-800">Data Quality Score: {result.data_quality_score}/100</h5>
                    <p className="text-xs text-amber-700 mt-1">Some optional inputs (e.g., occupancy rate, valuation amount) are missing. This relies on engine defaults.</p>
                  </div>
                </div>

                {!result.result_available && (
                  <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200 flex gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                    <div>
                      <h5 className="text-sm font-semibold text-red-800">ERCF Rule Result Unavailable</h5>
                      <p className="text-xs text-red-700 mt-1">
                        Confidence score ({result.confidence_score}) is below the threshold ({result.confidence_threshold}). 
                        Missing inputs: {result.missing_inputs.join(", ") || "none"}.
                      </p>
                    </div>
                  </div>
                )}

                {result.result_available && result.final_risk_weight !== null && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h5 className="text-sm font-semibold text-blue-800">Loan-Level ERCF Result</h5>
                    <div className="mt-2 flex justify-between items-center">
                      <span className="text-xs text-blue-700">Final Risk Weight</span>
                      <span className="text-lg font-bold text-blue-900">{(result.final_risk_weight * 100).toFixed(2)}%</span>
                    </div>
                    {result.floor_applied && (
                      <p className="text-xs text-blue-700 mt-1">Floor applied (minimum 20% risk weight)</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : (
          <div className="h-full min-h-[400px] flex items-center justify-center border-2 border-dashed border-slate-200 rounded-xl bg-slate-50">
            <div className="text-center text-slate-500 max-w-sm">
              <CalcIcon className="w-12 h-12 mx-auto text-slate-300 mb-4" />
              <p>Fill out the loan attributes and run the capital engine to view the ERCF proxy results.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
