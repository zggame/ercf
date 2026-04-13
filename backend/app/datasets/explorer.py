from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.schema import (
    BreakdownResponse,
    BreakdownRow,
    CohortExplorerResponse,
    CohortSummary,
    DrilldownRow,
    FixedChartPoint,
    FixedChartSeries,
)

from .canonical import (
    BREAKDOWN_METRIC_TO_FIELD,
    SUPPORTED_BREAKDOWN_DIMENSIONS,
    SUPPORTED_FILTER_FIELDS,
    CAPITAL_FACTOR_BANDS,
    FIXED_CHART_CAPITAL_FACTOR_BANDS,
    FIXED_CHART_PROPERTY_TYPE,
    FIXED_CHART_STATE,
    SUMMARY_METRICS,
    WEIGHTED_AVERAGE_FIELDS,
    capital_factor_band_label,
    metric_value,
    sum_numeric,
    weighted_average,
)


class ExplorerService:
    def __init__(self, rows: list[dict[str, Any]]):
        self.rows = rows

    def build_cohort(
        self,
        source: str,
        snapshot: str,
        filters: dict[str, list[Any]],
        breakdown_dimension: str,
        breakdown_metric: str,
    ) -> CohortExplorerResponse:
        self._validate_filters(filters)
        filtered = [
            row
            for row in self.rows
            if row.get("source") == source
            and row.get("snapshot") == snapshot
            and self._matches_filters(row, filters)
        ]

        return CohortExplorerResponse(
            cohort_label=f"{source} {snapshot}",
            summary=self._summarize(filtered),
            fixed_charts=self._fixed_charts(filtered),
            breakdown=self._breakdown(filtered, breakdown_dimension, breakdown_metric),
            drilldown_rows=self._drilldown(filtered),
        )

    @staticmethod
    def _matches_filters(row: dict[str, Any], filters: dict[str, list[Any]]) -> bool:
        for key, values in filters.items():
            if not values:
                continue
            if row.get(key) not in values:
                return False
        return True

    @staticmethod
    def _validate_filters(filters: dict[str, list[Any]]) -> None:
        unsupported_fields = sorted(
            key for key in filters if key not in SUPPORTED_FILTER_FIELDS
        )
        if unsupported_fields:
            joined_fields = ", ".join(unsupported_fields)
            raise ValueError(f"Unsupported cohort filter field(s): {joined_fields}")

    def _summarize(self, rows: list[dict[str, Any]]) -> CohortSummary:
        summary_values: dict[str, float | int] = {"loan_count": len(rows)}

        for metric_name, field_name in SUMMARY_METRICS.items():
            summary_values[metric_name] = sum_numeric(rows, field_name)

        for metric_name, field_name in WEIGHTED_AVERAGE_FIELDS.items():
            summary_values[metric_name] = weighted_average(rows, field_name)

        return CohortSummary(**summary_values)

    def _fixed_charts(self, rows: list[dict[str, Any]]) -> dict[str, FixedChartSeries]:
        return {
            FIXED_CHART_CAPITAL_FACTOR_BANDS: self._chart_series(
                self._capital_factor_band_counts(rows)
            ),
            FIXED_CHART_PROPERTY_TYPE: self._chart_series(
                self._category_metric(rows, "property_type", "loan_count")
            ),
            FIXED_CHART_STATE: self._chart_series(
                self._category_metric(rows, "state", "loan_count")
            ),
        }

    def _breakdown(
        self,
        rows: list[dict[str, Any]],
        dimension: str,
        metric: str,
    ) -> BreakdownResponse:
        if dimension not in SUPPORTED_BREAKDOWN_DIMENSIONS:
            raise ValueError(f"Unsupported breakdown dimension: {dimension}")
        if metric not in BREAKDOWN_METRIC_TO_FIELD:
            raise ValueError(f"Unsupported breakdown metric: {metric}")

        buckets = self._category_metric(rows, dimension, metric)
        return BreakdownResponse(
            dimension=dimension,
            metric=metric,
            rows=[
                BreakdownRow(key=key, value=value)
                for key, value in sorted(
                    buckets.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ],
        )

    def _drilldown(self, rows: list[dict[str, Any]]) -> list[DrilldownRow]:
        ordered_rows = sorted(
            rows,
            key=lambda row: str(row.get("loan_id", "")),
        )
        return [
            DrilldownRow(
                loan_id=str(row.get("loan_id", "")),
                source=str(row.get("source", "")),
                reporting_date=row.get("reporting_date"),
                property_type=row.get("property_type"),
                state=row.get("state"),
                current_upb=float(row.get("current_upb", 0.0) or 0.0),
                dscr=float(row.get("dscr", 0.0) or 0.0),
                ltv=float(row.get("ltv", 0.0) or 0.0),
                estimated_capital_factor=float(
                    row.get("estimated_capital_factor", 0.0) or 0.0
                ),
                estimated_capital_amount=float(
                    row.get("estimated_capital_amount", 0.0) or 0.0
                ),
            )
            for row in ordered_rows
        ]

    def _capital_factor_band_counts(self, rows: list[dict[str, Any]]) -> dict[str, float]:
        counts = {label: 0.0 for label, _, _ in CAPITAL_FACTOR_BANDS}
        for row in rows:
            value = float(row.get("estimated_capital_factor", 0.0) or 0.0)
            counts[capital_factor_band_label(value)] += 1.0
        return counts

    def _category_metric(
        self,
        rows: list[dict[str, Any]],
        dimension: str,
        metric: str,
    ) -> dict[str, float]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            key = row.get(dimension)
            grouped[str(key if key not in (None, "") else "Unknown")].append(row)

        return {
            key: metric_value(group_rows, metric)
            for key, group_rows in grouped.items()
        }

    @staticmethod
    def _chart_series(points_by_label: dict[str, float]) -> FixedChartSeries:
        return FixedChartSeries(
            points=[
                FixedChartPoint(label=label, value=value)
                for label, value in sorted(points_by_label.items())
            ]
        )
