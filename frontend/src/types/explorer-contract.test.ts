import type {
  CohortExplorerResponse,
  CohortRequest,
  CompareRequest,
  CompareResponse,
} from "@/types/api";

const primaryRequest: CohortRequest = {
  source: "freddie_mac",
  snapshot: "2025Q3",
  filters: {
    state: ["CA"],
    property_type: ["Multifamily"],
  },
  breakdown_dimension: "state",
  breakdown_metric: "current_upb_total",
};

const compareRequest: CompareRequest = {
  left: primaryRequest,
  right: {
    ...primaryRequest,
    source: "fannie_mae",
  },
};

const cohortResponse: CohortExplorerResponse = {
  cohort_label: "Freddie Mac 2025Q3",
  summary: {
    loan_count: 1,
    original_upb_total: 100,
    current_upb_total: 90,
    wa_dscr: 1.25,
    wa_ltv: 0.65,
    wa_estimated_capital_factor: 0.5,
    total_estimated_capital_amount: 45,
  },
  fixed_charts: {
    capital_factor_bands: {
      points: [{ label: "0.0-0.5", value: 1 }],
    },
  },
  breakdown: {
    dimension: "state",
    metric: "current_upb_total",
    rows: [{ key: "CA", value: 90 }],
  },
  drilldown_rows: [
    {
      loan_id: "FRE-1",
      source: "freddie_mac",
      reporting_date: "2025-09-30",
      property_type: "Multifamily",
      state: "CA",
      current_upb: 90,
      dscr: 1.25,
      ltv: 0.65,
      estimated_capital_factor: 0.5,
      estimated_capital_amount: 45,
    },
  ],
};

const compareResponse: CompareResponse = {
  left: cohortResponse,
  right: cohortResponse,
  deltas: {
    loan_count: 0,
    original_upb_total: 0,
    current_upb_total: 0,
    wa_dscr: 0,
    wa_ltv: 0,
    wa_estimated_capital_factor: 0,
    total_estimated_capital_amount: 0,
  },
};

void compareRequest;
void compareResponse;
