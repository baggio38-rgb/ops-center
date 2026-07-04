# V6.5 Upload Admin Split

This version moves data-admin and upload implementation out of `core/legacy.py` into:

- `features/upload_admin.py`

Updated:

- `app_pages/data_admin.py` now imports from `features.upload_admin`
- `core/legacy.py` keeps compatibility imports only

Behavior is intended to be unchanged.
