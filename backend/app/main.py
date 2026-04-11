from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import pandas as pd
import io
from .schema import LoanInput, EngineResult, PortfolioSummary
from .engine import ERCFEngine

app = FastAPI(title="ERCF Capital Analytics API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ERCFEngine()

# In-memory mock database for now
PORTFOLIO: List[LoanInput] = [
    LoanInput(
        loan_id="MOCK-001",
        original_upb=15000000,
        current_upb=14500000,
        property_type="Multifamily",
        is_affordable=True,
        dscr=1.45,
        ltv=0.65,
        state="CA"
    ),
    LoanInput(
        loan_id="MOCK-002",
        original_upb=25000000,
        current_upb=25000000,
        property_type="Seniors Housing",
        is_affordable=False,
        dscr=1.15,
        ltv=0.75,
        state="TX"
    )
]

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
            total_estimated_capital_amount=0
        )

    results = [engine.calculate_loan(loan) for loan in PORTFOLIO]

    total_cur_upb = sum(loan.current_upb for loan in PORTFOLIO)

    wa_dscr = sum(loan.dscr * loan.current_upb for loan in PORTFOLIO) / total_cur_upb if total_cur_upb else 0
    wa_ltv = sum(loan.ltv * loan.current_upb for loan in PORTFOLIO) / total_cur_upb if total_cur_upb else 0
    wa_factor = sum(res.estimated_capital_factor * p.current_upb for res, p in zip(results, PORTFOLIO)) / total_cur_upb if total_cur_upb else 0
    total_cap = sum(res.estimated_capital_amount for res in results)

    return PortfolioSummary(
        loan_count=len(PORTFOLIO),
        original_upb_total=sum(loan.original_upb for loan in PORTFOLIO),
        current_upb_total=total_cur_upb,
        wa_dscr=wa_dscr,
        wa_ltv=wa_ltv,
        wa_estimated_capital_factor=wa_factor,
        total_estimated_capital_amount=total_cap
    )

@app.get("/api/portfolio/results", response_model=List[EngineResult])
def get_portfolio_results():
    return [engine.calculate_loan(loan) for loan in PORTFOLIO]

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

    # basic mapping logic
    mapped_count = 0
    for _, row in df.iterrows():
        try:
            loan = LoanInput(
                loan_id=str(row.get('loan_id', f'UPL-{mapped_count}')),
                original_upb=float(row.get('original_upb', 1000000)),
                current_upb=float(row.get('current_upb', 1000000)),
                dscr=float(row.get('dscr', 1.25)),
                ltv=float(row.get('ltv', 0.65)),
                property_type=str(row.get('property_type', 'Multifamily')),
                state=str(row.get('state', 'Unknown'))
            )
            PORTFOLIO.append(loan)
            mapped_count += 1
        except Exception as e:
            print(f"Failed to map row: {e}")
            continue

    return {"status": "success", "mapped_records": mapped_count}
