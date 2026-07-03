# Ops Center v4 refactor

This package is a safe v4 bridge:

- `dashboard.py` now routes page navigation through `pages/*` modules.
- Page modules are thin wrappers that delegate to the current implementation functions in `dashboard.py`.
- This keeps all existing behavior stable while preparing the project for deeper module extraction.
- `.gitattributes` keeps Python files on LF line endings to reduce Windows CRLF diff noise.

Next refactor steps can move implementation code from `dashboard.py` into each `pages/*.py` file gradually.
