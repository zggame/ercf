# Design: Shared Breakdown Bar in Compare Mode

## Problem

In compare mode, the primary `CohortPanel` (tone=primary) renders a Dimension/Metric control bar between FixedCharts and BreakdownChart. The comparison panel (tone=secondary) skips this bar. Even with `xl:items-stretch` equalizing panel heights, the BreakdownChart sections land at different vertical offsets.

## Solution

Extract the Dimension/Metric control bar to a shared horizontal row that spans both panels in compare mode. The bar is controlled by the primary panel's state and propagates to both.

## Layout

```
Compare mode:
┌─────────────────────────────────────────────────────────────┐
│  [Primary Cohort]              │  [Comparison Cohort]       │
│  FixedCharts                   │  FixedCharts                │
│  ─────────────────────────── │  ───────────────────────── │
│  [=== Shared Dimension/Metric Bar ===]                      │  ← new, full-width
│  BreakdownChart                │  BreakdownChart             │  ← now aligned
│  DrilldownTable               │  DrilldownTable            │
└─────────────────────────────────────────────────────────────┘

Single mode (unchanged):
┌─────────────────────────────────────────────────────────────┐
│  [Primary Cohort]                                           │
│  FixedCharts                                                │
│  [=== Dimension/Metric Bar (per-panel) ===]                 │
│  BreakdownChart                                             │
│  DrilldownTable                                            │
└─────────────────────────────────────────────────────────────┘
```

## Component Changes

### `cohort-panel.tsx`
- Add `showBreakdownControls?: boolean` prop (default `true`)
- Wrap the Dimension/Metric bar in `showBreakdownControls ? (...) : null`

### `page.tsx`
- In compare mode: render a shared `<BreakdownSharedBar>` above the flex row
- Shared bar uses `primaryRequest.breakdown_dimension` / `breakdown_metric`
- On change calls `setPrimaryRequest`
- Both `CohortPanel` instances in compare mode pass `showBreakdownControls={false}`
- Non-compare mode: unchanged behavior

## Backward Compatibility

Single-panel mode (compare disabled) is unaffected — CohortPanel still renders its own bar as before.
