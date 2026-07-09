# v6.0 logical page groups

This release keeps runtime behavior the same, but makes `dashboard.py` a thinner shell.

Changed:

- Added `app_pages/` logical page group package.
- Moved navigation group definitions out of `dashboard.py`.
- `dashboard.py` now imports grouped page lists:
  - `FINANCE_RESULT_PAGES`
  - `MEMBER_VALUE_PAGES`
  - `AGENT_CHANNEL_PAGES`
  - `DATA_ADMIN_PAGES`
- No `sys.modules["__main__"]` wrapper is used.

Next:

- Move actual function implementations from `ops_core.py` into page modules group by group.
