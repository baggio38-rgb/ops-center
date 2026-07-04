"""Core implementation package for Ops Center.

V6.2 keeps shared helpers and non-migrated page renderers in legacy.py.
Finance-result page renderers now live in features/finance_results.py and are
imported directly by app_pages/finance_results.py to avoid circular imports.
"""

from .legacy import *  # noqa: F401,F403
