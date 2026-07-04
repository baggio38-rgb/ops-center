"""Core compatibility package.

Do not import core.legacy here. Importing legacy at package import time creates
circular imports with feature modules and services.
"""

__all__ = []
