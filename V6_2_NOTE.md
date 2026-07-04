# V6.2 Finance Results Split

This step moves the finance-result page implementations out of `core/legacy.py` and into `features/finance_results.py`.

Moved renderers:

- `render_overview`
- `render_recent_trend`
- `render_finance_channel`
- `render_bonus_analysis`
- `render_bonus_roi_agent_quality`
- `render_agent_commission`

The shared helpers still come from `core.legacy` in this transition step, so runtime behavior stays the same while the architecture starts slimming down.
