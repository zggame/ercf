from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.engine import ERCFEngine
from app.schema import LoanInput

from app.datasets.canonical import SOURCE_FANNIE_MAE, SOURCE_FREDDIE_MAC


FREDDIE_QUARTER_PATTERN = re.compile(r"^y(?P<year>\d{2})q(?P<quarter>[1-4])$")


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        value = value.replace("$", "").replace(",", "")
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(numeric):
        return None
    return numeric


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _parse_freddie_quarter(value: Any) -> tuple[int, int] | None:
    quarter = _clean_text(value)
    if quarter is None:
        return None
    match = FREDDIE_QUARTER_PATTERN.fullmatch(quarter.lower())
    if not match:
        return None
    year_two_digits = int(match.group("year"))
    year = 1900 + year_two_digits if year_two_digits >= 90 else 2000 + year_two_digits
    quarter_number = int(match.group("quarter"))
    return year, quarter_number


def _freddie_quarter_snapshot(value: Any) -> str:
    parsed = _parse_freddie_quarter(value)
    if not parsed:
        raise ValueError(f"Invalid Freddie quarter value: {value!r}")
    year, quarter_number = parsed
    return f"{year}Q{quarter_number}"


def _freddie_quarter_end_date(value: Any) -> date | None:
    parsed = _parse_freddie_quarter(value)
    if not parsed:
        return None
    year, quarter_number = parsed
    month = quarter_number * 3
    if month in {3, 12}:
        day = 31
    else:
        day = 30
    return date(year, month, day)


def _normalize_ltv(value: Any) -> float:
    numeric = _parse_float(value) or 0.0
    if numeric > 1.0:
        return numeric / 100.0
    return numeric


def _currency_value(value: Any) -> float:
    return _parse_float(value) or 0.0


def _rows_with_reporting_date(
    frame: pd.DataFrame,
    column_name: str,
    target_date: date,
) -> pd.DataFrame:
    parsed_dates = pd.to_datetime(frame[column_name], errors="coerce").dt.date
    return frame.loc[parsed_dates == target_date].copy()


def _row_to_output(
    *,
    source: str,
    snapshot: str,
    loan_input: LoanInput,
    result: Any,
    reporting_date: date | None = None,
    msa: str | None = None,
) -> dict[str, Any]:
    return {
        "loan_id": loan_input.loan_id,
        "source": source,
        "snapshot": snapshot,
        "reporting_date": reporting_date.isoformat() if reporting_date else None,
        "state": loan_input.state,
        "property_type": loan_input.property_type,
        "current_upb": loan_input.current_upb,
        "original_upb": loan_input.original_upb,
        "dscr": loan_input.dscr,
        "ltv": loan_input.ltv,
        "estimated_capital_factor": result.estimated_capital_factor,
        "estimated_capital_amount": result.estimated_capital_amount,
        "is_affordable": loan_input.is_affordable,
        "msa": msa,
    }


def _normalize_freddie_records(
    records: list[dict[str, Any]],
    *,
    snapshot: str | None,
    engine: ERCFEngine,
) -> list[dict[str, Any]]:
    latest_quarter = max(
        (quarter for quarter in (_parse_freddie_quarter(row.get("quarter")) for row in records) if quarter is not None),
        default=None,
    )
    if latest_quarter is None:
        return []

    latest_rows = [
        row
        for row in records
        if _parse_freddie_quarter(row.get("quarter")) == latest_quarter
    ]
    resolved_snapshot = snapshot or f"{latest_quarter[0]}Q{latest_quarter[1]}"
    reporting_date = _freddie_quarter_end_date(f"y{str(latest_quarter[0])[-2:]}q{latest_quarter[1]}")

    output_rows: list[dict[str, Any]] = []
    for row in latest_rows:
        loan_input = LoanInput(
            loan_id=str(row.get("lnno", "")).strip(),
            original_upb=_currency_value(row.get("amt_upb_pch")),
            current_upb=_currency_value(row.get("amt_upb_endg")),
            dscr=_parse_float(row.get("rate_dcr")) or 0.0,
            ltv=_normalize_ltv(row.get("rate_ltv")),
            property_type="Multifamily",
            is_affordable=False,
            state=_clean_text(row.get("code_st")),
            reporting_date=reporting_date,
        )
        result = engine.calculate_loan(loan_input)
        output_rows.append(
            _row_to_output(
                source=SOURCE_FREDDIE_MAC,
                snapshot=resolved_snapshot,
                loan_input=loan_input,
                result=result,
                reporting_date=reporting_date,
                msa=_clean_text(row.get("geographical_region")),
            )
        )

    return output_rows


def _normalize_fannie_records(
    records: list[dict[str, Any]],
    *,
    snapshot: str | None,
    engine: ERCFEngine,
) -> list[dict[str, Any]]:
    dated_rows: list[tuple[date, dict[str, Any]]] = []
    for row in records:
        reporting_date = _parse_date(row.get("Reporting Period Date"))
        if reporting_date is not None:
            dated_rows.append((reporting_date, row))

    if not dated_rows:
        return []

    latest_reporting_date = max(reporting_date for reporting_date, _ in dated_rows)
    latest_rows = [
        row for reporting_date, row in dated_rows if reporting_date == latest_reporting_date
    ]
    resolved_snapshot = snapshot or latest_reporting_date.strftime("%Y%m")

    output_rows: list[dict[str, Any]] = []
    for row in latest_rows:
        original_upb = _currency_value(row.get("Original UPB"))
        current_upb = _currency_value(row.get("UPB - Current"))
        loan_input = LoanInput(
            loan_id=str(row.get("Loan Number", "")).strip(),
            original_upb=original_upb or current_upb,
            current_upb=current_upb,
            dscr=_parse_float(row.get("Underwritten DSCR")) or 0.0,
            ltv=_normalize_ltv(row.get("Loan Acquisition LTV")),
            property_type=_clean_text(row.get("Specific Property Type")) or "Multifamily",
            is_affordable=bool(_clean_text(row.get("Affordable Housing Type"))),
            state=_clean_text(row.get("Property State")),
            msa=_clean_text(row.get("Metropolitan Statistical Area")),
            reporting_date=latest_reporting_date,
        )
        result = engine.calculate_loan(loan_input)
        output_rows.append(
            _row_to_output(
                source=SOURCE_FANNIE_MAE,
                snapshot=resolved_snapshot,
                loan_input=loan_input,
                result=result,
                reporting_date=latest_reporting_date,
                msa=_clean_text(row.get("Metropolitan Statistical Area")),
            )
        )

    return output_rows


def _detect_latest_fannie_reporting_date(input_path: Path) -> date | None:
    latest_reporting_date: date | None = None
    source_usecols = ["Reporting Period Date"]

    def consider_frame(frame: pd.DataFrame) -> None:
        nonlocal latest_reporting_date
        parsed_dates = pd.to_datetime(frame["Reporting Period Date"], errors="coerce").dropna()
        if parsed_dates.empty:
            return
        candidate = parsed_dates.max().date()
        if latest_reporting_date is None or candidate > latest_reporting_date:
            latest_reporting_date = candidate

    if input_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(input_path) as archive:
            for member in sorted(archive.namelist()):
                if not member.lower().endswith(".csv"):
                    continue
                with archive.open(member) as handle:
                    for frame in pd.read_csv(
                        handle,
                        low_memory=False,
                        usecols=source_usecols,
                        chunksize=100_000,
                    ):
                        consider_frame(frame)
    else:
        for frame in pd.read_csv(
            input_path,
            low_memory=False,
            usecols=source_usecols,
            chunksize=100_000,
        ):
            consider_frame(frame)

    return latest_reporting_date


def build_curated_rows(
    source: str,
    csv_frames: list[pd.DataFrame],
    snapshot: str | None = None,
) -> list[dict[str, Any]]:
    engine = ERCFEngine()
    records: list[dict[str, Any]] = []
    for frame in csv_frames:
        records.extend(frame.to_dict(orient="records"))

    if source == SOURCE_FREDDIE_MAC:
        return _normalize_freddie_records(records, snapshot=snapshot, engine=engine)
    if source == SOURCE_FANNIE_MAE:
        return _normalize_fannie_records(records, snapshot=snapshot, engine=engine)
    raise ValueError(f"Unsupported source: {source}")


def _read_csv_frames(input_path: Path, *, source: str) -> list[pd.DataFrame]:
    source_usecols = {
        SOURCE_FREDDIE_MAC: [
            "lnno",
            "quarter",
            "amt_upb_endg",
            "amt_upb_pch",
            "rate_dcr",
            "rate_ltv",
            "code_st",
            "geographical_region",
        ],
        SOURCE_FANNIE_MAE: [
            "Loan Number",
            "Reporting Period Date",
            "Original UPB",
            "UPB - Current",
            "Underwritten DSCR",
            "Loan Acquisition LTV",
            "Specific Property Type",
            "Property State",
            "Metropolitan Statistical Area",
            "Affordable Housing Type",
        ],
    }
    usecols = source_usecols.get(source)
    if usecols is None:
        raise ValueError(f"Unsupported source: {source}")

    if source == SOURCE_FANNIE_MAE:
        latest_reporting_date = _detect_latest_fannie_reporting_date(input_path)
        if latest_reporting_date is None:
            return []

        def filter_frame(frame: pd.DataFrame) -> pd.DataFrame:
            return _rows_with_reporting_date(frame, "Reporting Period Date", latest_reporting_date)

        if input_path.suffix.lower() == ".zip":
            frames: list[pd.DataFrame] = []
            with zipfile.ZipFile(input_path) as archive:
                for member in sorted(archive.namelist()):
                    if not member.lower().endswith(".csv"):
                        continue
                    with archive.open(member) as handle:
                        for frame in pd.read_csv(
                            handle,
                            low_memory=False,
                            usecols=usecols,
                            chunksize=100_000,
                        ):
                            filtered = filter_frame(frame)
                            if not filtered.empty:
                                frames.append(filtered)
            return frames

        frames = []
        for frame in pd.read_csv(
            input_path,
            low_memory=False,
            usecols=usecols,
            chunksize=100_000,
        ):
            filtered = filter_frame(frame)
            if not filtered.empty:
                frames.append(filtered)
        return frames

    if input_path.suffix.lower() == ".zip":
        frames: list[pd.DataFrame] = []
        with zipfile.ZipFile(input_path) as archive:
            for member in sorted(archive.namelist()):
                if member.lower().endswith(".csv"):
                    with archive.open(member) as handle:
                        frames.append(pd.read_csv(handle, low_memory=False, usecols=usecols))
        return frames
    return [pd.read_csv(input_path, low_memory=False, usecols=usecols)]


def _write_curated_artifact(source: str, snapshot: str, rows: list[dict[str, Any]]) -> Path:
    output_dir = PROJECT_ROOT / "tmp" / "datasets" / source
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{snapshot}.json"
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, default=str)
    return output_path


def ingest_source(source: str, input_path: Path, snapshot: str | None = None) -> Path:
    frames = _read_csv_frames(input_path, source=source)
    rows = build_curated_rows(source, frames, snapshot=snapshot)
    if not rows:
        raise ValueError(f"No curated rows produced for {source} from {input_path}")

    resolved_snapshot = snapshot or rows[0]["snapshot"]
    return _write_curated_artifact(source, resolved_snapshot, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build curated GSE dataset artifacts.")
    parser.add_argument("--source", required=True, choices=[SOURCE_FREDDIE_MAC, SOURCE_FANNIE_MAE])
    parser.add_argument("--input", required=True)
    parser.add_argument("--snapshot", default=None)
    args = parser.parse_args()

    output_path = ingest_source(args.source, Path(args.input), snapshot=args.snapshot)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
