"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter, ZAxis } from "recharts";
import axios from "axios";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await axios.get("http://localhost:8000/api/portfolio/summary");
        setSummary(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  // Mock data for charts to make the UI look polished immediately
  const mockDistributionData = [
    { riskBand: "< 0.5", count: 45, avgCap: 0.4 },
    { riskBand: "0.5 - 0.7", count: 120, avgCap: 0.6 },
    { riskBand: "0.7 - 1.0", count: 80, avgCap: 0.85 },
    { riskBand: "1.0 - 1.5", count: 35, avgCap: 1.2 },
    { riskBand: "> 1.5", count: 15, avgCap: 1.8 },
  ];

  const mockScatterData = [
    { dscr: 1.1, ltv: 0.8, cap: 1.5 },
    { dscr: 1.3, ltv: 0.65, cap: 0.8 },
    { dscr: 1.5, ltv: 0.55, cap: 0.6 },
    { dscr: 1.2, ltv: 0.75, cap: 1.2 },
    { dscr: 1.8, ltv: 0.5, cap: 0.4 },
    { dscr: 1.05, ltv: 0.85, cap: 1.8 },
  ];

  if (loading) {
    return <div className="flex justify-center items-center h-full">Loading analytics...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Portfolio Analytics</h2>
          <p className="text-slate-600">Aggregated ERCF proxy results across loaded datasets</p>
        </div>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-slate-500">Total Loans</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-2">{summary?.loan_count || 0}</h3>
          </CardContent>
        </Card>
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-slate-500">Current UPB</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-2">
              ${((summary?.current_upb_total || 0) / 1000000).toFixed(1)}M
            </h3>
          </CardContent>
        </Card>
        <Card className="shadow-sm bg-blue-50 border-blue-100">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-blue-800">WA Capital Factor</p>
            <h3 className="text-2xl font-bold text-blue-900 mt-2">
              {((summary?.wa_estimated_capital_factor || 0) * 100).toFixed(2)}%
            </h3>
          </CardContent>
        </Card>
        <Card className="shadow-sm bg-emerald-50 border-emerald-100">
          <CardContent className="p-6">
            <p className="text-sm font-medium text-emerald-800">Est. Total Capital</p>
            <h3 className="text-2xl font-bold text-emerald-900 mt-2">
              ${((summary?.total_estimated_capital_amount || 0) / 1000000).toFixed(2)}M
            </h3>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="shadow-sm">
          <CardContent className="p-6 flex justify-between items-center">
            <span className="text-sm font-medium text-slate-500">WA DSCR</span>
            <span className="text-lg font-semibold">{summary?.wa_dscr?.toFixed(2) || "0.00"}x</span>
          </CardContent>
        </Card>
        <Card className="shadow-sm">
          <CardContent className="p-6 flex justify-between items-center">
            <span className="text-sm font-medium text-slate-500">WA LTV</span>
            <span className="text-lg font-semibold">{((summary?.wa_ltv || 0) * 100).toFixed(1)}%</span>
          </CardContent>
        </Card>
        <Card className="shadow-sm">
          <CardContent className="p-6 flex justify-between items-center">
            <span className="text-sm font-medium text-slate-500">Avg Cap per Loan</span>
            <span className="text-lg font-semibold">
              ${summary?.loan_count ? ((summary.total_estimated_capital_amount / summary.loan_count) / 1000).toFixed(1) : 0}k
            </span>
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <CardTitle>Capital Factor Distribution</CardTitle>
            <CardDescription>Loan count by estimated capital factor bands</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mockDistributionData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="riskBand" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <Tooltip
                    cursor={{fill: '#f1f5f9'}}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <CardTitle>DSCR vs LTV Risk Topography</CardTitle>
            <CardDescription>Bubble size represents estimated capital factor</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" dataKey="ltv" name="LTV" tickFormatter={(v) => `${(v*100).toFixed(0)}%`} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <YAxis type="number" dataKey="dscr" name="DSCR" tickFormatter={(v) => `${v}x`} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <ZAxis type="number" dataKey="cap" range={[50, 400]} name="Capital Factor" />
                  <Tooltip
                    cursor={{strokeDasharray: '3 3'}}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                  />
                  <Scatter name="Loans" data={mockScatterData} fill="#10b981" opacity={0.7} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
