import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import main
from app.engine import ERCFEngine
from app.schema import LoanInput

class TestERCFEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ERCFEngine()

    def test_engine_result_exposes_confidence_and_rule_fields(self):
        loan = LoanInput(
            loan_id="RULE-INPUT-1",
            original_upb=1000,
            current_upb=1000,
            original_loan_amount=1000,
            dscr=1.4,
            ltv=0.6,
            rate_type="fixed",
            interest_only=False,
            original_term_months=120,
            amortization_term_months=360,
            payment_performance="current",
            property_type="Multifamily",
            government_subsidy_type="lihtc",
            qualifying_unit_share=0.25,
            total_units=100,
            qualifying_units=25,
        )

        # Contract: new rule inputs must be present as real fields (not ignored extras).
        self.assertTrue(hasattr(loan, "rate_type"))
        self.assertEqual(loan.rate_type, "fixed")
        self.assertTrue(hasattr(loan, "original_loan_amount"))
        self.assertEqual(loan.original_loan_amount, 1000)

        result = self.engine.calculate_loan(loan)

        # Contract: existing fields remain present for current UI.
        self.assertTrue(hasattr(result, "estimated_capital_factor"))
        self.assertTrue(hasattr(result, "estimated_capital_amount"))
        self.assertTrue(hasattr(result, "data_quality_score"))

        # Contract: result exposes placeholders for the expanded ERCF fields.
        self.assertTrue(hasattr(result, "base_risk_weight"))
        self.assertTrue(hasattr(result, "payment_performance_multiplier"))
        self.assertTrue(hasattr(result, "interest_only_multiplier"))
        self.assertTrue(hasattr(result, "term_multiplier"))
        self.assertTrue(hasattr(result, "amortization_multiplier"))
        self.assertTrue(hasattr(result, "loan_size_multiplier"))
        self.assertTrue(hasattr(result, "special_product_multiplier"))
        self.assertTrue(hasattr(result, "subsidy_multiplier"))
        self.assertTrue(hasattr(result, "combined_multiplier"))
        self.assertTrue(hasattr(result, "floor_value"))
        self.assertTrue(hasattr(result, "floor_applied"))

        self.assertTrue(hasattr(result, "confidence_score"))
        self.assertTrue(hasattr(result, "confidence_threshold"))
        self.assertTrue(hasattr(result, "missing_input_count"))
        self.assertTrue(hasattr(result, "missing_inputs"))
        self.assertTrue(hasattr(result, "inferred_inputs"))
        self.assertTrue(hasattr(result, "result_available"))
        self.assertTrue(hasattr(result, "final_risk_weight"))
        self.assertTrue(hasattr(result, "capital_amount"))

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

    def test_load_portfolio_returns_seed_data_when_file_missing(self):
        missing_path = Path(tempfile.gettempdir()) / "missing-portfolio.json"
        if missing_path.exists():
            missing_path.unlink()

        with patch.object(main, "DB_PATH", missing_path):
            portfolio = main.load_portfolio()

        self.assertEqual(len(portfolio), 2)
        self.assertEqual(portfolio[0].loan_id, "MOCK-001")

    def test_load_portfolio_returns_empty_when_persisted_file_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "portfolio_data.json"
            invalid_path.write_text("{invalid json", encoding="utf-8")

            with patch.object(main, "DB_PATH", invalid_path):
                portfolio = main.load_portfolio()

        self.assertEqual(portfolio, [])

    def test_load_portfolio_reads_valid_persisted_loans(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "portfolio_data.json"
            data_path.write_text(
                json.dumps(
                    [
                        {
                            "loan_id": "PERSISTED-1",
                            "original_upb": 2000,
                            "current_upb": 1500,
                            "property_type": "Multifamily",
                            "is_affordable": True,
                            "dscr": 1.3,
                            "ltv": 0.6,
                            "state": "NY",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch.object(main, "DB_PATH", data_path):
                portfolio = main.load_portfolio()

        self.assertEqual(len(portfolio), 1)
        self.assertEqual(portfolio[0].loan_id, "PERSISTED-1")
        self.assertTrue(portfolio[0].is_affordable)

if __name__ == '__main__':
    unittest.main()
