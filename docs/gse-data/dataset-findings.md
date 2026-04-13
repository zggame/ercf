# GSE Dataset Findings

**Date:** April 12, 2026

## Curated snapshot choice for the PoC

The deployed PoC uses one curated snapshot per source:

- Freddie Mac: `2025Q3`
- Fannie Mae: `202509`

That choice keeps the deployed experience deterministic and keeps the explorer defaults aligned with the backend cohort contract.

## Why that shape

Freddie Mac is released as a split panel dataset with an older historical file and a newer recent file. For the PoC, the newer window is enough for current-period review, so the curated artifact keeps only the latest quarter from the recent file.

Fannie Mae's main multifamily file already contains the current-period fields needed for the PoC. The separate DSCR file is useful later as an enrichment source, but it is not required for the curated reviewer snapshot.

## Builder implication

The offline builder should:

- read the local ZIPs
- normalize each source into the same canonical row shape
- keep one snapshot artifact per source
- write the result under `tmp/datasets/<source>/<snapshot>.json`

That keeps the deployed app read-only while still making the data lineage clear enough for reviewer walkthroughs.
