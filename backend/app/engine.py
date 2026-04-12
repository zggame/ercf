import yaml
import os
from typing import Any, Dict, List, Optional, Tuple
from .schema import LoanInput, EngineResult

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ercf_config.yaml')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

class ERCFEngine:
    def __init__(self):
        self.config = load_config()

    def _band_key_for_value(self, value: float, bands: List[Dict[str, Any]]) -> Optional[str]:
        if value is None or not bands:
            return None
        for band in bands:
            if value <= float(band["max"]):
                return str(band["key"])
        # Catch-all: if bands are present but malformed (no max catches), use last key.
        return str(bands[-1].get("key")) if bands[-1].get("key") is not None else None

    def _base_risk_weight_from_tables(self, loan: LoanInput) -> Optional[float]:
        cfg = self.config
        if not (
            isinstance(cfg.get("ltv_bands"), list)
            and isinstance(cfg.get("dscr_bands"), list)
            and isinstance(cfg.get("fixed_rate_base_risk_weights"), dict)
            and isinstance(cfg.get("arm_base_risk_weights"), dict)
        ):
            return None

        ltv_key = self._band_key_for_value(loan.ltv, cfg["ltv_bands"])
        dscr_key = self._band_key_for_value(loan.dscr, cfg["dscr_bands"])
        if not ltv_key or not dscr_key:
            return None

        rate_type = loan.rate_type
        if rate_type is None:
            # Backward-compat fallback to the legacy `is_fixed_rate` flag when provided.
            if loan.is_fixed_rate is False:
                rate_type = "arm"
            else:
                rate_type = "fixed"

        table = cfg["arm_base_risk_weights"] if rate_type == "arm" else cfg["fixed_rate_base_risk_weights"]
        try:
            return float(table[dscr_key][ltv_key])
        except Exception:
            return None

    def _core_multipliers(self, loan: LoanInput) -> Tuple[float, float, float, float, float, float]:
        # These are placeholders for the fully-configurable FHFA multiplier tables
        # (wired up in later tasks). For now, we compute stable, monotonic loan-level
        # multipliers without affecting the legacy proxy fields.
        perf = (loan.payment_performance or "").strip().lower()
        if perf in ("", "current", "performing", "paid", "ok"):
            payment_performance_multiplier = 1.0
        elif perf in ("30", "30dq", "30_dq", "dq30"):
            payment_performance_multiplier = 1.10
        elif perf in ("60", "60dq", "60_dq", "dq60", "60_plus", "60plus", "90", "90dq", "nonperforming", "default"):
            payment_performance_multiplier = 1.25
        else:
            payment_performance_multiplier = 1.0

        interest_only_multiplier = 1.10 if loan.interest_only is True else 1.0

        term = loan.original_term_months
        if term is None:
            term_multiplier = 1.0
        elif term <= 60:
            term_multiplier = 1.0
        elif term <= 120:
            term_multiplier = 1.05
        elif term <= 240:
            term_multiplier = 1.10
        else:
            term_multiplier = 1.15

        amort = loan.amortization_term_months
        if amort is None:
            amortization_multiplier = 1.0
        elif amort <= 240:
            amortization_multiplier = 1.0
        elif amort <= 360:
            amortization_multiplier = 1.05
        else:
            amortization_multiplier = 1.10

        size = loan.original_loan_amount
        if size is None:
            loan_size_multiplier = 1.0
        elif size < 1_000_000:
            loan_size_multiplier = 1.15
        elif size < 5_000_000:
            loan_size_multiplier = 1.10
        elif size < 25_000_000:
            loan_size_multiplier = 1.05
        else:
            loan_size_multiplier = 1.0

        special_product_multiplier = 1.0
        return (
            payment_performance_multiplier,
            interest_only_multiplier,
            term_multiplier,
            amortization_multiplier,
            loan_size_multiplier,
            special_product_multiplier,
        )

    def calculate_loan(self, loan: LoanInput) -> EngineResult:
        base_weight = self.config.get('base_risk_weight', 0.5)

        ltv_multiplier = 1.0
        for band in self.config.get('ltv_multipliers', []):
            if loan.ltv <= band['max']:
                ltv_multiplier = band['multiplier']
                break

        dscr_multiplier = 1.0
        for band in self.config.get('dscr_multipliers', []):
            if loan.dscr <= band['max']:
                dscr_multiplier = band['multiplier']
                break

        property_multiplier = self.config.get('property_type_multipliers', {}).get(loan.property_type, 1.0)

        affordability_multiplier = self.config.get('affordability_multiplier', 0.9) if loan.is_affordable else 1.0

        final_factor = base_weight * ltv_multiplier * dscr_multiplier * property_multiplier * affordability_multiplier

        # very basic data quality score
        score = 100
        if not loan.occupancy_rate: score -= 10
        if not loan.valuation_amount: score -= 10

        # New, additive loan-level ERCF fields (Task 3). These do NOT change the
        # legacy proxy `estimated_capital_factor` or `estimated_capital_amount`.
        base_risk_weight = self._base_risk_weight_from_tables(loan)
        (
            payment_performance_multiplier,
            interest_only_multiplier,
            term_multiplier,
            amortization_multiplier,
            loan_size_multiplier,
            special_product_multiplier,
        ) = self._core_multipliers(loan)
        subsidy_multiplier = 1.0  # wired up in Task 5
        combined_multiplier = (
            payment_performance_multiplier
            * interest_only_multiplier
            * term_multiplier
            * amortization_multiplier
            * loan_size_multiplier
            * special_product_multiplier
            * subsidy_multiplier
        )
        floor_value = 0.20
        floor_applied = False
        final_risk_weight = None
        capital_amount = None
        if base_risk_weight is not None:
            raw = base_risk_weight * combined_multiplier
            if raw < floor_value:
                floor_applied = True
                final_risk_weight = floor_value
            else:
                final_risk_weight = raw
            capital_amount = loan.current_upb * final_risk_weight

        return EngineResult(
            loan_id=loan.loan_id,
            estimated_capital_factor=final_factor,
            estimated_capital_amount=loan.current_upb * final_factor,
            base_weight=base_weight,
            ltv_multiplier=ltv_multiplier,
            dscr_multiplier=dscr_multiplier,
            property_multiplier=property_multiplier,
            affordability_multiplier=affordability_multiplier,
            data_quality_score=score,
            base_risk_weight=base_risk_weight,
            payment_performance_multiplier=payment_performance_multiplier,
            interest_only_multiplier=interest_only_multiplier,
            term_multiplier=term_multiplier,
            amortization_multiplier=amortization_multiplier,
            loan_size_multiplier=loan_size_multiplier,
            special_product_multiplier=special_product_multiplier,
            subsidy_multiplier=subsidy_multiplier,
            combined_multiplier=combined_multiplier,
            floor_value=floor_value,
            floor_applied=floor_applied,
            final_risk_weight=final_risk_weight,
            capital_amount=capital_amount,
        )
