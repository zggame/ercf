import Link from "next/link";
import { Building2, Calculator, LineChart, Database, FileText } from "lucide-react";

export function Sidebar() {
  return (
    <div className="w-64 h-full bg-slate-50 border-r border-slate-200 flex flex-col hidden md:flex">
      <div className="p-6 border-b border-slate-200">
        <Link href="/" className="flex items-center gap-2 text-slate-900 font-semibold text-lg">
          <Building2 className="w-6 h-6 text-blue-600" />
          <span>MF ERCF Explorer</span>
        </Link>
      </div>
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 mt-2">Main</div>
        <Link href="/" className="flex items-center gap-3 px-3 py-2 text-slate-700 rounded-md hover:bg-slate-100 transition-colors">
          <Building2 className="w-5 h-5 text-slate-500" />
          <span className="font-medium text-sm">Overview</span>
        </Link>
        <Link href="/calculator" className="flex items-center gap-3 px-3 py-2 text-slate-700 rounded-md hover:bg-slate-100 transition-colors">
          <Calculator className="w-5 h-5 text-slate-500" />
          <span className="font-medium text-sm">Single Loan Calculator</span>
        </Link>

        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 mt-8">Explorer</div>
        <Link href="/dataset" className="flex items-center gap-3 px-3 py-2 text-slate-700 rounded-md hover:bg-slate-100 transition-colors">
          <Database className="w-5 h-5 text-slate-500" />
          <span className="font-medium text-sm">Dataset Source</span>
        </Link>
        <Link href="/analytics" className="flex items-center gap-3 px-3 py-2 text-slate-700 rounded-md hover:bg-slate-100 transition-colors">
          <LineChart className="w-5 h-5 text-slate-500" />
          <span className="font-medium text-sm">Dataset Explorer</span>
        </Link>

        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 mt-8">Documentation</div>
        <Link href="/methodology" className="flex items-center gap-3 px-3 py-2 text-slate-700 rounded-md hover:bg-slate-100 transition-colors">
          <FileText className="w-5 h-5 text-slate-500" />
          <span className="font-medium text-sm">Methodology</span>
        </Link>
      </nav>
      <div className="p-4 border-t border-slate-200">
        <div className="text-xs text-slate-500">v1.0 Internal Tool</div>
      </div>
    </div>
  );
}
