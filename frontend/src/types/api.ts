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
}

export interface PortfolioSummary {
  loan_count: number;
  original_upb_total: number;
  current_upb_total: number;
  wa_dscr: number;
  wa_ltv: number;
  wa_estimated_capital_factor: number;
  total_estimated_capital_amount: number;
}

export interface UploadResponse {
  status: "success" | "partial" | "error";
  mapped_records: number;
  failed_records: number;
  errors: Array<{ row: number; error: string }>;
}
