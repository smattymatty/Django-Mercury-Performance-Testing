# Issue #2: Add End-of-Run Summary Report

**Label:** `enhancement`, `ux`
**Milestone:** v0.1.1
**Estimated Effort:** 20 minutes

## Problem

When running many tests, individual reports scroll by quickly. Need a summary at the end showing overall performance statistics.

## Proposed Solution

Track all monitor results globally and print a summary after test run completes.

```
================================ MERCURY SUMMARY ================================
Total tests monitored: 23
Passed: 20 (87%)
Failed: 3 (13%)

Slowest tests:
  1. test_user_list_with_joins - 567.25ms (11 queries)
  2. test_dashboard_load - 234.12ms (45 queries, N+1 detected)
  3. test_search_autocomplete - 189.45ms (8 queries)

Top issues:
  • 3 tests with N+1 patterns
  • 2 tests exceeded response time threshold
  • 1 test exceeded query count threshold

Average metrics:
  Response time: 45.32ms (median: 23.11ms)
  Query count: 5.2 (median: 3)
=================================================================================
```

## Acceptance Criteria

- [ ] Global tracker collects all MonitorResult instances
- [ ] Summary printed automatically after test run (using `atexit` or test framework hook)
- [ ] Shows total/pass/fail counts
- [ ] Lists top 5 slowest tests
- [ ] Aggregates common issues
- [ ] Can be disabled with `MERCURY_NO_SUMMARY=1`

## Implementation Notes

**File:** `django_mercury/summary.py` (new)

```python
import atexit
from typing import List

class MercurySummaryTracker:
    """Global singleton to track all monitor results."""
    _instance = None
    results: List[tuple[str, MonitorResult]] = []

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            atexit.register(cls._instance.print_summary)
        return cls._instance

    def add_result(self, test_name: str, result: MonitorResult):
        """Record a test result."""
        self.results.append((test_name, result))

    def print_summary(self):
        """Print summary report."""
        if not self.results or os.getenv('MERCURY_NO_SUMMARY'):
            return

        # Calculate stats and print formatted report
        ...
```

**Update:** `django_mercury/monitor.py`

```python
def monitor(**inline_overrides):
    result = MonitorResult()
    # ... existing code ...

    # On exit: record result
    if result.test_name:
        from .summary import MercurySummaryTracker
        MercurySummaryTracker.instance().add_result(
            result.test_name, result
        )
```

## Alternative Approaches

1. **Pytest plugin hook:** Use `pytest_sessionfinish` hook (requires #4)
2. **Django test runner:** Subclass `DiscoverRunner` to add summary
3. **Manual call:** Require `MercurySummary.print()` at end of test suite

## Questions

- Should summary be opt-in or opt-out?
- Include memory stats if we add memory tracking later?
