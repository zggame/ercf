from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pandas as pd
import io
import os
import json
import threading
from pathlib import Path
from .schema import LoanInput, EngineResult, LoanWithResult, PortfolioSummary
from .engine import ERCFEngine

app = FastAPI(title="ERCF Capital Analytics API")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ERCFEngine()
portfolio_lock = threading.Lock()

DB_PATH = Path(__file__).parent.parent / "portfolio_data.json"


def _get_default_portfolio() -> List[LoanInput]:
    return [
        LoanInput(
            loan_id="MOCK-001",
            original_upb=15000000,
            current_upb=14500000,
            property_type="Multifamily",
            is_affordable=True,
            dscr=1.45,
            ltv=0.65,
            state="CA",
        ),
        LoanInput(
            loan_id="MOCK-002",
            original_upb=25000000,
            current_upb=25000000,
            property_type="Seniors Housing",
            is_affordable=False,
            dscr=1.15,
            ltv=0.75,
            state="TX",
        ),
    ]


def load_portfolio() -> List[LoanInput]:
    if not DB_PATH.exists():
        return _get_default_portfolio()

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [LoanInput(**item) for item in data]
    except Exception as exc:
        print(f"Failed to load persisted portfolio from {DB_PATH}: {exc}")
        return []


def save_portfolio(portfolio: List[LoanInput]) -> None:
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump([loan.model_dump(mode="json") for loan in portfolio], f)


PORTFOLIO: List[LoanInput] = load_portfolio()


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Multifamily ERCF Engine is running"}


@app.post("/api/calculate", response_model=EngineResult)
def calculate_single_loan(loan: LoanInput):
    return engine.calculate_loan(loan)


@app.get("/api/portfolio", response_model=List[LoanInput])
def get_portfolio():
    return PORTFOLIO


@app.get("/api/portfolio/summary", response_model=PortfolioSummary)
def get_portfolio_summary():
    if not PORTFOLIO:
        return PortfolioSummary(
            loan_count=0,
            original_upb_total=0,
            current_upb_total=0,
            wa_dscr=0,
            wa_ltv=0,
            wa_estimated_capital_factor=0,
            total_estimated_capital_amount=0,
        )

    results = [engine.calculate_loan(loan) for loan in PORTFOLIO]

    total_cur_upb = sum(loan.current_upb for loan in PORTFOLIO)

    wa_dscr = (
        sum(loan.dscr * loan.current_upb for loan in PORTFOLIO) / total_cur_upb
        if total_cur_upb
        else 0
    )
    wa_ltv = (
        sum(loan.ltv * loan.current_upb for loan in PORTFOLIO) / total_cur_upb
        if total_cur_upb
        else 0
    )
    wa_factor = (
        sum(
            res.estimated_capital_factor * p.current_upb
            for res, p in zip(results, PORTFOLIO)
        )
        / total_cur_upb
        if total_cur_upb
        else 0
    )
    total_cap = sum(res.estimated_capital_amount for res in results)

    confidence_scores = [res.confidence_score for res in results]
    loans_with_available = sum(1 for res in results if res.result_available)
    loans_with_missing = len(results) - loans_with_available
    avg_confidence = (
        sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    )
    min_confidence = min(confidence_scores) if confidence_scores else 0
    sorted_scores = sorted(confidence_scores)
    mid = len(sorted_scores) // 2
    median_confidence = (
        (
            (sorted_scores[mid - 1] + sorted_scores[mid]) / 2
            if len(sorted_scores) % 2 == 0 and len(sorted_scores) > 1
            else sorted_scores[mid]
        )
        if sorted_scores
        else 0.0
    )

    missing_counts = [res.missing_input_count for res in results]
    total_missing = sum(missing_counts)

    field_counts: dict[str, int] = {}
    for res in results:
        for field_name in res.missing_inputs:
            field_counts[field_name] = field_counts.get(field_name, 0) + 1

    return PortfolioSummary(
        loan_count=len(PORTFOLIO),
        original_upb_total=sum(loan.original_upb for loan in PORTFOLIO),
        current_upb_total=total_cur_upb,
        wa_dscr=wa_dscr,
        wa_ltv=wa_ltv,
        wa_estimated_capital_factor=wa_factor,
        total_estimated_capital_amount=total_cap,
        loans_with_available_results=loans_with_available,
        loans_with_missing_results=loans_with_missing,
        average_confidence_score=avg_confidence,
        median_confidence_score=median_confidence,
        minimum_confidence_score=min_confidence,
        total_missing_input_count=total_missing,
        missing_input_counts_by_field=field_counts,
    )


@app.get("/api/portfolio/results", response_model=List[LoanWithResult])
def get_portfolio_results():
    return [
        LoanWithResult(loan=loan, result=engine.calculate_loan(loan))
        for loan in PORTFOLIO
    ]


@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    mapped_count = 0
    failed_rows = []
    new_loans = []

    for idx, row in df.iterrows():
        try:
            row_id = row.get("loan_id")
            row_upb = row.get("original_upb")
            row_cur_upb = row.get("current_upb")
            row_dscr = row.get("dscr")
            row_ltv = row.get("ltv")

            if pd.isna(row_id) or str(row_id).strip() == "":
                failed_rows.append({"row": int(idx), "error": "loan_id is required"})
                continue
            if pd.isna(row_upb) or pd.isna(row_cur_upb):
                failed_rows.append(
                    {
                        "row": int(idx),
                        "error": "original_upb and current_upb are required",
                    }
                )
                continue
            if pd.isna(row_dscr) or pd.isna(row_ltv):
                failed_rows.append(
                    {"row": int(idx), "error": "dscr and ltv are required"}
                )
                continue

            loan = LoanInput(
                loan_id=str(row_id).strip(),
                original_upb=float(row_upb),
                current_upb=float(row_cur_upb),
                dscr=float(row_dscr),
                ltv=float(row_ltv),
                property_type=str(row.get("property_type", "Multifamily"))
                if not pd.isna(row.get("property_type"))
                else "Multifamily",
                state=str(row.get("state", "Unknown"))
                if not pd.isna(row.get("state"))
                else "Unknown",
            )
            new_loans.append(loan)
            mapped_count += 1
        except Exception as e:
            failed_rows.append({"row": int(idx), "error": str(e)})

    if mapped_count > 0:
        with portfolio_lock:
            PORTFOLIO.extend(new_loans)
            save_portfolio(PORTFOLIO)

    return {
        "status": "success" if mapped_count > 0 and not failed_rows else "partial",
        "mapped_records": mapped_count,
        "failed_records": len(failed_rows),
        "errors": failed_rows[:10] if failed_rows else [],
    }
