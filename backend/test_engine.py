import json
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch


import pandas as pd

from app import main
from app.engine import ERCFEngine
from app.engine import load_config
from app.schema import LoanInput
from fastapi.testclient import TestClient
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest_gse import build_curated_rows

class TestERCFEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ERCFEngine()

    def _expected_base_weight(self, rate_type: str, dscr_band_key: str, ltv_band_key: str) -> float:
        cfg = load_config()
        table = cfg["arm_base_risk_weights"] if rate_type == "arm" else cfg["fixed_rate_base_risk_weights"]
        return float(table[dscr_band_key][ltv_band_key])

    def test_engine_uses_table_driven_base_risk_weight_for_fixed_rate_loans(self):
        # Validate the lookup path (bands -> keys -> table cell), not the literal numbers.
        loan = LoanInput(
            loan_id="BASE-TABLE-FIXED-1",
            original_upb=1000,
            current_upb=1000,
            original_loan_amount=2_000_000,
            dscr=1.10,  # dscr_bands: le_125
            ltv=0.75,   # ltv_bands: le_80
            rate_type="fixed",
            interest_only=False,
            original_term_months=120,
            amortization_term_months=360,
            payment_performance="current",
            property_type="Multifamily",
        )

        result = self.engine.calculate_loan(loan)
        self.assertAlmostEqual(result.base_risk_weight, self._expected_base_weight("fixed", "le_125", "le_80"))

    def test_engine_uses_table_driven_base_risk_weight_for_arm_loans(self):
        # Validate the lookup path (bands -> keys -> table cell), not the literal numbers.
        loan = LoanInput(
            loan_id="BASE-TABLE-ARM-1",
            original_upb=1000,
            current_upb=1000,
            original_loan_amount=2_000_000,
            dscr=0.95,  # dscr_bands: le_100
            ltv=0.65,   # ltv_bands: le_70
            rate_type="arm",
            interest_only=False,
            original_term_months=120,
            amortization_term_months=360,
            payment_performance="current",
            property_type="Multifamily",
        )

        result = self.engine.calculate_loan(loan)
        self.assertAlmostEqual(result.base_risk_weight, self._expected_base_weight("arm", "le_100", "le_70"))

    def test_engine_populates_core_multipliers_and_combines_them(self):
        loan = LoanInput(
            loan_id="CORE-MULT-1",
            original_upb=1000,
            current_upb=1000,
            original_loan_amount=750_000,
            dscr=1.10,  # le_125
            ltv=0.75,   # le_80
            rate_type="fixed",
            interest_only=False,
            original_term_months=120,
            amortization_term_months=360,
            payment_performance="current",
            property_type="Multifamily",
        )
        baseline = self.engine.calculate_loan(loan)

        io_loan = loan.model_copy(update={"interest_only": True})
        io_result = self.engine.calculate_loan(io_loan)

        # Regression: the new core multipliers must not affect the legacy proxy outputs.
        self.assertAlmostEqual(io_result.estimated_capital_factor, baseline.estimated_capital_factor)
        self.assertAlmostEqual(io_result.estimated_capital_amount, baseline.estimated_capital_amount)

        self.assertGreater(io_result.interest_only_multiplier, baseline.interest_only_multiplier)
        self.assertGreater(io_result.combined_multiplier, baseline.combined_multiplier)

        expected = (
            io_result.payment_performance_multiplier
            * io_result.interest_only_multiplier
            * io_result.term_multiplier
            * io_result.amortization_multiplier
            * io_result.loan_size_multiplier
            * io_result.special_product_multiplier
            * io_result.subsidy_multiplier
        )
        self.assertAlmostEqual(io_result.combined_multiplier, expected)

        self.assertIsNotNone(io_result.base_risk_weight)
        self.assertIsNotNone(io_result.final_risk_weight)
        self.assertGreater(io_result.final_risk_weight, 0.0)

    def test_engine_base_risk_weight_changes_across_bands(self):
        # Two loans differing only by LTV band should produce different base risk weights.
        base_kwargs = dict(
            original_upb=1000,
            current_upb=1000,
            original_loan_amount=2_000_000,
            dscr=1.10,  # dscr_bands: le_125
            rate_type="fixed",
            interest_only=False,
            original_term_months=120,
            amortization_term_months=360,
            payment_performance="current",
            property_type="Multifamily",
        )

        low_ltv = LoanInput(loan_id="BANDS-1", ltv=0.59, **base_kwargs)  # le_60
        high_ltv = LoanInput(loan_id="BANDS-2", ltv=0.75, **base_kwargs)  # le_80
        low_res = self.engine.calculate_loan(low_ltv)
        high_res = self.engine.calculate_loan(high_ltv)

        self.assertAlmostEqual(low_res.base_risk_weight, self._expected_base_weight("fixed", "le_125", "le_60"))
        self.assertAlmostEqual(high_res.base_risk_weight, self._expected_base_weight("fixed", "le_125", "le_80"))
        self.assertNotEqual(low_res.base_risk_weight, high_res.base_risk_weight)

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

    def test_pbra_subsidy_type_receives_qualifying_multiplier(self):
        loan = LoanInput(
            loan_id="SUBSIDY-PBRA-1",
            original_upb=1000,
            current_upb=1000,
            original_loan_amount=2_000_000,
            dscr=1.4,
            ltv=0.6,
            rate_type="fixed",
            interest_only=False,
            original_term_months=120,
            amortization_term_months=360,
            payment_performance="current",
            property_type="Multifamily",
            government_subsidy_type="section 8",
            qualifying_unit_share=1.0,
        )

        result = self.engine.calculate_loan(loan)

        self.assertEqual(loan.government_subsidy_type, "pbra")
        self.assertAlmostEqual(result.subsidy_multiplier, 0.6)

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

    def test_calculator_api_response_keeps_refined_trace_fields(self):
        client = TestClient(main.app)
        response = client.post(
            "/api/calculate",
            json={
                "loan_id": "TRACE-API-1",
                "original_upb": 1000,
                "current_upb": 1000,
                "original_loan_amount": 1000,
                "dscr": 1.25,
                "ltv": 0.70,
                "rate_type": "fixed",
                "interest_only": False,
                "original_term_months": 120,
                "amortization_term_months": 360,
                "payment_performance": "current",
                "property_type": "Multifamily",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        trace_fields = [
            "base_weight",
            "ltv_multiplier",
            "dscr_multiplier",
            "property_multiplier",
            "affordability_multiplier",
            "base_risk_weight",
            "payment_performance_multiplier",
            "interest_only_multiplier",
            "term_multiplier",
            "amortization_multiplier",
            "loan_size_multiplier",
            "special_product_multiplier",
            "subsidy_multiplier",
            "combined_multiplier",
            "floor_value",
            "floor_applied",
            "confidence_score",
            "confidence_threshold",
            "missing_input_count",
            "missing_inputs",
            "inferred_inputs",
            "confidence_notes",
            "result_available",
            "final_risk_weight",
            "capital_amount",
        ]

        for field in trace_fields:
            with self.subTest(field=field):
                self.assertIn(field, body)

        self.assertTrue(body["result_available"])
        self.assertIsInstance(body["confidence_notes"], list)
        self.assertIsInstance(body["missing_inputs"], list)

    def test_confidence_scoring_applies_missing_input_penalties(self):
        # Task 4: confidence score and missing-input tracking are config-driven.
        self.engine.config = {
            "base_risk_weight": 0.5,
            "confidence": {
                "enabled": True,
                "minimum_score_for_result": 70,
                "penalties": {
                    "rate_type": 40,
                    "payment_performance": 20,
                    "original_loan_amount": 15,
                    "interest_only": 10,
                },
            },
            # Minimal tables so base_risk_weight can be computed (not backfilled).
            "ltv_bands": [{"key": "all", "max": 999.0}],
            "dscr_bands": [{"key": "all", "max": 999.0}],
            "fixed_rate_base_risk_weights": {"all": {"all": 0.30}},
            "arm_base_risk_weights": {"all": {"all": 0.40}},
        }

        loan = LoanInput(
            loan_id="CONF-1",
            original_upb=1000,
            current_upb=1000,
            dscr=1.25,
            ltv=0.65,
            property_type="Multifamily",
            # Missing: rate_type, payment_performance, original_loan_amount, interest_only
        )

        result = self.engine.calculate_loan(loan)
        expected_score = 100 - (40 + 20 + 15 + 10)
        self.assertEqual(result.confidence_score, expected_score)
        self.assertEqual(result.confidence_threshold, 70)
        self.assertEqual(result.missing_input_count, 4)
        self.assertCountEqual(
            result.missing_inputs,
            ["rate_type", "payment_performance", "original_loan_amount", "interest_only"],
        )

    def test_confidence_suppresses_result_below_threshold_but_preserves_legacy_proxy(self):
        self.engine.config = {
            "base_risk_weight": 0.5,
            "confidence": {
                "enabled": True,
                "minimum_score_for_result": 90,
                "penalties": {
                    "rate_type": 40,
                    "payment_performance": 20,
                },
            },
            "ltv_bands": [{"key": "all", "max": 999.0}],
            "dscr_bands": [{"key": "all", "max": 999.0}],
            "fixed_rate_base_risk_weights": {"all": {"all": 0.30}},
            "arm_base_risk_weights": {"all": {"all": 0.40}},
        }

        loan = LoanInput(
            loan_id="CONF-2",
            original_upb=1000,
            current_upb=1000,
            dscr=1.25,
            ltv=0.65,
            property_type="Multifamily",
            # Missing rate_type + payment_performance => score 40 < 90
        )

        result = self.engine.calculate_loan(loan)
        self.assertFalse(result.result_available)
        self.assertLess(result.confidence_score, result.confidence_threshold)

        # Suppressed ERCF result should be marked as unavailable.
        self.assertEqual(result.final_risk_weight, 0.0)
        self.assertEqual(result.capital_amount, 0.0)

        # Legacy proxy outputs must remain intact regardless of confidence.
        self.assertGreater(result.estimated_capital_factor, 0.0)
        self.assertGreater(result.estimated_capital_amount, 0.0)

    def test_confidence_tracks_inferred_rate_type_and_still_penalizes_missing(self):
        self.engine.config = {
            "base_risk_weight": 0.5,
            "confidence": {
                "enabled": True,
                "minimum_score_for_result": 70,
                "penalties": {
                    "rate_type": 40,
                },
            },
            "ltv_bands": [{"key": "all", "max": 999.0}],
            "dscr_bands": [{"key": "all", "max": 999.0}],
            "fixed_rate_base_risk_weights": {"all": {"all": 0.30}},
            "arm_base_risk_weights": {"all": {"all": 0.40}},
        }

        loan = LoanInput(
            loan_id="CONF-3",
            original_upb=1000,
            current_upb=1000,
            dscr=1.25,
            ltv=0.65,
            property_type="Multifamily",
            is_fixed_rate=False,  # Engine can infer ARM, but input is still missing.
            rate_type=None,
        )

        result = self.engine.calculate_loan(loan)
        self.assertIn("rate_type", result.inferred_inputs)
        self.assertIn("rate_type", result.missing_inputs)
        self.assertEqual(result.confidence_score, 60)

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

    def test_upload_row_mapping_populates_ercf_rule_fields(self):
        row = pd.Series(
            {
                "loan_id": "UPLOAD-1",
                "original_upb": 1000,
                "current_upb": 900,
                "dscr": 1.4,
                "ltv": 0.6,
                "property_type": "Multifamily",
                "state": "NY",
                "original_loan_amount": 2_500_000,
                "rate_type": "fixed",
                "interest_only": "true",
                "original_term_months": 120,
                "amortization_term_months": 360,
                "payment_performance": "current",
                "government_subsidy_type": "section 8",
                "qualifying_unit_share": 0.5,
                "total_units": 100,
                "qualifying_units": 50,
            }
        )

        uploaded = main._loan_from_upload_row(row)
        self.assertEqual(uploaded.original_loan_amount, 2_500_000)
        self.assertEqual(uploaded.rate_type, "fixed")
        self.assertTrue(uploaded.interest_only)
        self.assertEqual(uploaded.original_term_months, 120)
        self.assertEqual(uploaded.amortization_term_months, 360)
        self.assertEqual(uploaded.payment_performance, "current")
        self.assertEqual(uploaded.government_subsidy_type, "pbra")
        self.assertEqual(uploaded.qualifying_unit_share, 0.5)
        self.assertEqual(uploaded.total_units, 100)
        self.assertEqual(uploaded.qualifying_units, 50)

    def test_calculator_api_response_keeps_multiplier_trace_fields(self):
        client = TestClient(main.app)
        response = client.post(
            "/api/calculate",
            json={
                "loan_id": "TRACE-API-1",
                "original_upb": 1000,
                "current_upb": 1000,
                "dscr": 1.25,
                "ltv": 0.70,
                "property_type": "Multifamily",
                "is_affordable": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()

        for field in (
            "estimated_capital_factor",
            "estimated_capital_amount",
            "base_weight",
            "ltv_multiplier",
            "dscr_multiplier",
            "property_multiplier",
            "affordability_multiplier",
            "data_quality_score",
        ):
            with self.subTest(field=field):
                self.assertIn(field, body)

    def test_build_curated_rows_normalizes_freddie_latest_quarter(self):
        frame = pd.DataFrame(
            [
                {
                    "lnno": 100,
                    "quarter": "y24q4",
                    "amt_upb_pch": 120.0,
                    "amt_upb_endg": 100.0,
                    "rate_dcr": 1.25,
                    "rate_ltv": 0.65,
                    "code_st": "CA",
                    "geographical_region": "LOS ANGELES, CA",
                    "rate_int": 5.5,
                    "cnt_mrtg_term": 120,
                    "cnt_amtn_per": 360,
                    "cnt_io_per": 12,
                    "cd_fxfltr": "F",
                    "mrtg_status": "C",
                    "cnt_rsdntl_unit": 200,
                },
                {
                    "lnno": 101,
                    "quarter": "y25q3",
                    "amt_upb_pch": 150.0,
                    "amt_upb_endg": 130.0,
                    "rate_dcr": 1.30,
                    "rate_ltv": 0.70,
                    "code_st": "TX",
                    "geographical_region": "DALLAS, TX",
                    "rate_int": 6.0,
                    "cnt_mrtg_term": 60,
                    "cnt_amtn_per": 300,
                    "cnt_io_per": 0,
                    "cd_fxfltr": None,
                    "code_int": "FIX",
                    "mrtg_status": "30",
                    "cnt_rsdntl_unit": 150,
                },
            ]
        )

        rows = build_curated_rows("freddie_mac", [frame], snapshot="2025Q3")

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["source"], "freddie_mac")
        self.assertEqual(row["snapshot"], "2025Q3")
        self.assertEqual(row["loan_id"], "101")
        self.assertEqual(row["state"], "TX")
        self.assertAlmostEqual(row["current_upb"], 130.0)
        self.assertAlmostEqual(row["original_upb"], 150.0)
        self.assertAlmostEqual(row["original_loan_amount"], 150.0)
        self.assertAlmostEqual(row["dscr"], 1.30)
        self.assertAlmostEqual(row["ltv"], 0.70)
        self.assertAlmostEqual(row["note_rate"], 6.0)
        self.assertEqual(row["original_term_months"], 60)
        self.assertEqual(row["amortization_term_months"], 300)
        self.assertEqual(row["interest_only_term"], 0)
        self.assertEqual(row["interest_only"], False)
        self.assertEqual(row["rate_type"], "fixed")
        self.assertEqual(row["is_fixed_rate"], True)
        self.assertEqual(row["payment_performance"], "30")
        self.assertEqual(row["total_units"], 150)

    def test_build_curated_rows_preserves_freddie_senior_housing_and_arm_signals(self):
        frame = pd.DataFrame(
            [
                {
                    "lnno": 201,
                    "quarter": "y25q3",
                    "amt_upb_pch": 500.0,
                    "amt_upb_endg": 450.0,
                    "rate_dcr": 1.20,
                    "rate_ltv": 0.68,
                    "code_st": "TX",
                    "geographical_region": "DALLAS, TX",
                    "rate_int": 0.061,
                    "cnt_mrtg_term": 240,
                    "cnt_amtn_per": 240,
                    "cnt_io_per": 24,
                    "cd_fxfltr": "FXDFLT",
                    "code_int": "VAR",
                    "mrtg_status": "100.0",
                    "cnt_rsdntl_unit": 80,
                    "code_sr": "SAP",
                }
            ]
        )

        rows = build_curated_rows("freddie_mac", [frame], snapshot="2025Q3")

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["property_type"], "Seniors Housing")
        self.assertEqual(row["property_subtype"], "Senior apartments")
        self.assertEqual(row["property_subtype_code"], "SAP")
        self.assertEqual(row["rate_type"], "arm")
        self.assertEqual(row["rate_type_code"], "VAR")
        self.assertEqual(row["fixed_to_float_code"], "FXDFLT")
        self.assertFalse(row["is_fixed_rate"])
        self.assertEqual(row["interest_only_term"], 24)
        self.assertTrue(row["interest_only"])

    def test_build_curated_rows_normalizes_fannie_latest_reporting_period(self):
        frame = pd.DataFrame(
            [
                {
                    "Loan Number": "FNM-1",
                    "Reporting Period Date": "2025-06-30",
                    "Original UPB": 200.0,
                    "UPB - Current": 150.0,
                    "Underwritten DSCR": 1.20,
                    "Loan Acquisition LTV": 68.0,
                    "Specific Property Type": "Multifamily",
                    "Property State": "CA",
                    "Metropolitan Statistical Area": "Los Angeles, CA",
                    "Affordable Housing Type": "",
                    "Note Rate": 4.5,
                    "Original Term": 120,
                    "Amortization Term": 360,
                    "Original I/O Term": 24,
                    "Interest Type": "Fixed",
                    "Loan Payment Status": "Current",
                    "Property Acquisition Total Unit Count": 100,
                    "Physical Occupancy %": 0.95,
                },
                {
                    "Loan Number": "FNM-2",
                    "Reporting Period Date": "2025-09-30",
                    "Original UPB": 300.0,
                    "UPB - Current": 250.0,
                    "Underwritten DSCR": 1.35,
                    "Loan Acquisition LTV": 0.72,
                    "Specific Property Type": "Seniors Housing",
                    "Property State": "TX",
                    "Metropolitan Statistical Area": "Dallas, TX",
                    "Affordable Housing Type": "Affordable",
                    "Note Rate": 5.0,
                    "Original Term": 240,
                    "Amortization Term": 240,
                    "Original I/O Term": 0,
                    "Interest Type": "ARM",
                    "Loan Payment Status": "60+ Days",
                    "Property Acquisition Total Unit Count": 80,
                    "Physical Occupancy %": 0.90,
                },
            ]
        )

        rows = build_curated_rows("fannie_mae", [frame], snapshot="202509")

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["source"], "fannie_mae")
        self.assertEqual(row["snapshot"], "202509")
        self.assertEqual(row["loan_id"], "FNM-2")
        self.assertEqual(row["state"], "TX")
        self.assertTrue(row["is_affordable"])
        self.assertAlmostEqual(row["current_upb"], 250.0)
        self.assertAlmostEqual(row["original_upb"], 300.0)
        self.assertAlmostEqual(row["original_loan_amount"], 300.0)
        self.assertAlmostEqual(row["dscr"], 1.35)
        self.assertAlmostEqual(row["ltv"], 0.72)
        self.assertAlmostEqual(row["note_rate"], 5.0)
        self.assertEqual(row["original_term_months"], 240)
        self.assertEqual(row["amortization_term_months"], 240)
        self.assertEqual(row["interest_only_term"], 0)
        self.assertEqual(row["interest_only"], False)
        self.assertEqual(row["rate_type"], "arm")
        self.assertEqual(row["is_fixed_rate"], False)
        self.assertEqual(row["payment_performance"], "60+ Days")
        self.assertEqual(row["total_units"], 80)
        self.assertEqual(row["occupancy_rate"], 0.90)

    def test_portfolio_cohort_request_accepts_source_and_filters(self):
        from app.schema import CohortRequest

        request = CohortRequest(
            source="freddie_mac",
            snapshot="2025Q3",
            filters={"state": ["CA"], "property_type": ["Multifamily"]},
            breakdown_dimension="state",
            breakdown_metric="current_upb_total",
        )

        self.assertEqual(request.source, "freddie_mac")
        self.assertEqual(request.snapshot, "2025Q3")
        self.assertEqual(request.filters["state"], ["CA"])

    def test_portfolio_cohort_request_uses_default_breakdown_contract(self):
        from app.schema import CohortRequest

        request = CohortRequest(source="freddie_mac", snapshot="2025Q3")

        self.assertEqual(request.breakdown_dimension, "state")
        self.assertEqual(request.breakdown_metric, "current_upb_total")

    def test_explorer_response_accepts_nested_structured_models(self):
        from app.schema import CohortExplorerResponse

        response = CohortExplorerResponse(
            cohort_label="Freddie Mac 2025Q3",
            summary={
                "loan_count": 2,
                "original_upb_total": 300.0,
                "current_upb_total": 250.0,
                "wa_dscr": 1.2,
                "wa_ltv": 0.65,
                "wa_estimated_capital_factor": 0.5,
                "total_estimated_capital_amount": 125.0,
            },
            fixed_charts={
                "capital_factor_bands": {
                    "points": [
                        {"label": "0.0-0.5", "value": 10.0},
                        {"label": "0.5-1.0", "value": 5.0},
                    ]
                }
            },
            breakdown={
                "dimension": "state",
                "metric": "current_upb_total",
                "rows": [
                    {"key": "CA", "value": 150.0},
                    {"key": "TX", "value": 100.0},
                ],
            },
            drilldown_rows=[],
        )

        self.assertEqual(response.cohort_label, "Freddie Mac 2025Q3")
        self.assertEqual(response.fixed_charts["capital_factor_bands"].points[0].label, "0.0-0.5")
        self.assertEqual(response.breakdown.dimension, "state")
        self.assertEqual(response.breakdown.rows[1].key, "TX")


class TestCuratedExplorer(unittest.TestCase):
    def test_curated_store_loads_rows_from_snapshot_json(self):
        from app.datasets.curated_store import CuratedStore

        rows = [
            {
                "loan_id": "FNM-1",
                "source": "fannie_mae",
                "snapshot": "2025Q3",
                "state": "NY",
                "property_type": "Multifamily",
                "current_upb": 123.0,
                "original_upb": 150.0,
                "dscr": 1.25,
                "ltv": 0.62,
                "estimated_capital_factor": 0.55,
                "estimated_capital_amount": 67.65,
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "fannie_mae"
            source_dir.mkdir(parents=True, exist_ok=True)
            snapshot_path = source_dir / "2025Q3.json"
            snapshot_path.write_text(json.dumps(rows), encoding="utf-8")

            loaded_rows = CuratedStore(root).load_rows("fannie_mae", "2025Q3")

        self.assertEqual(loaded_rows, rows)

    def test_curated_store_rejects_unsafe_source_and_snapshot_names(self):
        from app.datasets.curated_store import CuratedStore

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = CuratedStore(root)

            with self.assertRaisesRegex(ValueError, "Unsupported curated source"):
                store.load_rows("../fannie_mae", "2025Q3")

            with self.assertRaisesRegex(ValueError, "Invalid snapshot name"):
                store.load_rows("fannie_mae", "../escape")

    def test_empty_filter_list_does_not_remove_rows(self):
        from app.datasets.explorer import ExplorerService

        rows = [
            {
                "loan_id": "FRE-1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            },
            {
                "loan_id": "FRE-2",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "TX",
                "property_type": "Seniors Housing",
                "current_upb": 200.0,
                "original_upb": 220.0,
                "dscr": 1.10,
                "ltv": 0.75,
                "estimated_capital_factor": 0.75,
                "estimated_capital_amount": 150.0,
            },
        ]

        response = ExplorerService(rows).build_cohort(
            source="freddie_mac",
            snapshot="2025Q3",
            filters={"state": []},
            breakdown_dimension="state",
            breakdown_metric="current_upb_total",
        )

        self.assertEqual(response.summary.loan_count, 2)
        self.assertEqual(response.summary.current_upb_total, 300.0)
        self.assertEqual(
            [point.label for point in response.fixed_charts["state_mix"].points],
            ["CA", "TX"],
        )

    def test_unsupported_filter_key_is_rejected(self):
        from app.datasets.explorer import ExplorerService

        rows = [
            {
                "loan_id": "FRE-1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            }
        ]

        service = ExplorerService(rows)

        with self.assertRaisesRegex(ValueError, "Unsupported cohort filter field"):
            service.build_cohort(
                source="freddie_mac",
                snapshot="2025Q3",
                filters={"unsupported_field": ["x"]},
                breakdown_dimension="state",
                breakdown_metric="current_upb_total",
            )

    def test_invalid_breakdown_dimension_is_rejected(self):
        from app.datasets.explorer import ExplorerService

        rows = [
            {
                "loan_id": "FRE-1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            }
        ]

        service = ExplorerService(rows)

        with self.assertRaisesRegex(ValueError, "Unsupported breakdown dimension"):
            service.build_cohort(
                source="freddie_mac",
                snapshot="2025Q3",
                filters={},
                breakdown_dimension="msa",
                breakdown_metric="current_upb_total",
            )

    def test_explorer_service_filters_and_summarizes_a_curated_source(self):
        from app.datasets.explorer import ExplorerService

        rows = [
            {
                "loan_id": "FRE-1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            },
            {
                "loan_id": "FRE-2",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "TX",
                "property_type": "Seniors Housing",
                "current_upb": 200.0,
                "original_upb": 220.0,
                "dscr": 1.10,
                "ltv": 0.75,
                "estimated_capital_factor": 0.75,
                "estimated_capital_amount": 150.0,
            },
        ]

        service = ExplorerService(rows)
        response = service.build_cohort(
            source="freddie_mac",
            snapshot="2025Q3",
            filters={"state": ["CA"]},
            breakdown_dimension="state",
            breakdown_metric="current_upb_total",
        )

        self.assertEqual(response.summary.loan_count, 1)
        self.assertEqual(response.summary.current_upb_total, 100.0)
        self.assertEqual(response.summary.original_upb_total, 120.0)
        self.assertEqual(response.summary.wa_dscr, 1.30)
        self.assertEqual(response.summary.wa_ltv, 0.60)
        self.assertEqual(response.summary.wa_estimated_capital_factor, 0.50)
        self.assertEqual(response.summary.total_estimated_capital_amount, 50.0)
        self.assertEqual(response.breakdown.dimension, "state")
        self.assertEqual(response.breakdown.metric, "current_upb_total")
        self.assertEqual(response.breakdown.rows[0].key, "CA")
        self.assertEqual(response.breakdown.rows[0].value, 100.0)
        self.assertEqual(response.drilldown_rows[0].loan_id, "FRE-1")
        self.assertIn("capital_factor_bands", response.fixed_charts)


class TestExplorerEndpoints(unittest.TestCase):
    def test_compare_endpoint_returns_two_cohorts_and_delta_cards(self):
        from app.main import build_compare_response

        left = {
            "loan_count": 2,
            "original_upb_total": 300.0,
            "current_upb_total": 250.0,
            "wa_dscr": 1.20,
            "wa_ltv": 0.65,
            "wa_estimated_capital_factor": 0.55,
            "total_estimated_capital_amount": 140.0,
        }
        right = {
            "loan_count": 2,
            "original_upb_total": 310.0,
            "current_upb_total": 260.0,
            "wa_dscr": 1.10,
            "wa_ltv": 0.70,
            "wa_estimated_capital_factor": 0.60,
            "total_estimated_capital_amount": 156.0,
        }

        response = build_compare_response(left, right)

        self.assertAlmostEqual(response["deltas"]["wa_dscr"], 0.10)
        self.assertAlmostEqual(
            response["deltas"]["total_estimated_capital_amount"], -16.0
        )

    def test_explorer_compare_endpoint_uses_curated_store_and_service(self):
        from app.schema import CohortRequest, CompareRequest

        request = CompareRequest(
            left=CohortRequest(
                source="freddie_mac",
                snapshot="2025Q3",
                filters={"state": ["CA"]},
                breakdown_dimension="state",
                breakdown_metric="current_upb_total",
            ),
            right=CohortRequest(
                source="freddie_mac",
                snapshot="2025Q4",
                filters={"state": ["TX"]},
                breakdown_dimension="state",
                breakdown_metric="current_upb_total",
            ),
        )
        left_rows = [
            {
                "loan_id": "FRE-L1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            }
        ]
        right_rows = [
            {
                "loan_id": "FRE-R1",
                "source": "freddie_mac",
                "snapshot": "2025Q4",
                "state": "TX",
                "property_type": "Multifamily",
                "current_upb": 160.0,
                "original_upb": 180.0,
                "dscr": 1.10,
                "ltv": 0.75,
                "estimated_capital_factor": 0.75,
                "estimated_capital_amount": 120.0,
            }
        ]

        with patch.object(
            main.curated_store,
            "load_rows",
            side_effect=[left_rows, right_rows],
        ) as load_rows:
            response = main.compare_explorer_cohorts(request)

        self.assertEqual(load_rows.call_count, 2)
        self.assertEqual(response.left.cohort_label, "freddie_mac 2025Q3")
        self.assertEqual(response.right.cohort_label, "freddie_mac 2025Q4")
        self.assertEqual(response.left.summary.loan_count, 1)
        self.assertEqual(response.right.summary.loan_count, 1)
        self.assertAlmostEqual(response.deltas.current_upb_total, -60.0)
        self.assertAlmostEqual(response.deltas.wa_dscr, 0.20)

    def test_explorer_cohort_endpoint_uses_curated_store_and_service(self):
        from app.schema import CohortRequest

        request = CohortRequest(
            source="freddie_mac",
            snapshot="2025Q3",
            filters={"state": ["CA"]},
            breakdown_dimension="state",
            breakdown_metric="current_upb_total",
        )
        rows = [
            {
                "loan_id": "FRE-1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            }
        ]

        with patch.object(main.curated_store, "load_rows", return_value=rows) as load_rows:
            response = main.get_explorer_cohort(request)

        load_rows.assert_called_once_with("freddie_mac", "2025Q3")
        self.assertEqual(response.cohort_label, "freddie_mac 2025Q3")
        self.assertEqual(response.summary.loan_count, 1)
        self.assertEqual(response.breakdown.rows[0].key, "CA")


class TestExplorerHttpEndpoints(unittest.TestCase):
    def test_post_explorer_cohort_returns_serialized_response(self):
        rows = [
            {
                "loan_id": "FRE-1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            }
        ]

        with TestClient(main.app, raise_server_exceptions=False) as client:
            with patch.object(main.curated_store, "load_rows", return_value=rows):
                response = client.post(
                    "/api/explorer/cohort",
                    json={
                        "source": "freddie_mac",
                        "snapshot": "2025Q3",
                        "filters": {"state": ["CA"]},
                        "breakdown_dimension": "state",
                        "breakdown_metric": "current_upb_total",
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["cohort_label"], "freddie_mac 2025Q3")
        self.assertEqual(payload["summary"]["loan_count"], 1)
        self.assertEqual(payload["breakdown"]["rows"][0]["key"], "CA")

    def test_post_explorer_compare_returns_serialized_response(self):
        left_rows = [
            {
                "loan_id": "FRE-L1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            }
        ]
        right_rows = [
            {
                "loan_id": "FRE-R1",
                "source": "freddie_mac",
                "snapshot": "2025Q4",
                "state": "TX",
                "property_type": "Multifamily",
                "current_upb": 160.0,
                "original_upb": 180.0,
                "dscr": 1.10,
                "ltv": 0.75,
                "estimated_capital_factor": 0.75,
                "estimated_capital_amount": 120.0,
            }
        ]

        with TestClient(main.app, raise_server_exceptions=False) as client:
            with patch.object(
                main.curated_store,
                "load_rows",
                side_effect=[left_rows, right_rows],
            ):
                response = client.post(
                    "/api/explorer/compare",
                    json={
                        "left": {
                            "source": "freddie_mac",
                            "snapshot": "2025Q3",
                            "filters": {"state": ["CA"]},
                            "breakdown_dimension": "state",
                            "breakdown_metric": "current_upb_total",
                        },
                        "right": {
                            "source": "freddie_mac",
                            "snapshot": "2025Q4",
                            "filters": {"state": ["TX"]},
                            "breakdown_dimension": "state",
                            "breakdown_metric": "current_upb_total",
                        },
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["left"]["cohort_label"], "freddie_mac 2025Q3")
        self.assertEqual(payload["right"]["cohort_label"], "freddie_mac 2025Q4")
        self.assertAlmostEqual(payload["deltas"]["current_upb_total"], -60.0)

    def test_invalid_explorer_filter_returns_4xx_response(self):
        rows = [
            {
                "loan_id": "FRE-1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            }
        ]

        with TestClient(main.app, raise_server_exceptions=False) as client:
            with patch.object(main.curated_store, "load_rows", return_value=rows):
                response = client.post(
                    "/api/explorer/cohort",
                    json={
                        "source": "freddie_mac",
                        "snapshot": "2025Q3",
                        "filters": {"unsupported_field": ["CA"]},
                        "breakdown_dimension": "state",
                        "breakdown_metric": "current_upb_total",
                    },
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported cohort filter field", response.json()["detail"])

    def test_invalid_explorer_dimension_returns_4xx_response(self):
        rows = [
            {
                "loan_id": "FRE-1",
                "source": "freddie_mac",
                "snapshot": "2025Q3",
                "state": "CA",
                "property_type": "Multifamily",
                "current_upb": 100.0,
                "original_upb": 120.0,
                "dscr": 1.30,
                "ltv": 0.60,
                "estimated_capital_factor": 0.50,
                "estimated_capital_amount": 50.0,
            }
        ]

        with TestClient(main.app, raise_server_exceptions=False) as client:
            with patch.object(main.curated_store, "load_rows", return_value=rows):
                response = client.post(
                    "/api/explorer/compare",
                    json={
                        "left": {
                            "source": "freddie_mac",
                            "snapshot": "2025Q3",
                            "filters": {"state": ["CA"]},
                            "breakdown_dimension": "state",
                            "breakdown_metric": "current_upb_total",
                        },
                        "right": {
                            "source": "freddie_mac",
                            "snapshot": "2025Q3",
                            "filters": {"state": ["CA"]},
                            "breakdown_dimension": "msa",
                            "breakdown_metric": "current_upb_total",
                        },
                    },
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported breakdown dimension", response.json()["detail"])

if __name__ == '__main__':
    unittest.main()
