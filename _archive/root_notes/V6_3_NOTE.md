# V6.3 Member Value Split

This package moves the member-value page group out of `core/legacy.py` into a real feature module.

## Changed

- Added `features/member_value.py`
- Updated `app_pages/member_value.py` to import from `features.member_value`
- Removed migrated member renderers from `core/legacy.py`

## Migrated page renderers

- `render_member_value`
- `render_bet_analysis`
- `render_cs_analysis`
- `render_winback`
- `render_realtime`

## Behavior

No business logic was intentionally changed. Shared helpers still come from `core.legacy` during this transition step.
