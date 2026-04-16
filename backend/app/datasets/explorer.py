from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

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
from .duckdb_store import DuckDBStore


class ExplorerService:
    def __init__(
        self,
        rows: list[dict[str, Any]],
        curated_store: Optional[Any] = None,
    ):
        self.rows = rows
        self.curated_store = curated_store

    def build_cohort(
        self,
        source: str,
        snapshot: str,
        filters: dict[str, list[Any]],
        breakdown_dimension: str,
        breakdown_metric: str,
    ) -> CohortExplorerResponse:
        self._validate_filters(filters)

        if self.curated_store is not None:
            path = self.curated_store.get_parquet_path(source, snapshot)
            use_duckdb = path.exists() and path.suffix == ".parquet"

            if use_duckdb:
                summary = self._duckdb_summarize(
                    source, snapshot, filters, breakdown_dimension, breakdown_metric
                )
                breakdown = self._duckdb_breakdown(
                    source, snapshot, filters, breakdown_dimension, breakdown_metric
                )
                fixed_charts = self._duckdb_fixed_charts(
                    source, snapshot, filters, breakdown_dimension
                )
                drilldown_rows = self._duckdb_drilldown(
                    source, snapshot, filters, breakdown_dimension, breakdown_metric
                )

                return CohortExplorerResponse(
                    cohort_label=f"{source} {snapshot}",
                    summary=summary,
                    fixed_charts=fixed_charts,
                    breakdown=breakdown,
                    drilldown_rows=drilldown_rows,
                )

            fallback_rows = self.curated_store.load_rows(source, snapshot)
            filtered = [
                row
                for row in fallback_rows
                if row.get("source") == source
                and row.get("snapshot") == snapshot
                and self._matches_filters(row, filters)
            ]
        else:
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

    def _duckdb_summarize(
        self,
        source: str,
        snapshot: str,
        filters: dict[str, list[Any]],
        breakdown_dimension: str,
        breakdown_metric: str,
    ) -> CohortSummary:
        path = self.curated_store.get_parquet_path(source, snapshot)
        db = DuckDBStore()
        where_clause = self._build_where_clause(source, snapshot, filters)

        query = f"""
            SELECT
                COUNT(*) AS loan_count,
                COALESCE(SUM(current_upb), 0.0) AS current_upb_total,
                COALESCE(SUM(original_upb), 0.0) AS original_upb_total,
                COALESCE(SUM(dscr * current_upb) / NULLIF(SUM(current_upb), 0), 0.0) AS wa_dscr,
                COALESCE(SUM(ltv * current_upb) / NULLIF(SUM(current_upb), 0), 0.0) AS wa_ltv,
                COALESCE(SUM(estimated_capital_factor * current_upb) / NULLIF(SUM(current_upb), 0), 0.0) AS wa_estimated_capital_factor,
                COALESCE(SUM(estimated_capital_amount), 0.0) AS total_estimated_capital_amount
            FROM read_parquet('{path.as_posix()}')
            {where_clause}
        """

        with db.connect() as conn:
            df = conn.execute(query).fetch_df()

        row_data = df.iloc[0]
        return CohortSummary(
            loan_count=int(row_data["loan_count"]),
            current_upb_total=float(row_data["current_upb_total"]),
            original_upb_total=float(row_data["original_upb_total"]),
            wa_dscr=float(row_data["wa_dscr"]),
            wa_ltv=float(row_data["wa_ltv"]),
            wa_estimated_capital_factor=float(row_data["wa_estimated_capital_factor"]),
            total_estimated_capital_amount=float(
                row_data["total_estimated_capital_amount"]
            ),
        )

    def _duckdb_breakdown(
        self,
        source: str,
        snapshot: str,
        filters: dict[str, list[Any]],
        dimension: str,
        metric: str,
    ) -> BreakdownResponse:
        if dimension not in SUPPORTED_BREAKDOWN_DIMENSIONS:
            raise ValueError(f"Unsupported breakdown dimension: {dimension}")
        if metric not in BREAKDOWN_METRIC_TO_FIELD:
            raise ValueError(f"Unsupported breakdown metric: {metric}")

        path = self.curated_store.get_parquet_path(source, snapshot)
        db = DuckDBStore()
        where_clause = self._build_where_clause(source, snapshot, filters)

        field = BREAKDOWN_METRIC_TO_FIELD[metric]
        if metric == "loan_count":
            agg_expr = "COUNT(*) AS value"
        else:
            agg_expr = f"SUM({field}) AS value"

        query = f"""
            SELECT
                COALESCE({dimension}, 'Unknown') AS key,
                {agg_expr}
            FROM read_parquet('{path.as_posix()}')
            {where_clause}
            GROUP BY COALESCE({dimension}, 'Unknown')
            ORDER BY value DESC
        """

        with db.connect() as conn:
            df = conn.execute(query).fetch_df()

        return BreakdownResponse(
            dimension=dimension,
            metric=metric,
            rows=[
                BreakdownRow(key=str(row["key"]), value=float(row["value"]))
                for row in df.to_dict(orient="records")
            ],
        )

    def _duckdb_fixed_charts(
        self,
        source: str,
        snapshot: str,
        filters: dict[str, list[Any]],
        breakdown_dimension: str,
    ) -> dict[str, FixedChartSeries]:
        path = self.curated_store.get_parquet_path(source, snapshot)
        db = DuckDBStore()
        where_clause = self._build_where_clause(source, snapshot, filters)

        cf_bands_query = f"""
            SELECT
                CASE
                    WHEN estimated_capital_factor < 0.5 THEN '0.0-0.5'
                    WHEN estimated_capital_factor < 1.0 THEN '0.5-1.0'
                    WHEN estimated_capital_factor < 1.5 THEN '1.0-1.5'
                    ELSE '1.5+'
                END AS band,
                COUNT(*) AS count
            FROM read_parquet('{path.as_posix()}')
            {where_clause}
            GROUP BY band
            ORDER BY
                CASE band
                    WHEN '0.0-0.5' THEN 1
                    WHEN '0.5-1.0' THEN 2
                    WHEN '1.0-1.5' THEN 3
                    WHEN '1.5+' THEN 4
                END
        """

        property_type_query = f"""
            SELECT
                COALESCE(property_type, 'Unknown') AS prop_type,
                COUNT(*) AS count
            FROM read_parquet('{path.as_posix()}')
            {where_clause}
            GROUP BY COALESCE(property_type, 'Unknown')
            ORDER BY count DESC
        """

        state_query = f"""
            SELECT
                COALESCE(state, 'Unknown') AS st,
                COUNT(*) AS count
            FROM read_parquet('{path.as_posix()}')
            {where_clause}
            GROUP BY COALESCE(state, 'Unknown')
            ORDER BY count DESC
        """

        with db.connect() as conn:
            cf_df = conn.execute(cf_bands_query).fetch_df()
            prop_df = conn.execute(property_type_query).fetch_df()
            state_df = conn.execute(state_query).fetch_df()

        cf_points = [
            FixedChartPoint(label=str(row["band"]), value=float(row["count"]))
            for row in cf_df.to_dict(orient="records")
        ]

        prop_points = [
            FixedChartPoint(label=str(row["prop_type"]), value=float(row["count"]))
            for row in prop_df.to_dict(orient="records")
        ]

        state_points = [
            FixedChartPoint(label=str(row["st"]), value=float(row["count"]))
            for row in state_df.to_dict(orient="records")
        ]

        return {
            FIXED_CHART_CAPITAL_FACTOR_BANDS: FixedChartSeries(points=cf_points),
            FIXED_CHART_PROPERTY_TYPE: FixedChartSeries(points=prop_points),
            FIXED_CHART_STATE: FixedChartSeries(points=state_points),
        }

    def _duckdb_drilldown(
        self,
        source: str,
        snapshot: str,
        filters: dict[str, list[Any]],
        breakdown_dimension: str,
        breakdown_metric: str,
        limit: int = 1000,
    ) -> list[DrilldownRow]:
        path = self.curated_store.get_parquet_path(source, snapshot)
        db = DuckDBStore()
        where_clause = self._build_where_clause(source, snapshot, filters)

        query = f"""
            SELECT * EXCLUDE (source, snapshot)
            FROM read_parquet('{path.as_posix()}')
            {where_clause}
            ORDER BY loan_id
            LIMIT {limit}
        """

        with db.connect() as conn:
            df = conn.execute(query).fetch_df()

        rows = df.where(df.notnull(), None).to_dict(orient="records")

        ordered_rows = sorted(rows, key=lambda row: str(row.get("loan_id", "")))
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
                note_rate=row.get("note_rate"),
                original_term_months=row.get("original_term_months"),
                amortization_term_months=row.get("amortization_term_months"),
                interest_only_term=row.get("interest_only_term"),
                interest_only=row.get("interest_only"),
                rate_type=row.get("rate_type"),
                is_fixed_rate=row.get("is_fixed_rate"),
                payment_performance=row.get("payment_performance"),
                total_units=row.get("total_units"),
                occupancy_rate=row.get("occupancy_rate"),
                is_affordable=row.get("is_affordable"),
            )
            for row in ordered_rows
        ]

    @staticmethod
    def _build_where_clause(
        source: str, snapshot: str, filters: dict[str, list[Any]]
    ) -> str:
        conditions = [f"source = '{source}'", f"snapshot = '{snapshot}'"]

        for key, values in filters.items():
            if not values:
                continue
            if isinstance(values[0], str):
                quoted = [f"'{v}'" for v in values]
                conditions.append(f"{key} IN ({', '.join(quoted)})")
            elif isinstance(values[0], (int, float)):
                conditions.append(f"{key} IN ({', '.join(str(v) for v in values)})")

        return "WHERE " + " AND ".join(conditions)

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
                note_rate=row.get("note_rate"),
                original_term_months=row.get("original_term_months"),
                amortization_term_months=row.get("amortization_term_months"),
                interest_only_term=row.get("interest_only_term"),
                interest_only=row.get("interest_only"),
                rate_type=row.get("rate_type"),
                is_fixed_rate=row.get("is_fixed_rate"),
                payment_performance=row.get("payment_performance"),
                total_units=row.get("total_units"),
                occupancy_rate=row.get("occupancy_rate"),
                is_affordable=row.get("is_affordable"),
            )
            for row in ordered_rows
        ]

    def _capital_factor_band_counts(
        self, rows: list[dict[str, Any]]
    ) -> dict[str, float]:
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
            key: metric_value(group_rows, metric) for key, group_rows in grouped.items()
        }

    @staticmethod
    def _chart_series(points_by_label: dict[str, float]) -> FixedChartSeries:
        return FixedChartSeries(
            points=[
                FixedChartPoint(label=label, value=value)
                for label, value in sorted(points_by_label.items())
            ]
        )
