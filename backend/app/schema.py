from pydantic import BaseModel, Field
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

    # Status
    delinquency_status: Optional[str] = "Current"


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
