export interface LoanInput {
  loan_id: string;
  source_system?: string;
  lender?: string;
  origination_date?: string;
  acquisition_date?: string;
  reporting_date?: string;
  original_upb: number;
  current_upb: number;
  note_rate?: number;
  amortization_term?: number;
  interest_only_term?: number;
  remaining_term?: number;
  maturity_date?: string;
  balloon_flag?: boolean;
  is_fixed_rate?: boolean;
  spread?: number;
  property_type: string;
  number_of_units?: number;
  occupancy_rate?: number;
  is_affordable: boolean;
  state?: string;
  msa?: string;
  dscr: number;
  ltv: number;
  debt_yield?: number;
  underwritten_noi?: number;
  valuation_amount?: number;
  delinquency_status?: string;

  // ERCF loan-level rule inputs (expanded contract; engine support comes later)
  original_loan_amount?: number;
  rate_type?: "fixed" | "arm";
  interest_only?: boolean;
  original_term_months?: number;
  amortization_term_months?: number;
  payment_performance?: string;
  government_subsidy_type?: "lihtc" | "pbra" | "section_515" | "state_local";
  qualifying_unit_share?: number;
  total_units?: number;
  qualifying_units?: number;
}

export interface EngineResult {
  loan_id: string;
  estimated_capital_factor: number;
  estimated_capital_amount: number;
  base_weight: number;
  ltv_multiplier: number;
  dscr_multiplier: number;
  property_multiplier: number;
  affordability_multiplier: number;
  data_quality_score: number;

  // ERCF loan-level rule outputs (expanded contract; engine support comes later)
  base_risk_weight: number | null;
  payment_performance_multiplier: number;
  interest_only_multiplier: number;
  term_multiplier: number;
  amortization_multiplier: number;
  loan_size_multiplier: number;
  special_product_multiplier: number;
  subsidy_multiplier: number;
  combined_multiplier: number;
  floor_value: number;
  floor_applied: boolean;

  confidence_score: number;
  confidence_threshold: number;
  missing_input_count: number;
  missing_inputs: string[];
  inferred_inputs: string[];
  confidence_notes: string[];
  result_available: boolean;

  final_risk_weight: number | null;
  capital_amount: number | null;
}

export interface LoanWithResult {
  loan: LoanInput;
  result: EngineResult;
}

export interface PortfolioSummary {
  loan_count: number;
  original_upb_total: number;
  current_upb_total: number;
  wa_dscr: number;
  wa_ltv: number;
  wa_estimated_capital_factor: number;
  total_estimated_capital_amount: number;
  loans_with_available_results: number;
  loans_with_missing_results: number;
  average_confidence_score: number;
  median_confidence_score: number;
  minimum_confidence_score: number;
  total_missing_input_count: number;
  missing_input_counts_by_field: Record<string, number>;
}

export interface UploadResponse {
  status: "success" | "partial" | "error";
  mapped_records: number;
  failed_records: number;
  errors: Array<{ row: number; error: string }>;
}

export interface CohortRequest {
  source: "freddie_mac" | "fannie_mae";
  snapshot: string;
  filters: Record<string, string[]>;
  breakdown_dimension: "state" | "property_type" | "rate_type" | "interest_only";
  breakdown_metric:
    | "loan_count"
    | "current_upb_total"
    | "total_estimated_capital_amount";
}

export interface CohortSummary {
  loan_count: number;
  original_upb_total: number;
  current_upb_total: number;
  wa_dscr: number;
  wa_ltv: number;
  wa_estimated_capital_factor: number;
  total_estimated_capital_amount: number;
}

export interface FixedChartPoint {
  label: string;
  value: number;
}

export interface FixedChartSeries {
  points: FixedChartPoint[];
}

export interface BreakdownRow {
  key: string;
  value: number;
}

export interface BreakdownResponse {
  dimension: string;
  metric: string;
  rows: BreakdownRow[];
}

export interface DrilldownRow {
  loan_id: string;
  source: string;
  reporting_date?: string;
  property_type?: string;
  state?: string;
  current_upb: number;
  dscr: number;
  ltv: number;
  estimated_capital_factor: number;
  estimated_capital_amount: number;
  note_rate?: number;
  original_term_months?: number;
  amortization_term_months?: number;
  interest_only_term?: number;
  interest_only?: boolean;
  rate_type?: string;
  is_fixed_rate?: boolean;
  payment_performance?: string;
  total_units?: number;
  occupancy_rate?: number;
  is_affordable?: boolean;
}

export interface CohortExplorerResponse {
  cohort_label: string;
  summary: CohortSummary;
  fixed_charts: Record<string, FixedChartSeries>;
  breakdown: BreakdownResponse;
  drilldown_rows: DrilldownRow[];
}

export interface CompareRequest {
  left: CohortRequest;
  right: CohortRequest;
}

export interface CohortComparisonDeltas {
  loan_count: number;
  original_upb_total: number;
  current_upb_total: number;
  wa_dscr: number;
  wa_ltv: number;
  wa_estimated_capital_factor: number;
  total_estimated_capital_amount: number;
}

export interface CompareResponse {
  left: CohortExplorerResponse;
  right: CohortExplorerResponse;
  deltas: CohortComparisonDeltas;
}
