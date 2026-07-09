# v5.1 Core Split

This version moves the original large Streamlit implementation from `dashboard.py` into `ops_core.py`.

## What changed

- `dashboard.py` is now the main navigation entry point only.
- `ops_core.py` contains the original page implementations and shared Streamlit setup.
- Existing Chinese top navigation is preserved.
- Existing `pages/*.py` compatibility launchers continue to delegate back to `dashboard.main()`.

## Why this is safer

This avoids `sys.modules["__main__"]` wrappers and avoids circular imports while immediately making `dashboard.py` small enough to maintain.

## Next step

In v5.2, functions can be moved from `ops_core.py` into real modules one page group at a time.
