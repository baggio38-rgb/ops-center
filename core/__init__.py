"""Core implementation package for Ops Center.

v6.1 moves the historical implementation out of the project root and exposes
it through this package. The public render functions stay stable while later
v6.x steps move each page implementation into dedicated modules.
"""

from .legacy import *  # noqa: F401,F403
