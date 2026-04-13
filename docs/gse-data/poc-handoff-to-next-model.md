# PoC Handoff: GSE Comparison Explorer

Date: 2026-04-12

Worktree: `/home/pooh/work/ercf/tmp-worktree/gse-comparison-poc`

Branch: `feature/gse-comparison-poc`

## Goal

Build a deployable PoC for Multifamily ERCF analytics with:

- one loan calculator
- a Freddie Mac dataset view
- a Fannie Mae dataset view
- simple statistics and drilldown
- a comparison panel for Freddie vs Fannie, time vs time, and filtered vs filtered
- a refined ERCF calculation only, not base-vs-refined UI
- a methodology page with links back to authority/data notes

## Current Status

Implementation is complete for the PoC shell and the offline curated dataset builder.

### Verified

- Backend unit suite passes: `24/24`
- Frontend production build passes
- Curated Freddie snapshot generated
- Curated Fannie snapshot generated

### Generated artifacts

- `tmp/datasets/freddie_mac/2025Q3.json`
- `tmp/datasets/fannie_mae/202509.json`

## What Changed

### Backend / API

- Added curated dataset explorer contracts and compare support.
- Added backend tests for:
  - curated store loading
  - cohort filtering
  - compare response shape
  - Freddie curated normalization
  - Fannie curated normalization

### Frontend

- Added the dataset explorer page.
- Added compare behavior in the explorer.
- Added methodology and references pages.
- Updated calculator/methodology copy to match the refined PoC semantics.

### Offline ingestion

- Added `ingest_gse.py` at repo root.
- It builds one canonical snapshot per source from local ZIP or CSV input.
- It writes JSON artifacts into `tmp/datasets/<source>/<snapshot>.json`.
- Freddie normalization selects the latest Freddie quarter from the recent data window.
- Fannie normalization selects the latest reporting period from the main multifamily file.

### Documentation

- `docs/gse-data/data-access-research.md`
- `docs/gse-data/dataset-findings.md`
- `docs/gse-data/2026-04-12-comparison-poc-design.md`

## Important File References

- [`ingest_gse.py`](/home/pooh/work/ercf/tmp-worktree/gse-comparison-poc/ingest_gse.py)
- [`backend/test_engine.py`](/home/pooh/work/ercf/tmp-worktree/gse-comparison-poc/backend/test_engine.py)
- [`docs/gse-data/dataset-findings.md`](/home/pooh/work/ercf/tmp-worktree/gse-comparison-poc/docs/gse-data/dataset-findings.md)

## Verification Commands

Run from the PoC worktree:

```bash
cd /home/pooh/work/ercf/tmp-worktree/gse-comparison-poc/backend
./venv/bin/python -m unittest test_engine -v
```

```bash
cd /home/pooh/work/ercf/tmp-worktree/gse-comparison-poc/frontend
npm run build
```

## Current Git Status

At the time of handoff, the worktree still had uncommitted local changes:

- `backend/test_engine.py`
- `docs/gse-data/dataset-findings.md`
- `ingest_gse.py`
- `tmp/datasets/fannie_mae/`
- `tmp/datasets/freddie_mac/`

`backend/venv` is also present as an untracked local directory and should be ignored.

## Recommended Next Step for the Next Model

The next model should decide whether to:

1. Wire the curated JSON artifacts into app startup so the deployed PoC reads `tmp/datasets/...`
2. Commit the current PoC work as-is
3. Add a packaging step that copies the curated artifacts into the deployment bundle

## Notes / Constraints

- Do not reintroduce live ingestion into the UI for the PoC.
- Keep only the refined methodology visible.
- Keep the explorer read-only and compare-focused.
- Freddie and Fannie are separate curated sources; do not merge them into one dataset.

