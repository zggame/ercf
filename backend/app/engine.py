import yaml
import os
from .schema import LoanInput, EngineResult

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ercf_config.yaml')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

class ERCFEngine:
    def __init__(self):
        self.config = load_config()

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

        return EngineResult(
            loan_id=loan.loan_id,
            estimated_capital_factor=final_factor,
            estimated_capital_amount=loan.current_upb * final_factor,
            base_weight=base_weight,
            ltv_multiplier=ltv_multiplier,
            dscr_multiplier=dscr_multiplier,
            property_multiplier=property_multiplier,
            affordability_multiplier=affordability_multiplier,
            data_quality_score=score
        )
