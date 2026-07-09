# v6.1 Legacy Core Package

This step keeps behavior unchanged while moving the historical large implementation into a real package:

- `core/legacy.py` now contains the previous `ops_core.py` implementation.
- `ops_core.py` remains as a compatibility shim.
- `app_pages/*` now imports render functions from `core` instead of `ops_core`.

No business logic, SQL, charts, or UI behavior were changed.
