# Issue #1: Add NO_COLOR Environment Variable Support

**Label:** `enhancement`, `quick-win`
**Milestone:** v0.1.1
**Estimated Effort:** 5 minutes

## Problem

ANSI color codes look ugly in CI/CD logs and some terminals. Need a way to disable colors for cleaner output.

## Proposed Solution

Support `NO_COLOR` environment variable (industry standard) to strip ANSI codes from output.

```bash
# Disable colors
NO_COLOR=1 python -m unittest tests/

# Or Mercury-specific
MERCURY_NO_COLOR=1 python -m unittest tests/
```

## Acceptance Criteria

- [ ] Check for `NO_COLOR` or `MERCURY_NO_COLOR` environment variables
- [ ] When set, return plain text without ANSI codes from `_format_report()`
- [ ] Colors still work when env var not set
- [ ] Update README with example usage

## Implementation Notes

**File:** `django_mercury/monitor.py`

```python
import os

class Colors:
    """ANSI escape codes (disabled if NO_COLOR set)."""
    _DISABLED = os.getenv('NO_COLOR') or os.getenv('MERCURY_NO_COLOR')

    RESET = "" if _DISABLED else "\033[0m"
    BOLD = "" if _DISABLED else "\033[1m"
    # ... rest of colors
```

**Alternative approach:**
```python
def _should_use_colors() -> bool:
    """Check if colors should be used based on environment."""
    if os.getenv('NO_COLOR') or os.getenv('MERCURY_NO_COLOR'):
        return False
    # Could also check if stdout is a TTY
    return True
```

## References

- NO_COLOR standard: https://no-color.org/
- Used by: pytest, ruff, black, many others
