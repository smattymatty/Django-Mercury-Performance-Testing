"""Configuration resolution for performance thresholds.

Resolves thresholds from multiple sources with priority:
1. Inline kwargs (highest priority)
2. File-level MERCURY_PERFORMANCE_THRESHOLDS variable
3. Django settings.MERCURY_PERFORMANCE_THRESHOLDS
4. DEFAULTS (lowest priority)
"""

import inspect
from typing import Dict, Tuple, Any


# Default thresholds
DEFAULTS = {
    "response_time_ms": 100,
    "query_count": 10,
    "n_plus_one_threshold": 10,
}


def resolve_thresholds(**inline_overrides: Any) -> Tuple[Dict[str, int], bool]:
    """Resolve performance thresholds from config hierarchy.

    Priority (highest first):
    1. Inline kwargs passed to monitor()
    2. File-level MERCURY_PERFORMANCE_THRESHOLDS in caller's module
    3. Django settings.MERCURY_PERFORMANCE_THRESHOLDS
    4. DEFAULTS

    Args:
        **inline_overrides: Direct threshold overrides (response_time_ms, etc.)

    Returns:
        Tuple of (thresholds_dict, used_defaults: bool)
        - thresholds_dict: Resolved threshold values
        - used_defaults: True if no custom config was found
    """
    thresholds = DEFAULTS.copy()
    used_defaults = True

    # Layer 1: Django settings (lowest priority custom config)
    try:
        from django.conf import settings

        django_config = getattr(settings, "MERCURY_PERFORMANCE_THRESHOLDS", None)
        if django_config:
            thresholds.update(django_config)
            used_defaults = False
    except (ImportError, Exception):
        # Django not installed/configured or ImproperlyConfigured
        pass

    # Layer 2: File-level variable in caller's module
    try:
        # Search up the call stack for MERCURY_PERFORMANCE_THRESHOLDS
        # More robust than hardcoded frame depth - works in unit tests and real usage
        stack = inspect.stack()
        for frame_info in stack[1:]:  # Skip ourselves (frame 0)
            caller_frame = frame_info.frame
            caller_module = inspect.getmodule(caller_frame)

            if caller_module:
                file_config = getattr(caller_module, "MERCURY_PERFORMANCE_THRESHOLDS", None)
                if file_config:
                    thresholds.update(file_config)
                    used_defaults = False
                    break  # Found it, stop searching
    except (IndexError, Exception):
        # Frame inspection failed - skip file-level config
        pass

    # Layer 3: Inline overrides (highest priority)
    if inline_overrides:
        thresholds.update(inline_overrides)
        used_defaults = False

    return thresholds, used_defaults
