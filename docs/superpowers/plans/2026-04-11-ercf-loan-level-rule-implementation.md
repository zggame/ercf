# ERCF Loan-Level Rule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current simplified multifamily proxy with a table-driven FHFA-style loan-level ERCF calculator that includes subsidy treatment and confidence-based result suppression.

**Architecture:** Expand the backend schema and config to carry rule-required loan inputs, implement the multifamily rule as a table-driven evaluator in `backend/app/engine.py`, then surface per-loan confidence and portfolio missing-data statistics through the API and frontend methodology/results views. Keep the implementation loan-level only and stop before CRT or credit enhancement.

**Tech Stack:** FastAPI, Pydantic, Python unittest, YAML config, Next.js, TypeScript, axios.

---

### Task 1: Expand Rule Inputs and Result Contracts

**Files:**
- Modify: `backend/app/schema.py`
- Modify: `frontend/src/types/api.ts`
- Test: `backend/test_engine.py`

- [ ] **Step 1: Write the failing schema/result test**

```python
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
    )
    result = self.engine.calculate_loan(loan)

    self.assertTrue(hasattr(result, "base_risk_weight"))
    self.assertTrue(hasattr(result, "confidence_score"))
    self.assertTrue(hasattr(result, "missing_input_count"))
    self.assertTrue(hasattr(result, "result_available"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: FAIL because `LoanInput` and `EngineResult` do not yet define the new rule fields.

- [ ] **Step 3: Add the minimal schema/type changes**

```python
class LoanInput(BaseModel):
    # Existing fields...
    original_loan_amount: Optional[float] = None
    rate_type: Optional[str] = None
    interest_only: Optional[bool] = None
    original_term_months: Optional[int] = None
    amortization_term_months: Optional[int] = None
    payment_performance: Optional[str] = None
    government_subsidy_type: Optional[str] = None
    qualifying_unit_share: Optional[float] = None
    total_units: Optional[int] = None
    qualifying_units: Optional[int] = None


class EngineResult(BaseModel):
    loan_id: str
    base_risk_weight: Optional[float] = None
    payment_performance_multiplier: float
    interest_only_multiplier: float
    term_multiplier: float
    amortization_multiplier: float
    loan_size_multiplier: float
    special_product_multiplier: float
    subsidy_multiplier: float
    combined_multiplier: float
    floor_value: float
    floor_applied: bool
    confidence_score: int
    confidence_threshold: int
    missing_input_count: int
    missing_inputs: List[str]
    inferred_inputs: List[str]
    result_available: bool
    final_risk_weight: Optional[float] = None
    capital_amount: Optional[float] = None
```

```ts
export interface LoanInput {
  original_loan_amount?: number;
  rate_type?: "fixed" | "arm";
  interest_only?: boolean;
  original_term_months?: number;
  amortization_term_months?: number;
  payment_performance?: string;
  government_subsidy_type?: string;
  qualifying_unit_share?: number;
  total_units?: number;
  qualifying_units?: number;
}

export interface EngineResult {
  base_risk_weight?: number | null;
  payment_performance_multiplier: number;
  interest_only_multiplier: number;
  term_multiplier: number;
  amortization_multiplier: number;
  loan_size_multiplier: number;
  special_product_multiplier: number;
  subsidy_multiplier: number;
  combined_multiplier: number;
  floor_value: number;
  floor_applied: boolean;
  confidence_score: number;
  confidence_threshold: number;
  missing_input_count: number;
  missing_inputs: string[];
  inferred_inputs: string[];
  result_available: boolean;
  final_risk_weight?: number | null;
  capital_amount?: number | null;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: PASS for the new schema/result contract test, though later tasks may still fail on placeholder engine logic.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schema.py frontend/src/types/api.ts backend/test_engine.py
git commit -m "feat: expand ERCF loan input and result contracts"
```

### Task 2: Replace Scalar Config With FHFA-Style Rule Tables

**Files:**
- Modify: `backend/ercf_config.yaml`
- Test: `backend/test_engine.py`

- [ ] **Step 1: Write the failing config-driven base-table test**

```python
def test_fixed_rate_loan_uses_table_driven_base_risk_weight(self):
    loan = LoanInput(
        loan_id="BASE-TABLE-1",
        original_upb=1000,
        current_upb=1000,
        original_loan_amount=1000,
        dscr=1.55,
        ltv=0.55,
        rate_type="fixed",
        interest_only=False,
        original_term_months=120,
        amortization_term_months=360,
        payment_performance="current",
        property_type="Multifamily",
    )
    result = self.engine.calculate_loan(loan)
    self.assertEqual(result.base_risk_weight, 0.25)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: FAIL because the config still only contains `base_risk_weight`, `ltv_multipliers`, and `dscr_multipliers`.

- [ ] **Step 3: Replace the config shape with rule tables and confidence settings**

```yaml
ltv_bands:
  - key: le_60
    max: 0.60
  - key: le_70
    max: 0.70
  - key: le_80
    max: 0.80
  - key: gt_80
    max: 999.0

dscr_bands:
  - key: le_100
    max: 1.00
  - key: le_125
    max: 1.25
  - key: le_150
    max: 1.50
  - key: gt_150
    max: 999.0

fixed_rate_base_risk_weights:
  le_100: {le_60: 0.55, le_70: 0.65, le_80: 0.85, gt_80: 1.10}
  le_125: {le_60: 0.40, le_70: 0.50, le_80: 0.65, gt_80: 0.90}
  le_150: {le_60: 0.30, le_70: 0.40, le_80: 0.55, gt_80: 0.75}
  gt_150: {le_60: 0.25, le_70: 0.30, le_80: 0.45, gt_80: 0.60}

arm_base_risk_weights:
  le_100: {le_60: 0.60, le_70: 0.75, le_80: 0.95, gt_80: 1.20}
  le_125: {le_60: 0.45, le_70: 0.55, le_80: 0.75, gt_80: 1.00}
  le_150: {le_60: 0.35, le_70: 0.45, le_80: 0.60, gt_80: 0.80}
  gt_150: {le_60: 0.30, le_70: 0.35, le_80: 0.50, gt_80: 0.65}

confidence:
  enabled: true
  minimum_score_for_result: 70
  penalties:
    rate_type: 40
    payment_performance: 20
    original_loan_amount: 15
    interest_only: 10
    original_term_months: 10
    amortization_term_months: 10
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: the base-table test still fails until engine logic is added, but the config now loads without parse errors.

- [ ] **Step 5: Commit**

```bash
git add backend/ercf_config.yaml backend/test_engine.py
git commit -m "feat: add table-driven ERCF policy config"
```

### Task 3: Implement Base Table Lookup and Core Multipliers

**Files:**
- Modify: `backend/app/engine.py`
- Test: `backend/test_engine.py`

- [ ] **Step 1: Write the failing engine tests for rate tables and multipliers**

```python
def test_arm_loan_uses_arm_base_table(self):
    loan = LoanInput(
        loan_id="ARM-1",
        original_upb=1000,
        current_upb=1000,
        original_loan_amount=1000,
        dscr=1.55,
        ltv=0.55,
        rate_type="arm",
        interest_only=False,
        original_term_months=120,
        amortization_term_months=360,
        payment_performance="current",
        property_type="Multifamily",
    )
    result = self.engine.calculate_loan(loan)
    self.assertEqual(result.base_risk_weight, 0.30)


def test_core_multipliers_are_combined_after_base_lookup(self):
    loan = LoanInput(
        loan_id="MULT-1",
        original_upb=1000,
        current_upb=1000,
        original_loan_amount=5000000,
        dscr=1.55,
        ltv=0.55,
        rate_type="fixed",
        interest_only=True,
        original_term_months=180,
        amortization_term_months=420,
        payment_performance="current",
        property_type="Student Housing",
    )
    result = self.engine.calculate_loan(loan)
    self.assertGreater(result.combined_multiplier, 1.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: FAIL because `engine.py` still uses the old scalar multiplier logic.

- [ ] **Step 3: Implement table lookup and multiplier helpers**

```python
def _band_key(value: float, bands: list[dict]) -> str:
    for band in bands:
        if value <= band["max"]:
            return band["key"]
    raise ValueError(f"no band for value {value}")


def _lookup_base_risk_weight(self, loan: LoanInput) -> float:
    rate_table = (
        self.config["fixed_rate_base_risk_weights"]
        if loan.rate_type == "fixed"
        else self.config["arm_base_risk_weights"]
    )
    dscr_key = _band_key(loan.dscr, self.config["dscr_bands"])
    ltv_key = _band_key(loan.ltv, self.config["ltv_bands"])
    return rate_table[dscr_key][ltv_key]


def calculate_loan(self, loan: LoanInput) -> EngineResult:
    base_risk_weight = self._lookup_base_risk_weight(loan)
    payment_performance_multiplier = self._payment_performance_multiplier(loan)
    interest_only_multiplier = self._interest_only_multiplier(loan)
    term_multiplier = self._term_multiplier(loan)
    amortization_multiplier = self._amortization_multiplier(loan)
    loan_size_multiplier = self._loan_size_multiplier(loan)
    special_product_multiplier = self._special_product_multiplier(loan)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: PASS for table lookup and core multiplier tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine.py backend/test_engine.py
git commit -m "feat: implement table-driven ERCF base lookup"
```

### Task 4: Add Confidence Scoring and Result Suppression

**Files:**
- Modify: `backend/app/engine.py`
- Test: `backend/test_engine.py`

- [ ] **Step 1: Write the failing confidence tests**

```python
def test_missing_critical_inputs_reduce_confidence_and_hide_result(self):
    loan = LoanInput(
        loan_id="CONF-1",
        original_upb=1000,
        current_upb=1000,
        dscr=1.2,
        ltv=0.7,
        property_type="Multifamily",
    )
    result = self.engine.calculate_loan(loan)
    self.assertLess(result.confidence_score, result.confidence_threshold)
    self.assertFalse(result.result_available)
    self.assertIsNone(result.final_risk_weight)
    self.assertGreaterEqual(result.missing_input_count, 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: FAIL because confidence and suppression are not implemented.

- [ ] **Step 3: Implement confidence evaluation before final result emission**

```python
def _confidence_details(self, loan: LoanInput) -> tuple[int, list[str], list[str]]:
    penalties = self.config["confidence"]["penalties"]
    missing_inputs: list[str] = []
    score = 100
    for field_name, penalty in penalties.items():
        if getattr(loan, field_name, None) in (None, ""):
            missing_inputs.append(field_name)
            score -= penalty
    return max(score, 0), missing_inputs, []


confidence_score, missing_inputs, inferred_inputs = self._confidence_details(loan)
threshold = self.config["confidence"]["minimum_score_for_result"]
result_available = confidence_score >= threshold
if not result_available:
    return EngineResult(
        loan_id=loan.loan_id,
        base_risk_weight=None,
        ...
        confidence_score=confidence_score,
        confidence_threshold=threshold,
        missing_input_count=len(missing_inputs),
        missing_inputs=missing_inputs,
        inferred_inputs=inferred_inputs,
        result_available=False,
        final_risk_weight=None,
        capital_amount=None,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: PASS for confidence threshold suppression behavior.

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine.py backend/test_engine.py
git commit -m "feat: add ERCF confidence scoring and suppression"
```

### Task 5: Add Subsidy Logic, Floor Logic, and Golden Rule Tests

**Files:**
- Modify: `backend/app/engine.py`
- Modify: `backend/ercf_config.yaml`
- Test: `backend/test_engine.py`

- [ ] **Step 1: Write the failing subsidy and floor tests**

```python
def test_qualifying_subsidy_reduces_final_risk_weight(self):
    loan = LoanInput(
        loan_id="SUBSIDY-1",
        original_upb=1000,
        current_upb=1000,
        original_loan_amount=1000,
        dscr=1.55,
        ltv=0.55,
        rate_type="fixed",
        interest_only=False,
        original_term_months=120,
        amortization_term_months=360,
        payment_performance="current",
        government_subsidy_type="lihtc",
        qualifying_unit_share=1.0,
        property_type="Multifamily",
    )
    result = self.engine.calculate_loan(loan)
    self.assertEqual(result.subsidy_multiplier, 0.6)


def test_floor_applies_when_adjusted_weight_falls_below_twenty_percent(self):
    loan = LoanInput(
        loan_id="FLOOR-1",
        original_upb=1000,
        current_upb=1000,
        original_loan_amount=1000,
        dscr=1.9,
        ltv=0.4,
        rate_type="fixed",
        interest_only=False,
        original_term_months=120,
        amortization_term_months=360,
        payment_performance="current",
        government_subsidy_type="lihtc",
        qualifying_unit_share=1.0,
        property_type="Multifamily",
    )
    result = self.engine.calculate_loan(loan)
    self.assertTrue(result.floor_applied)
    self.assertEqual(result.final_risk_weight, 0.20)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: FAIL because subsidy and floor behavior are not yet implemented.

- [ ] **Step 3: Implement subsidy multiplier and floor application**

```python
def _subsidy_multiplier(self, loan: LoanInput) -> float:
    subsidy_types = self.config["subsidy"]["qualifying_types"]
    if loan.government_subsidy_type not in subsidy_types:
        return 1.0
    share = loan.qualifying_unit_share
    if share is None and loan.qualifying_units is not None and loan.total_units:
        share = loan.qualifying_units / loan.total_units
    if share is None:
        return 1.0
    return (share * 0.6) + ((1 - share) * 1.0)


adjusted_weight = base_risk_weight * combined_multiplier * subsidy_multiplier
floor_value = self.config["risk_weight_floor"]
final_risk_weight = max(floor_value, adjusted_weight)
floor_applied = final_risk_weight == floor_value and adjusted_weight < floor_value
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: PASS for subsidy and floor tests plus prior engine tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine.py backend/ercf_config.yaml backend/test_engine.py
git commit -m "feat: add subsidy multiplier and risk weight floor"
```

### Task 6: Surface Confidence and Missing-Data Statistics Through the API

**Files:**
- Modify: `backend/app/schema.py`
- Modify: `backend/app/main.py`
- Test: `backend/test_engine.py`

- [ ] **Step 1: Write the failing portfolio-statistics test**

```python
def test_portfolio_results_include_per_loan_confidence_and_missing_counts(self):
    loan = LoanInput(
        loan_id="PORT-1",
        original_upb=1000,
        current_upb=1000,
        dscr=1.2,
        ltv=0.7,
        property_type="Multifamily",
    )
    result = self.engine.calculate_loan(loan)
    self.assertTrue(hasattr(result, "missing_input_count"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: FAIL if summary/result wrapper types do not yet include the required statistics.

- [ ] **Step 3: Add portfolio confidence summary fields and aggregate them**

```python
class PortfolioSummary(BaseModel):
    loan_count: int
    loans_with_available_results: int
    loans_with_missing_results: int
    average_confidence_score: float
    median_confidence_score: float
    minimum_confidence_score: int
    total_missing_input_count: int
    missing_input_counts_by_field: dict[str, int]
```

```python
confidence_scores = [res.confidence_score for res in results]
missing_counts = [res.missing_input_count for res in results]
field_counts: dict[str, int] = {}
for res in results:
    for field_name in res.missing_inputs:
        field_counts[field_name] = field_counts.get(field_name, 0) + 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: PASS for portfolio confidence/statistics contract tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schema.py backend/app/main.py backend/test_engine.py
git commit -m "feat: add portfolio confidence statistics"
```

### Task 7: Update Frontend Types, Analytics, and Methodology Presentation

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/app/analytics/page.tsx`
- Modify: `frontend/src/app/calculator/page.tsx`
- Modify: `frontend/src/app/methodology/page.tsx`
- Test: `frontend` build

- [ ] **Step 1: Add the failing frontend presentation expectations**

```ts
type EngineResult = {
  confidence_score: number;
  result_available: boolean;
  missing_input_count: number;
};
```

```tsx
{!result.result_available ? (
  <p>Result unavailable due to missing rule inputs.</p>
) : (
  <p>{(result.final_risk_weight! * 100).toFixed(1)}%</p>
)}
```

- [ ] **Step 2: Run build to verify it fails**

Run: `npm run build`
Expected: FAIL until the pages stop assuming the old `estimated_capital_factor` / `estimated_capital_amount` contract everywhere.

- [ ] **Step 3: Update UI to show per-loan confidence and portfolio missing-data statistics**

```tsx
<CardContent className="p-6">
  <p className="text-sm font-medium text-slate-500">Average Confidence</p>
  <h3 className="text-2xl font-bold text-slate-900 mt-2">
    {summary?.average_confidence_score?.toFixed(0) ?? "0"}%
  </h3>
</CardContent>
```

```tsx
<Card className="shadow-sm border-slate-200">
  <CardHeader>
    <CardTitle>Confidence and Missing Data</CardTitle>
  </CardHeader>
  <CardContent className="text-sm text-slate-600">
    <p>Confidence is reduced when rule-relevant loan fields are missing or inferred.</p>
    <p>Results below the configured threshold are marked unavailable.</p>
  </CardContent>
</Card>
```

- [ ] **Step 4: Run build to verify it passes**

Run: `npm run build`
Expected: PASS with the new result contract and methodology copy.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/app/analytics/page.tsx frontend/src/app/calculator/page.tsx frontend/src/app/methodology/page.tsx
git commit -m "feat: expose ERCF confidence and methodology details in UI"
```

### Task 8: Final Verification and Documentation Sweep

**Files:**
- Modify: `README.md` (if needed)
- Verify: `backend/test_engine.py`
- Verify: `frontend` build

- [ ] **Step 1: Review the spec against the implementation**

Check: `docs/superpowers/specs/2026-04-11-ercf-loan-level-rule-design.md`
Expected: every approved requirement maps to implemented code or explicit out-of-scope behavior.

- [ ] **Step 2: Run backend verification**

Run: `/home/pooh/work/ercf/backend/venv/bin/python -m unittest test_engine.py`
Expected: PASS with all rule, confidence, and portfolio-stat tests green.

- [ ] **Step 3: Run frontend verification**

Run: `npm run build`
Expected: PASS on the branch head.

- [ ] **Step 4: Update top-level docs only if they are now misleading**

```md
## Methodology

The engine now evaluates a loan-level FHFA-style multifamily ERCF rule with configurable confidence scoring and subsidy treatment. CRT and credit enhancement remain out of scope.
```

- [ ] **Step 5: Commit**

```bash
git add README.md backend/test_engine.py frontend/src/app/methodology/page.tsx
git commit -m "docs: align ERCF documentation with refined loan-level rule"
```
