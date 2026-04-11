import { Bell, UserCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        {/* Mobile menu toggle could go here */}
        <h1 className="text-xl font-semibold text-slate-800 hidden sm:block">Executive Summary</h1>
      </div>
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="text-slate-500">
          <Bell className="w-5 h-5" />
        </Button>
        <div className="flex items-center gap-2 border-l pl-4 border-slate-200">
          <div className="text-sm text-right hidden sm:block">
            <p className="font-medium text-slate-700 leading-none">Strategy Team</p>
            <p className="text-slate-500 text-xs mt-1">Capital Markets</p>
          </div>
          <UserCircle className="w-8 h-8 text-slate-400" />
        </div>
      </div>
    </header>
  );
}
