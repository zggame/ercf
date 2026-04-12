import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import main
from app.engine import ERCFEngine
from app.engine import load_config
from app.schema import LoanInput

class TestERCFEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ERCFEngine()

    def test_policy_config_is_table_driven_and_has_confidence_settings(self):
        cfg = load_config()

        # Base-table policy config (FHFA-style shape). Engine logic will be updated
        # in later tasks; this test only asserts the policy config loads and is
        # internally consistent.
        self.assertIn("ltv_bands", cfg)
        self.assertIn("dscr_bands", cfg)
        self.assertIn("fixed_rate_base_risk_weights", cfg)
        self.assertIn("arm_base_risk_weights", cfg)
        self.assertIn("confidence", cfg)

        ltv_bands = cfg["ltv_bands"]
        dscr_bands = cfg["dscr_bands"]
        self.assertIsInstance(ltv_bands, list)
        self.assertIsInstance(dscr_bands, list)
        self.assertGreaterEqual(len(ltv_bands), 1)
        self.assertGreaterEqual(len(dscr_bands), 1)

        ltv_keys = [b["key"] for b in ltv_bands]
        dscr_keys = [b["key"] for b in dscr_bands]
        self.assertEqual(len(ltv_keys), len(set(ltv_keys)))
        self.assertEqual(len(dscr_keys), len(set(dscr_keys)))

        ltv_maxes = [b["max"] for b in ltv_bands]
        dscr_maxes = [b["max"] for b in dscr_bands]
        self.assertEqual(ltv_maxes, sorted(ltv_maxes))
        self.assertEqual(dscr_maxes, sorted(dscr_maxes))
        # Must be strictly increasing (no overlaps/gaps ambiguity).
        self.assertEqual(len(ltv_maxes), len(set(ltv_maxes)))
        self.assertEqual(len(dscr_maxes), len(set(dscr_maxes)))
        # Catch-all final band.
        self.assertGreaterEqual(float(ltv_maxes[-1]), 999.0)
        self.assertGreaterEqual(float(dscr_maxes[-1]), 999.0)

        fixed = cfg["fixed_rate_base_risk_weights"]
        arm = cfg["arm_base_risk_weights"]
        self.assertIsInstance(fixed, dict)
        self.assertIsInstance(arm, dict)

        # Rows: DSCR bands. Columns: LTV bands.
        self.assertEqual(set(fixed.keys()), set(dscr_keys))
        self.assertEqual(set(arm.keys()), set(dscr_keys))
        for row_key in dscr_keys:
            self.assertEqual(set(fixed[row_key].keys()), set(ltv_keys))
            self.assertEqual(set(arm[row_key].keys()), set(ltv_keys))
            for col_key in ltv_keys:
                self.assertIsInstance(fixed[row_key][col_key], (int, float))
                self.assertIsInstance(arm[row_key][col_key], (int, float))

        confidence = cfg["confidence"]
        self.assertIsInstance(confidence, dict)
        self.assertIn("enabled", confidence)
        self.assertIn("minimum_score_for_result", confidence)
        self.assertIn("penalties", confidence)
        self.assertIsInstance(confidence["enabled"], bool)
        self.assertIsInstance(confidence["minimum_score_for_result"], int)
        self.assertIsInstance(confidence["penalties"], dict)

    def test_government_subsidy_type_normalization(self):
        base_kwargs = dict(
            loan_id="SUBSIDY-NORM-1",
            original_upb=1000,
            current_upb=1000,
            dscr=1.35,
            ltv=0.65,
            property_type="Multifamily",
        )

        self.assertEqual(
            LoanInput(**base_kwargs, government_subsidy_type="section 8").government_subsidy_type,
            "pbra",
        )
        self.assertEqual(
            LoanInput(**base_kwargs, government_subsidy_type="Section-8").government_subsidy_type,
            "pbra",
        )
        self.assertEqual(
            LoanInput(**base_kwargs, government_subsidy_type="  section_8  ").government_subsidy_type,
            "pbra",
        )
        self.assertEqual(
            LoanInput(**base_kwargs, government_subsidy_type="section 515").government_subsidy_type,
            "section_515",
        )
        self.assertEqual(
            LoanInput(**base_kwargs, government_subsidy_type="low income housing tax credit").government_subsidy_type,
            "lihtc",
        )
        self.assertEqual(
            LoanInput(**base_kwargs, government_subsidy_type="state/local").government_subsidy_type,
            "state_local",
        )

        self.assertIsNone(LoanInput(**base_kwargs, government_subsidy_type="").government_subsidy_type)
        self.assertIsNone(LoanInput(**base_kwargs, government_subsidy_type="   ").government_subsidy_type)
        self.assertIsNone(LoanInput(**base_kwargs, government_subsidy_type="unknown subsidy").government_subsidy_type)

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
        self.assertTrue(hasattr(loan, "government_subsidy_type"))
        self.assertEqual(loan.government_subsidy_type, "lihtc")

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
        self.assertTrue(hasattr(result, "confidence_notes"))
        self.assertTrue(hasattr(result, "result_available"))
        self.assertTrue(hasattr(result, "final_risk_weight"))
        self.assertTrue(hasattr(result, "capital_amount"))

    def test_basic_calculation(self):
        # Keep this test independent of the on-disk policy config; the config
        # shape changes in Task 2 and engine logic will change in later tasks.
        self.engine.config = {
            "base_risk_weight": 0.5,
            "ltv_multipliers": [
                {"max": 0.60, "multiplier": 0.8},
                {"max": 0.70, "multiplier": 1.0},
                {"max": 0.80, "multiplier": 1.2},
                {"max": 1.00, "multiplier": 1.5},
                {"max": 999.0, "multiplier": 2.0},
            ],
            "dscr_multipliers": [
                {"max": 1.00, "multiplier": 1.5},
                {"max": 1.25, "multiplier": 1.2},
                {"max": 1.50, "multiplier": 1.0},
                {"max": 999.0, "multiplier": 0.8},
            ],
            "property_type_multipliers": {
                "Multifamily": 1.0,
                "Seniors Housing": 1.1,
                "Student Housing": 1.15,
                "Manufactured Housing": 1.05,
            },
            "affordability_multiplier": 0.9,
        }
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
        # Keep this test independent of the on-disk policy config; the config
        # shape changes in Task 2 and engine logic will change in later tasks.
        self.engine.config = {
            "base_risk_weight": 0.5,
            "ltv_multipliers": [
                {"max": 0.60, "multiplier": 0.8},
                {"max": 0.70, "multiplier": 1.0},
                {"max": 0.80, "multiplier": 1.2},
                {"max": 1.00, "multiplier": 1.5},
                {"max": 999.0, "multiplier": 2.0},
            ],
            "dscr_multipliers": [
                {"max": 1.00, "multiplier": 1.5},
                {"max": 1.25, "multiplier": 1.2},
                {"max": 1.50, "multiplier": 1.0},
                {"max": 999.0, "multiplier": 0.8},
            ],
            "property_type_multipliers": {
                "Multifamily": 1.0,
                "Seniors Housing": 1.1,
                "Student Housing": 1.15,
                "Manufactured Housing": 1.05,
            },
            "affordability_multiplier": 0.9,
        }
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
