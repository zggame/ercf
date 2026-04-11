import unittest
from app.schema import LoanInput
from app.engine import ERCFEngine

class TestERCFEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ERCFEngine()

    def test_basic_calculation(self):
        loan = LoanInput(
            loan_id="TEST-1",
            original_upb=1000,
            current_upb=1000,
            dscr=1.35, # should map to 1.0 multiplier based on config
            ltv=0.65,  # should map to 1.0 multiplier
            property_type="Multifamily" # 1.0 multiplier
        )
        result = self.engine.calculate_loan(loan)

        # Expected: base 0.5 * 1.0 * 1.0 * 1.0 = 0.5
        self.assertAlmostEqual(result.estimated_capital_factor, 0.5)
        self.assertEqual(result.estimated_capital_amount, 500.0)

    def test_high_risk_calculation(self):
        loan = LoanInput(
            loan_id="TEST-2",
            original_upb=1000,
            current_upb=1000,
            dscr=0.9, # max 1.0 = 1.5 multiplier
            ltv=0.85, # max 1.0 = 1.5 multiplier
            property_type="Seniors Housing" # 1.1 multiplier
        )
        result = self.engine.calculate_loan(loan)

        # Expected: base 0.5 * 1.5 * 1.5 * 1.1 = 1.2375
        self.assertAlmostEqual(result.estimated_capital_factor, 1.2375)

if __name__ == '__main__':
    unittest.main()
