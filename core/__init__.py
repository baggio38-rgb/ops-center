"""Core package for legacy shared helpers.

Keep this package initializer intentionally lightweight.
Do not import legacy.py here, because feature modules import core.legacy
and eager imports can create circular imports during Streamlit startup.
"""
