# GSE Comparison PoC Design

**Date:** April 12, 2026

## Goal

Build a deployable proof of concept for reviewers familiar with the GSE multifamily business that combines:

- a one-loan calculator
- curated Freddie Mac and Fannie Mae portfolio datasets
- portfolio statistics with limited drilldown
- side-by-side cohort comparison
- a methodology explanation that ties the analysis back to ERCF concepts and authoritative source materials

The PoC should prioritize deployment reliability and reviewer clarity over ingestion automation.

## Product Shape

The PoC should expose four core user experiences:

1. `Single Loan Calculator`
2. `Dataset Explorer`
3. `Optional Compare Panel`
4. `Methodology / ERCF Explanation`

The calculator remains a focused single-loan workflow. The dataset explorer becomes the main portfolio analytics surface. The compare experience is not a separate product area; it is a secondary panel that can be opened alongside the primary explorer. The methodology area explains the rule logic, caveats, field mapping, and source references.

## Data Strategy

The PoC should deploy with curated dataset artifacts already prepared offline. It should not depend on live GSE downloads or in-app ingestion for the initial release.

### Rationale

- Freddie Mac and Fannie Mae data access is operationally fragile in a deployed product because download access depends on registration, authenticated sessions, or expiring URLs.
- The PoC reviewers care more about analytical usefulness than ingestion mechanics.
- A read-only deployed experience reduces failure modes and improves demo consistency.

### Source Treatment

Freddie Mac:
- Use the recent Freddie Mac dataset window as the initial PoC default when the goal is current-period analysis.
- Keep the historical Freddie split-file finding documented, but do not require full historical ingestion unless a comparison requirement depends on it.

Fannie Mae:
- Use the main Multifamily dataset as the initial canonical source.
- Treat the DSCR supplemental file as an optional later enrichment, not a launch dependency.

### Canonical Model

Both GSE sources should map into one canonical analytical schema for the deployed app. The raw parsing and source-specific mapping can remain source-specific behind the scenes, but the explorer and compare views should operate on a consistent interface.

## Explorer and Compare Interaction

The primary user interaction is a single explorer with an optional second panel.

### Primary Explorer Panel

The default panel should let the user choose:

- source: Freddie Mac or Fannie Mae
- snapshot/time selection
- filters for cohort narrowing

The panel should then show:

- headline summary cards
- a compact fixed chart set
- one configurable breakdown chart
- a drilldown table

### Compare Panel

The compare panel should be hidden by default and opened on demand. When opened, it should mirror the primary panel structure and control set.

Each panel should allow independent selections for:

- source
- snapshot/time
- filters

The top of the compare experience should show comparison deltas for the most important metrics so users can immediately answer questions like:

- Freddie vs Fannie
- one time period vs another
- one filtered cohort vs another

The compare mode should be symmetric. Both panels should use the same output structure so visual comparison is fast and credible.

## Analytics Scope

The charting should not become a full BI tool in the first PoC. The recommended balance is:

- fixed summary cards
- fixed comparison-safe charts
- one configurable breakdown chart

### Fixed Outputs

Each panel should show:

- loan count
- original UPB total
- current UPB total
- weighted average DSCR
- weighted average LTV
- weighted average estimated capital factor
- total estimated capital amount

Recommended fixed charts:

- capital factor distribution
- DSCR band distribution
- LTV band distribution
- state or property type breakdown

### Configurable Breakdown

Add one breakdown control that lets users choose a grouping dimension such as:

- state
- property type
- vintage
- affordability

And one metric such as:

- loan count
- current UPB
- estimated capital amount

This gives enough flexibility for domain reviewers without turning the page into a generalized analytics builder.

### Drilldown

The table should support simple filtering and sorting and expose the canonical loan-level fields needed to validate what the charts are showing. It should remain a drilldown aid, not the primary interface.

## Methodology

The deployed PoC should expose only the refined calculation logic. It should not present a “base vs refined” toggle or comparison mode in the first release.

### Rationale

- Reviewers are evaluating whether the resulting analysis is useful and credible.
- Showing internal evolution of the model adds complexity without adding much product value in the PoC.
- The refined rule can still be documented clearly in the methodology section.

### Methodology Page Content

The methodology area should explain:

- what ERCF-style concepts are being approximated
- which portfolio fields feed the calculation
- how the refined logic interprets credit and collateral variables
- any important caveats or confidence limitations
- links back to source authority and internal data notes

It should also link to the GSE data research and findings documents under `docs/gse-data`.

Implementation clarification for Task 5:

- the calculator request and response contract stays stable, including the refined result trace fields
- the calculator copy should describe the refined ERCF-style methodology only and should not introduce any base-vs-refined toggle or comparison language
- the methodology page should frame Freddie Mac and Fannie Mae as source-specific mappings into one canonical refined trace, then link back to the two research notes below

## Deployment Model

The initial deployment should be read-only.

That means:

- no live GSE download process in production
- no required upload or refresh workflow in the deployed UI
- no dependency on portal credentials in the application runtime

Any ingestion workflow should remain offline and internal for now, using curated source files and canonical output artifacts prepared before deployment.

## Recommended First Release

The first deployed PoC should include:

- existing single-loan calculator updated to the refined methodology
- curated Freddie Mac snapshot
- curated Fannie Mae snapshot
- one explorer page with optional compare panel
- fixed summary cards and a small chart set
- one configurable breakdown chart
- simple drilldown table
- methodology page with source and caveat links

It should explicitly exclude:

- live ingestion
- user uploads in production
- full BI-style chart builders
- visible base-vs-refined rule switching

## Open Implementation Direction

The remaining implementation choice is not product direction but execution detail:

- whether the curated data should ship as parquet, DuckDB-backed tables, or another precomputed format
- how much of the refined-rule work from the other worktree can be cleanly integrated into this one

Those are implementation planning topics, not open design questions.
