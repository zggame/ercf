# ERCF Loan-Level Multifamily Rule Design

## Goal

Refine the current simplified ERCF-style proxy into a closer loan-level implementation of the FHFA Enterprise Regulatory Capital Framework for multifamily mortgage exposures.

This design is intentionally limited to the loan-level calculation. It does not include:

- CRT treatment
- credit enhancement treatment
- portfolio aggregation logic beyond summing already-computed loan results
- advanced-approach capital logic

The target is a transparent, table-driven standardized-approach engine for multifamily loans, including the government-subsidy multiplier.

## Scope

In scope:

- multifamily base risk-weight lookup using FHFA-style tables
- separate treatment for fixed-rate and adjustable-rate loans
- loan-level risk multipliers
- government-subsidy multiplier
- 20 percent minimum adjusted risk-weight floor
- capital amount calculation from current UPB
- methodology documentation and result transparency

Out of scope:

- CRT and retained-risk calculations
- external credit enhancement
- non-multifamily asset classes
- perfect replication of every Enterprise internal implementation detail not explicit in the rule text

## Calculation Overview

The loan-level calculation will use the following shape:

`Final Risk Weight = max(20%, Base Risk Weight × Combined Loan-Level Multipliers × Subsidy Multiplier)`

`Capital Amount = Current UPB × Final Risk Weight`

The sequence matters:

1. Determine the base risk weight from the multifamily table.
2. Apply the applicable loan-level multipliers.
3. Apply the government-subsidy multiplier if the loan qualifies.
4. Apply the 20 percent minimum adjusted risk-weight floor.
5. Multiply the final risk weight by current UPB to derive capital amount.

## Base Risk Weight

The current app uses one scalar `base_risk_weight`. That is not close enough to the FHFA rule.

The refined engine will instead use a table-driven lookup:

- one base table for fixed-rate multifamily loans
- one base table for adjustable-rate multifamily loans
- rows keyed by DSCR band
- columns keyed by LTV band
- each cell storing the base risk weight

The engine will:

- determine the loan’s `rate_type`
- find the DSCR band containing the loan
- find the LTV band containing the loan
- return the matching base risk weight from the corresponding table

This keeps the implementation auditable and close to the rule text.

## Loan-Level Multipliers

After base risk weight lookup, the engine will multiply by the applicable loan-level multipliers.

The first implementation should support the core factors that are explicitly loan-level and practical to collect:

- payment performance
- interest-only status
- original term
- original amortization term
- original loan amount
- special property / business-purpose flags where the rule distinguishes them

The multiplier set will be config-driven so the engine remains a generic evaluator rather than a hard-coded rule bundle.

## Government-Subsidy Multiplier

This design includes the multifamily government-subsidy treatment added in the FHFA amendments.

At a minimum, the engine should support:

- fully qualifying subsidized property treatment
- non-qualifying treatment
- weighted treatment for loans secured by multiple properties or mixed affordable / non-affordable unit populations

The first implementation will model this as a `subsidy_multiplier` with:

- `0.6` for qualifying subsidized exposure
- `1.0` for non-qualifying exposure
- weighted-average treatment where only a portion qualifies

The weighted approach should be driven by unit counts or a directly supplied qualifying-share percentage.

## Input Model

The rule needs more loan detail than the current proxy. The input model should be expanded with fields that are directly relevant to the calculation.

### Core balance and collateral inputs

#### `current_upb`

Used to convert final risk weight into capital amount.

- required
- non-negative
- treated as the exposure balance used in the capital amount output

#### `original_loan_amount`

Needed for loan-size multiplier logic.

- required for precise rule treatment
- should default conservatively if unavailable
- may differ from `original_upb` if the app later distinguishes accounting versus origination semantics

#### `ltv`

Used for base risk-weight table lookup.

- required
- decimal format, not percentage string
- should be validated to allow values above `1.0` because the rule still needs to handle distressed or unusual cases

#### `dscr`

Used for base risk-weight table lookup.

- required
- numeric
- should preserve enough precision to avoid incorrect band assignment near boundaries

### Rate and structure inputs

#### `rate_type`

Determines whether the loan uses the fixed-rate or adjustable-rate base table.

- required for rule-accurate treatment
- allowed values should be constrained, such as `fixed` and `arm`

#### `interest_only`

Used for the interest-only multiplier.

- boolean
- if unknown, v1 should use conservative treatment rather than preferred treatment

#### `original_term_months`

Used for term-based multiplier logic.

- integer
- should represent original contractual loan term, not remaining term

#### `amortization_term_months`

Used for amortization-based multiplier logic.

- integer
- should reflect original amortization schedule

### Credit performance inputs

#### `payment_performance`

Used for delinquency / payment-performance multiplier logic.

- should be modeled as an explicit categorical field rather than inferred from free-form status text
- v1 only needs enough resolution to support rule distinctions such as performing versus delinquent beyond threshold

#### `delinquency_days`

Optional supporting input if the source data provides day-count delinquency instead of a pre-bucketed status.

- if present, the engine can derive `payment_performance`
- if both are present, validation should prevent contradictory values

### Property and program inputs

#### `property_type`

The current app uses this for a simple multiplier. Under the refined rule, this field should remain available but should only drive behavior where the FHFA-style framework explicitly differentiates property subtypes.

- example subtypes may include student housing or other special multifamily categories
- unsupported values should fall back to neutral treatment unless a conservative rule is needed

#### `government_subsidy_type`

Identifies whether the collateral qualifies for subsidy treatment.

- modeled as a constrained categorical field
- examples may include LIHTC, project-based rental assistance, Section 515, or approved state / local affordable housing subsidy structures
- a plain boolean is not sufficient if we want auditability

#### `qualifying_unit_share`

Represents the share of units qualifying for subsidy treatment when the exposure is mixed.

- decimal from `0.0` to `1.0`
- allows weighted subsidy treatment
- can be derived from unit counts if raw counts are provided instead

#### `total_units`

Optional support field for deriving weighted subsidy treatment.

- useful for auditability and for future UI validation

#### `qualifying_units`

Optional support field for deriving `qualifying_unit_share`.

- if present with `total_units`, the engine can compute the weighted share directly

## Conservative Fallback Rules

The first implementation should avoid optimistic assumptions when required rule inputs are missing.

Preferred policy:

- missing rate type: fail validation rather than guess
- missing payment-performance field: default to neutral or conservative treatment only if the product requirement allows it
- missing subsidy evidence: treat as non-qualifying
- missing qualifying-share data for mixed subsidy loans: treat as non-qualifying unless explicitly provided

This avoids overstating subsidy relief or understating capital.

## Confidence and Result Availability

The engine should expose a confidence measure that reflects how complete the loan-level rule inputs are.

The purpose is not to judge whether the math executed correctly. The purpose is to indicate whether the result is supported by enough real loan data to be analytically credible.

### Confidence concept

The confidence score should represent input completeness for rule-relevant fields.

- high confidence means the engine used mostly direct, required loan inputs
- medium confidence means some fields were inferred or defaulted conservatively
- low confidence means too many rule-relevant elements were missing, so the output should not be presented as a usable result

### Confidence calculation

The score should be config-driven and based on missing or inferred elements.

Recommended structure:

- start from `100`
- subtract configured penalties for each missing, inferred, or downgraded input
- clamp the result to `0` through `100`

Penalty weights should be configurable by field or field group. Fields that materially change the FHFA-style rule should carry larger penalties than descriptive or supporting fields.

Example high-impact confidence inputs:

- missing `rate_type`
- missing `payment_performance`
- missing `original_loan_amount`
- missing `interest_only`
- missing `original_term_months`
- missing `amortization_term_months`
- missing subsidy qualification evidence when subsidy treatment is claimed

Example lower-impact confidence inputs:

- missing supporting unit-count detail when a direct qualifying share was still provided
- missing descriptive property subtype information when neutral treatment is still valid

### Configurable threshold

The minimum confidence threshold should be configurable in policy config.

Recommended config items:

- `confidence.enabled`
- `confidence.minimum_score_for_result`
- `confidence.penalties`
- `confidence.missing_result_code`

If the score falls below the configured minimum:

- the engine should mark the rule result as unavailable or missing
- the API should still return the confidence details and the missing-input reasons
- the UI should show that the loan does not have enough information for a credible ERCF-style result

This is preferable to emitting a seemingly precise number from heavily defaulted data.

### Output behavior

The result model should include:

- `confidence_score`
- `confidence_threshold`
- `result_available`
- `missing_input_count`
- `missing_inputs`
- `inferred_inputs`
- `confidence_notes`

If `result_available` is `false`, the result should not present a final risk weight or capital amount as authoritative. The response can either:

- set the numeric result fields to `null`, or
- return a dedicated missing-result status with explanation

The implementation should choose one of those patterns consistently and document it in the API contract.

### Per-loan requirement

Every loan-level result must carry its own confidence fields.

This is required even when the result is available and even when the score is high. Confidence is part of the analytical output, not a special-case warning field.

At minimum, every loan result should report:

- `confidence_score`
- `confidence_threshold`
- `missing_input_count`
- `result_available`

### Portfolio tracking and statistics

Missing data should also be tracked across the portfolio so users can understand whether weak coverage is isolated or systemic.

Recommended portfolio-level statistics:

- `total_loans`
- `loans_with_available_results`
- `loans_with_missing_results`
- `average_confidence_score`
- `median_confidence_score`
- `minimum_confidence_score`
- `total_missing_input_count`
- `missing_input_counts_by_field`

This allows the UI to answer questions such as:

- how many loans are below the confidence threshold
- which input fields most often prevent a usable result
- whether the dataset is generally complete enough for analysis

The `missing_input_counts_by_field` structure should be keyed by input name and count how many loans are missing each rule-relevant field.

## Configuration Design

The rule content should move into structured config rather than stay embedded in Python logic.

Recommended config sections:

- `fixed_rate_base_risk_weights`
- `arm_base_risk_weights`
- `ltv_bands`
- `dscr_bands`
- `multipliers.payment_performance`
- `multipliers.interest_only`
- `multipliers.original_term`
- `multipliers.amortization_term`
- `multipliers.original_loan_amount`
- `multipliers.special_product`
- `subsidy`
- `risk_weight_floor`
- `confidence`

The engine should:

- validate that every table is complete
- fail fast on malformed config
- keep the policy data easy to compare against FHFA source material

## Engine Behavior

The engine should expose a deterministic step-by-step evaluation:

1. validate required fields
2. select base table from `rate_type`
3. look up base risk weight from DSCR and LTV
4. compute each applicable loan-level multiplier
5. compute subsidy multiplier
6. compute confidence from missing and inferred inputs
7. if confidence is below threshold, return missing-result status with details
8. otherwise multiply base weight by all multipliers
9. apply the 20 percent floor
10. compute capital amount from `current_upb`

The result should include calculation detail, not just the final number.

## Output Model

The result payload should expose at least:

- `loan_id`
- `base_risk_weight`
- `payment_performance_multiplier`
- `interest_only_multiplier`
- `term_multiplier`
- `amortization_multiplier`
- `loan_size_multiplier`
- `special_product_multiplier`
- `subsidy_multiplier`
- `combined_multiplier`
- `floor_value`
- `floor_applied`
- `confidence_score`
- `confidence_threshold`
- `result_available`
- `missing_inputs`
- `inferred_inputs`
- `final_risk_weight`
- `capital_amount`

This supports UI explanation and testing.

## Methodology Page

The methodology page should stop describing the engine as a small custom proxy once the refined rule lands.

It should explain:

- that the app uses a loan-level FHFA-inspired multifamily ERCF calculation
- the formula order
- the key input fields and why they matter
- the confidence framework and when results are suppressed as missing
- where simplified treatment still exists
- that CRT and credit enhancement remain out of scope

The input reference should be written for analysts, not developers.

## Error Handling

The rule implementation should distinguish clearly between:

- unsupported calculation cases
- missing required data
- malformed configuration

Recommended behavior:

- missing required loan fields: request-level validation error
- unknown categorical values: validation error unless explicitly mapped
- malformed config: startup failure, not runtime silent fallback

## Testing Strategy

Tests should cover:

- base table lookup for fixed-rate loans
- base table lookup for adjustable-rate loans
- boundary values at DSCR and LTV cutoffs
- payment-performance multiplier application
- interest-only multiplier application
- term and amortization multiplier application
- loan-size multiplier application
- subsidy multiplier at `0`, `1`, and weighted mixed cases
- 20 percent floor behavior
- capital amount calculation
- confidence penalties for missing critical inputs
- result suppression when confidence falls below threshold
- configurable threshold behavior
- validation errors for missing rule-critical fields

Golden tests should use representative example loans with explicitly expected final risk weights.

## Implementation Approach

Recommended implementation order:

1. extend schema and TypeScript types for required loan-level inputs
2. replace scalar base-weight config with multifamily rule tables
3. update engine to evaluate the table-driven rule
4. add subsidy multiplier logic
5. extend output detail fields
6. update methodology documentation and UI copy
7. update tests for both happy path and boundary behavior

## Risks

- exact FHFA tables are dense, so transcription errors are a real risk
- some public datasets may not provide all required rule inputs
- if inputs are missing too often, the app may become validation-heavy unless upload mapping is improved
- subsidy qualification can be overstated if documentation or unit-share evidence is weak

## Decision Summary

Approved design direction:

- implement a loan-level multifamily ERCF engine
- include the government-subsidy multiplier
- exclude CRT and credit enhancement for now
- keep the implementation table-driven and auditable
