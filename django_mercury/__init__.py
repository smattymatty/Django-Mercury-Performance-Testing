"""Django Mercury - Performance testing for Django apps.

Fresh start with clean architecture.
"""

from .monitor import MonitorResult, monitor

# Version is managed in pyproject.toml - read dynamically
try:
    from importlib.metadata import version
    __version__ = version("django-mercury-performance")
except Exception:
    __version__ = "unknown"

__all__ = ["__version__", "monitor", "MonitorResult"]
