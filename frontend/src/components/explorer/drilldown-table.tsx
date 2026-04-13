"use client";

import { useState } from "react";
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Search } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { DrilldownRow } from "@/types/api";

type DrilldownTableProps = {
  rows: DrilldownRow[] | null;
  loading?: boolean;
};

type SortKey = "loan_id" | "state" | "current_upb" | "estimated_capital_factor" | "estimated_capital_amount";
type SortDirection = "asc" | "desc";

const PAGE_SIZE = 25;

const SORT_LABELS: Record<SortKey, string> = {
  loan_id: "Loan ID",
  state: "State",
  current_upb: "Current UPB",
  estimated_capital_factor: "Capital Factor",
  estimated_capital_amount: "Capital Amount",
};

function matchesQuery(row: DrilldownRow, query: string) {
  const haystack = [
    row.loan_id,
    row.source,
    row.reporting_date ?? "",
    row.property_type ?? "",
    row.state ?? "",
    row.current_upb.toString(),
    row.dscr.toString(),
    row.ltv.toString(),
    row.estimated_capital_factor.toString(),
    row.estimated_capital_amount.toString(),
  ]
    .join(" ")
    .toLowerCase();

  return haystack.includes(query);
}

function sortRows(rows: DrilldownRow[], sortKey: SortKey, sortDirection: SortDirection) {
  const direction = sortDirection === "asc" ? 1 : -1;
  return [...rows].sort((left, right) => {
    let comparison = 0;

    if (sortKey === "loan_id" || sortKey === "state") {
      comparison = (left[sortKey] ?? "").localeCompare(right[sortKey] ?? "");
    } else {
      comparison = left[sortKey] - right[sortKey];
    }

    return comparison * direction;
  });
}

function formatDollars(value: number) {
  return `$${Math.round(value).toLocaleString()}`;
}

export function DrilldownTable({ rows, loading = false }: DrilldownTableProps) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("current_upb");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [page, setPage] = useState(0);

  const filteredRows = (rows ?? []).filter((row) => matchesQuery(row, query.trim().toLowerCase()));
  const sortedRows = sortRows(filteredRows, sortKey, sortDirection);

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const visibleRows = sortedRows.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

  const handleQueryChange = (value: string) => {
    setQuery(value);
    setPage(0);
  };

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Drilldown Table</CardTitle>
        <CardDescription>
          Search and sort the loan-level records behind the charts.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Search loan id, state, property type, or source"
              value={query}
              onChange={(event) => handleQueryChange(event.target.value)}
              disabled={loading}
            />
          </div>
          <select
            className="h-8 rounded-lg border border-input bg-background px-3 text-sm text-foreground shadow-sm outline-none disabled:cursor-not-allowed disabled:opacity-50"
            value={sortKey}
            onChange={(event) => setSortKey(event.target.value as SortKey)}
            disabled={loading}
          >
            {Object.entries(SORT_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                Sort by {label}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="inline-flex h-8 items-center justify-center gap-2 rounded-lg border border-input bg-background px-3 text-sm font-medium shadow-sm transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
            onClick={() =>
              setSortDirection((current) => (current === "asc" ? "desc" : "asc"))
            }
            disabled={loading}
          >
            {sortDirection === "asc" ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {sortDirection === "asc" ? "Ascending" : "Descending"}
          </button>
        </div>

        <div className="rounded-xl border border-border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Loan ID</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Report Date</TableHead>
                <TableHead>Property Type</TableHead>
                <TableHead>State</TableHead>
                <TableHead className="text-right">Current UPB</TableHead>
                <TableHead className="text-right">DSCR</TableHead>
                <TableHead className="text-right">LTV</TableHead>
                <TableHead className="text-right">Cap. Factor</TableHead>
                <TableHead className="text-right">Cap. Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={10} className="py-8 text-center text-sm text-muted-foreground">
                    Loading drilldown records...
                  </TableCell>
                </TableRow>
              ) : visibleRows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="py-8 text-center text-sm text-muted-foreground">
                    No drilldown rows match the current search.
                  </TableCell>
                </TableRow>
              ) : (
                visibleRows.map((row) => (
                  <TableRow key={row.loan_id}>
                    <TableCell className="font-medium">{row.loan_id}</TableCell>
                    <TableCell>{row.source}</TableCell>
                    <TableCell>{row.reporting_date ?? "—"}</TableCell>
                    <TableCell>{row.property_type ?? "—"}</TableCell>
                    <TableCell>{row.state ?? "—"}</TableCell>
                    <TableCell className="text-right">{formatDollars(row.current_upb)}</TableCell>
                    <TableCell className="text-right">{row.dscr.toFixed(2)}x</TableCell>
                    <TableCell className="text-right">{(row.ltv * 100).toFixed(1)}%</TableCell>
                    <TableCell className="text-right">{(row.estimated_capital_factor * 100).toFixed(1)}%</TableCell>
                    <TableCell className="text-right">{formatDollars(row.estimated_capital_amount)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {sortedRows.length > 0 && (
          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-muted-foreground">
              Showing {safePage * PAGE_SIZE + 1}–{Math.min((safePage + 1) * PAGE_SIZE, sortedRows.length)} of{" "}
              {sortedRows.length.toLocaleString()} loans
            </p>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                className="h-7 w-7 p-0"
                disabled={safePage === 0}
                onClick={() => setPage(safePage - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="px-2 text-xs font-medium text-muted-foreground">
                {safePage + 1} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                className="h-7 w-7 p-0"
                disabled={safePage >= totalPages - 1}
                onClick={() => setPage(safePage + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
