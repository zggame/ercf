import re
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import date


class LoanInput(BaseModel):
    # Loan Identification
    loan_id: str
    source_system: Optional[str] = None
    lender: Optional[str] = None
    origination_date: Optional[date] = None
    acquisition_date: Optional[date] = None
    reporting_date: Optional[date] = None

    # Balance and Terms
    original_upb: float = Field(..., gt=0)
    current_upb: float = Field(..., ge=0)
    note_rate: Optional[float] = None
    amortization_term: Optional[int] = None
    interest_only_term: Optional[int] = None
    remaining_term: Optional[int] = None
    maturity_date: Optional[date] = None
    balloon_flag: Optional[bool] = None
    is_fixed_rate: Optional[bool] = True
    spread: Optional[float] = None

    # Property / Collateral
    property_type: str = "Multifamily"
    number_of_units: Optional[int] = None
    occupancy_rate: Optional[float] = None  # 0.0 to 1.0
    is_affordable: bool = False
    state: Optional[str] = None
    msa: Optional[str] = None

    # Credit and Underwriting
    dscr: float
    ltv: float  # 0.0 to 1.0
    debt_yield: Optional[float] = None
    underwritten_noi: Optional[float] = None
    valuation_amount: Optional[float] = None

    # ERCF loan-level rule inputs (expanded contract; engine support comes in later tasks)
    original_loan_amount: Optional[float] = Field(default=None, gt=0)
    rate_type: Optional[str] = None  # "fixed" | "arm"
    interest_only: Optional[bool] = None
    original_term_months: Optional[int] = Field(default=None, gt=0)
    amortization_term_months: Optional[int] = Field(default=None, gt=0)
    payment_performance: Optional[str] = None
    government_subsidy_type: Optional[str] = None
    qualifying_unit_share: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    total_units: Optional[int] = Field(default=None, ge=0)
    qualifying_units: Optional[int] = Field(default=None, ge=0)

    # Status
    delinquency_status: Optional[str] = "Current"

    @field_validator("rate_type")
    @classmethod
    def _validate_rate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        if v not in ("fixed", "arm"):
            raise ValueError("rate_type must be 'fixed' or 'arm'")
        return v

    @field_validator("government_subsidy_type")
    @classmethod
    def _validate_government_subsidy_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        raw = v.strip()
        if raw == "":
            return None

        # Keep this constrained/categorical while remaining backward compatible:
        # unknown values do not error; they simply fall back to "no subsidy".
        # Canonicalize: lowercase and collapse non-alphanumeric characters to underscores.
        v = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
        alias_map = {
            "lihtc": "lihtc",
            "low_income_housing_tax_credit": "lihtc",
            "pbra": "pbra",
            "project_based_rental_assistance": "pbra",
            "section8": "pbra",
            "section_8": "pbra",
            "section515": "section_515",
            "section_515": "section_515",
            "state_local": "state_local",
        }
        normalized = alias_map.get(v)
        allowed = {"lihtc", "pbra", "section_515", "state_local"}
        if normalized in allowed:
            return normalized
        if v in allowed:
            return v
        return None


class EngineResult(BaseModel):
    loan_id: str
    estimated_capital_factor: float
    estimated_capital_amount: float
    base_weight: float
    ltv_multiplier: float
    dscr_multiplier: float
    property_multiplier: float
    affordability_multiplier: float
    data_quality_score: int  # 0-100

    # ERCF loan-level rule outputs (expanded contract; engine support comes in later tasks)
    base_risk_weight: Optional[float] = None
    payment_performance_multiplier: float = 1.0
    interest_only_multiplier: float = 1.0
    term_multiplier: float = 1.0
    amortization_multiplier: float = 1.0
    loan_size_multiplier: float = 1.0
    special_product_multiplier: float = 1.0
    subsidy_multiplier: float = 1.0
    combined_multiplier: float = 1.0
    floor_value: float = 0.20
    floor_applied: bool = False

    confidence_score: int = Field(default=100, ge=0, le=100)
    confidence_threshold: int = Field(default=0, ge=0, le=100)
    missing_input_count: int = Field(default=0, ge=0)
    missing_inputs: List[str] = Field(default_factory=list)
    inferred_inputs: List[str] = Field(default_factory=list)
    confidence_notes: List[str] = Field(default_factory=list)
    result_available: bool = True

    final_risk_weight: Optional[float] = None
    capital_amount: Optional[float] = None

    @model_validator(mode="after")
    def _backfill_ercf_placeholders(self) -> "EngineResult":
        # Keep today's proxy engine working while providing stable fields for the
        # upgraded ERCF evaluator (implemented in later tasks).
        if self.base_risk_weight is None:
            self.base_risk_weight = self.base_weight
        if self.combined_multiplier == 1.0:
            self.combined_multiplier = (
                self.ltv_multiplier
                * self.dscr_multiplier
                * self.property_multiplier
                * self.affordability_multiplier
            )
        if self.final_risk_weight is None:
            self.final_risk_weight = self.estimated_capital_factor
        if self.capital_amount is None:
            self.capital_amount = self.estimated_capital_amount
        return self


class LoanWithResult(BaseModel):
    loan: LoanInput
    result: EngineResult


class PortfolioSummary(BaseModel):
    loan_count: int
    original_upb_total: float
    current_upb_total: float
    wa_dscr: float
    wa_ltv: float
    wa_estimated_capital_factor: float
    total_estimated_capital_amount: float
    loans_with_available_results: int = 0
    loans_with_missing_results: int = 0
    average_confidence_score: float = 0.0
    median_confidence_score: float = 0.0
    minimum_confidence_score: int = 0
    total_missing_input_count: int = 0
    missing_input_counts_by_field: dict[str, int] = {}


class CohortRequest(BaseModel):
    source: str
    snapshot: str
    filters: dict[str, list[str] | list[float] | list[int]] = Field(default_factory=dict)
    breakdown_dimension: str = "state"
    breakdown_metric: str = "current_upb_total"


class CohortSummary(BaseModel):
    loan_count: int
    original_upb_total: float
    current_upb_total: float
    wa_dscr: float
    wa_ltv: float
    wa_estimated_capital_factor: float
    total_estimated_capital_amount: float


class BreakdownRow(BaseModel):
    key: str
    value: float


class FixedChartPoint(BaseModel):
    label: str
    value: float


class FixedChartSeries(BaseModel):
    points: list[FixedChartPoint]


class BreakdownResponse(BaseModel):
    dimension: str
    metric: str
    rows: list[BreakdownRow]


class DrilldownRow(BaseModel):
    loan_id: str
    source: str
    reporting_date: Optional[date] = None
    property_type: Optional[str] = None
    state: Optional[str] = None
    current_upb: float
    dscr: float
    ltv: float
    estimated_capital_factor: float
    estimated_capital_amount: float


class CohortExplorerResponse(BaseModel):
    cohort_label: str
    summary: CohortSummary
    fixed_charts: dict[str, FixedChartSeries]
    breakdown: BreakdownResponse
    drilldown_rows: list[DrilldownRow]
