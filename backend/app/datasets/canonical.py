from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Any


SOURCE_FANNIE_MAE = "fannie_mae"
SOURCE_FREDDIE_MAC = "freddie_mac"
SUPPORTED_SOURCES = frozenset({SOURCE_FANNIE_MAE, SOURCE_FREDDIE_MAC})

FIXED_CHART_CAPITAL_FACTOR_BANDS = "capital_factor_bands"
FIXED_CHART_PROPERTY_TYPE = "property_type_mix"
FIXED_CHART_STATE = "state_mix"

BREAKDOWN_DIMENSION_STATE = "state"
BREAKDOWN_DIMENSION_PROPERTY_TYPE = "property_type"
SUPPORTED_BREAKDOWN_DIMENSIONS = frozenset(
    {
        BREAKDOWN_DIMENSION_STATE,
        BREAKDOWN_DIMENSION_PROPERTY_TYPE,
        "rate_type",
        "interest_only",
    }
)

SUPPORTED_FILTER_FIELDS = frozenset(
    {
        BREAKDOWN_DIMENSION_STATE,
        BREAKDOWN_DIMENSION_PROPERTY_TYPE,
        "is_affordable",
        "msa",
        "rate_type",
        "interest_only",
        "payment_performance",
    }
)

SNAPSHOT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

SUMMARY_METRICS = {
    "original_upb_total": "original_upb",
    "current_upb_total": "current_upb",
    "total_estimated_capital_amount": "estimated_capital_amount",
}

WEIGHTED_AVERAGE_FIELDS = {
    "wa_dscr": "dscr",
    "wa_ltv": "ltv",
    "wa_estimated_capital_factor": "estimated_capital_factor",
}

BREAKDOWN_METRIC_TO_FIELD = {
    "loan_count": None,
    "original_upb_total": "original_upb",
    "current_upb_total": "current_upb",
    "total_estimated_capital_amount": "estimated_capital_amount",
}

CAPITAL_FACTOR_BANDS = (
    ("0.0-0.5", 0.0, 0.5),
    ("0.5-1.0", 0.5, 1.0),
    ("1.0-1.5", 1.0, 1.5),
    ("1.5+", 1.5, None),
)


def sum_numeric(rows: Iterable[dict[str, Any]], field: str) -> float:
    return sum(float(row.get(field, 0.0) or 0.0) for row in rows)


def weighted_average(
    rows: Iterable[dict[str, Any]],
    field: str,
    *,
    weight_field: str = "current_upb",
) -> float:
    total_weight = 0.0
    weighted_total = 0.0

    for row in rows:
        weight = float(row.get(weight_field, 0.0) or 0.0)
        value = float(row.get(field, 0.0) or 0.0)
        total_weight += weight
        weighted_total += value * weight

    if total_weight == 0.0:
        return 0.0
    return weighted_total / total_weight


def metric_value(rows: Iterable[dict[str, Any]], metric: str) -> float:
    field = BREAKDOWN_METRIC_TO_FIELD.get(metric)
    if metric == "loan_count":
        return float(sum(1 for _ in rows))
    if field is None:
        raise ValueError(f"Unsupported breakdown metric: {metric}")
    return sum_numeric(rows, field)


def capital_factor_band_label(value: float) -> str:
    for label, lower_bound, upper_bound in CAPITAL_FACTOR_BANDS:
        if value >= lower_bound and (upper_bound is None or value < upper_bound):
            return label
    return CAPITAL_FACTOR_BANDS[-1][0]
