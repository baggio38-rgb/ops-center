"""Backward compatibility shim.

The heavy implementation moved to core.legacy in v6.1. Existing imports that
still use ops_core continue to work, but new code should import from core.
"""

from core.legacy import *  # noqa: F401,F403
