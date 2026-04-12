# Multifamily ERCF Capital Analytics

An elegant, institutional-grade business web application for multifamily loan analysis, focusing on FHFA ERCF-style capital results for a single loan and public-dataset portfolio views.

## Features

* **Single Loan Calculator**: Input loan attributes to estimate ERCF-style capital factors and risk multipliers.
* **Public Dataset Manager**: Upload and map GSE (Fannie Mae / Freddie Mac) multifamily loan performance data files.
* **Portfolio Analytics**: View aggregated KPIs, distributions, and scatter plots comparing risk topographies across portfolios.
* **Methodology Reference**: Transparent view into formulas, field mappings, and risk-weight assumptions.

## Tech Stack

* **Frontend**: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, Recharts.
* **Backend**: Python 3, FastAPI, Pydantic, Pandas.
* **Database**: In-memory Python list for v1 (seeded with mock data), with easy extensibility to PostgreSQL via SQLAlchemy.

## Architecture & Calculation Engine

The engine is modular and designed for easy updating:
* The core formulas and multipliers are defined in `/backend/ercf_config.yaml`.
* The `ERCFEngine` class in `/backend/app/engine.py` applies these assumptions to the canonical `LoanInput` schema.
* Extensible parsers can be added to the `/api/upload` route in `/backend/app/main.py`.

## Getting Started

### 1. Run the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt # (or install dependencies manually if missing: fastapi uvicorn pandas pydantic pyyaml python-multipart)
uvicorn app.main:app --reload --port 8000
```
The backend starts with seeded mock data so the portfolio analytics and schemas work immediately.

### 2. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to interact with the application.

### Customizing the Engine
To adjust risk weights, LTV thresholds, or DSCR bands, simply modify `backend/ercf_config.yaml`. The engine will apply the new multipliers immediately.
