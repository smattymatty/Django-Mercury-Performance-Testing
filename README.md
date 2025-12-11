# Django Mercury Performance Testing

[![PyPI version](https://badge.fury.io/py/django-mercury-performance.svg)](https://badge.fury.io/py/django-mercury-performance)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 3.2-5.1](https://img.shields.io/badge/django-3.2--5.1-green.svg)](https://docs.djangoproject.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-red.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Simple, powerful performance monitoring for Django tests.**

```python
from django_mercury import monitor

with monitor(response_time=100) as result:
    response = client.get('/api/users/')
# Automatic threshold checking - raises AssertionError on violations
```

The monitor either succeeds or fails:

```sh
============================================================
MERCURY PERFORMANCE REPORT
============================================================

🧪 Test: AuthEndpointPerformance.test_login_under_100ms
📍 Location: accounts/tests/mercury/test_auth_performance.py:20

📊 METRICS:
   Response time: 568.43ms (threshold: 100.00ms)
   Query count:   11 (threshold: 10)

✅ No N+1 patterns detected

❌ FAILURES:
   ⏱️  Response time 568.43ms exceeded threshold 100ms (+468.43ms over)
   🔢 Query count 11 exceeded threshold 10 (+1 extra queries)

============================================================
```

10 is the dafeult query count, but can be changed:

```python
with monitor(response_time_ms=10, query_count=5) as result:
            response = self.client.get('/api/v1/auth/me/')
result.explain() # print what the monitor found
```

If you aren't failing the mercury test, but you still want to see the stats monitored - use `.explain()`

```sh
============================================================
MERCURY PERFORMANCE REPORT
============================================================

🧪 Test: AuthEndpointPerformance.test_auth_me_under_50ms
📍 Location: accounts/tests/mercury/test_auth_performance.py:32

📊 METRICS:
   Response time: 6.86ms (threshold: 10.00ms)
   Query count:   3 (threshold: 5)

✅ No N+1 patterns detected

============================================================
```

No failure - but still useful information to help you understand your project, and tweak the performance thresholds.

## Why Mercury?

**Most performance tools just detect problems.** Mercury explains them in your test output, with clear context and actionable fixes.

**No configuration required.** Works out of the box with sensible defaults. Customize when you need to.

**Built for real Django projects.** Detects N+1 queries, slow responses, and excessive database calls automatically.

## Installation

```bash
pip install django-mercury-performance
```

### Two Usage Modes

**Minimal (context manager only):**
```python
# Just pip install - no setup needed
from django_mercury import monitor

with monitor() as result:
    response = self.client.get('/api/users/')
```

**Full features (management command, future admin, etc.):**
```python
# Add to settings.py
INSTALLED_APPS = [
    ...
    'django_mercury',  # Enables management commands
    ...
]
```

Then use the smart test discovery command:
```bash
# Only runs tests that use monitor()
python manage.py mercury_test

# Run specific app
python manage.py mercury_test myapp

# See what would run (dry run)
python manage.py mercury_test --verbosity=2
```

## Quick Start

### Basic Usage

```python
from django_mercury import monitor
from django.test import TestCase

class UserAPITest(TestCase):
    def test_user_list_performance(self):
        """Monitor performance with zero configuration."""
        with monitor() as result:
            response = self.client.get('/api/users/')

        # If thresholds exceeded, AssertionError with full report is raised
        # Otherwise, check metrics manually:
        print(f"Response time: {result.response_time_ms:.2f}ms")
        print(f"Queries: {result.query_count}")
```

### Custom Thresholds

```python
# Override defaults inline
with monitor(response_time_ms=50, query_count=5) as result:
    response = self.client.get('/api/users/')

# Or configure per-file
MERCURY_PERFORMANCE_THRESHOLDS = {
    'response_time_ms': 100,
    'query_count': 10,
    'n_plus_one_threshold': 8,
}

# Or in Django settings.py
MERCURY_PERFORMANCE_THRESHOLDS = {
    'response_time_ms': 200,
    'query_count': 20,
    'n_plus_one_threshold': 10,
}
```

**Configuration hierarchy:** Inline > File-level > Django settings > Defaults

### Detailed Reports

```python
with monitor() as result:
    response = self.client.get('/api/users/')

# Print full performance breakdown
result.explain()
```

**Example output:**

```
============================================================
MERCURY PERFORMANCE REPORT
============================================================

📊 METRICS:
   Response time: 156.32ms (threshold: 100ms)
   Query count:   45 (threshold: 10)

🔄 N+1 PATTERNS DETECTED:
   ❌ FAIL [23x] SELECT * FROM "auth_user" WHERE "id" = ?
        → SELECT * FROM "auth_user" WHERE "id" = 1
        → SELECT * FROM "auth_user" WHERE "id" = 2
        → SELECT * FROM "auth_user" WHERE "id" = 3

   ⚠️  WARN [8x] SELECT * FROM "user_profile" WHERE "user_id" = ?

❌ FAILURES:
   ⏱️  Response time 156.32ms exceeded threshold 100ms (+56.32ms over)
   🔢 Query count 45 exceeded threshold 10 (+35 extra queries)
   🔄 N+1 pattern detected: 23 similar queries (threshold: 10)
      Pattern: SELECT * FROM "auth_user" WHERE "id" = ?

============================================================
```

## What Gets Monitored

### Response Time
Measures end-to-end execution time using high-precision `perf_counter()`.

**Default threshold:** 200ms

### Query Count
Tracks all database queries executed during the monitored block using Django's `CaptureQueriesContext`.

**Default threshold:** 20 queries

### N+1 Query Detection
Automatically normalizes SQL queries and detects repeated patterns:

```sql
-- These are detected as the same pattern:
SELECT * FROM users WHERE id = 1
SELECT * FROM users WHERE id = 2
SELECT * FROM users WHERE id = 999

-- Normalized to:
SELECT * FROM users WHERE id = ?
```

**Detection levels:**
- **Failure:** Count >= threshold (default: 10)
- **Warning:** Count >= 80% of threshold
- **Notice:** Count >= 50% of threshold (minimum 3)

### Smart SQL Normalization
Handles:
- String literals: `'hello'` → `?`
- Numbers: `123`, `45.67` → `?`
- UUIDs: `'550e8400-e29b-41d4-a716-446655440000'` → `?`
- IN clauses: `IN (1, 2, 3)` → `IN (?)`
- Boolean values: `TRUE`, `FALSE` → `?`

## Configuration Options

```python
MERCURY_PERFORMANCE_THRESHOLDS = {
    # Response time in milliseconds
    'response_time_ms': 200,

    # Maximum number of queries
    'query_count': 20,

    # N+1 pattern failure threshold
    'n_plus_one_threshold': 10,
}
```

**Priority order (highest to lowest):**
1. **Inline:** `monitor(response_time_ms=100)`
2. **File-level:** `MERCURY_PERFORMANCE_THRESHOLDS` in test module
3. **Django settings:** `settings.MERCURY_PERFORMANCE_THRESHOLDS`
4. **Defaults:** Built-in sensible values

### Disabling Colors

Mercury uses ANSI colors for professional terminal output. To disable colors (useful for CI/CD logs):

```bash
# Standard NO_COLOR environment variable (https://no-color.org/)
NO_COLOR=1 python -m unittest tests/

# Or Mercury-specific
MERCURY_NO_COLOR=1 python manage.py test

# In GitHub Actions
env:
  NO_COLOR: 1
```

When colors are disabled, you get clean plain text output perfect for log parsing.

### Smart Test Discovery (Management Command)

Add `'django_mercury'` to `INSTALLED_APPS` to unlock the management command:

```bash
# Auto-discovers and runs only tests using monitor()
python manage.py mercury_test
```

**Example output:**
```
Discovering Mercury performance tests...

Found 3 file(s) with 8 Mercury test(s):
  ✓ accounts/tests/test_auth_performance.py (2 tests)
  ✓ api/tests/test_user_endpoints.py (5 tests)
  ✓ dashboard/tests/test_views.py (1 test)

Running 8 Mercury performance tests...
[... individual test reports ...]

================================================================================
MERCURY SUMMARY
================================================================================

Total tests monitored: 8
Passed: 7 (88%)  Failed: 1 (12%)

Slowest tests:
  1. test_user_list_with_joins - 567.25ms (11 queries)
  2. test_dashboard_load - 234.12ms (45 queries, N+1)
  3. test_search_autocomplete - 189.45ms (8 queries)

Top issues:
  • 1 test with N+1 patterns
  • 1 test exceeded response time threshold

Average metrics:
  Response time: 145.32ms (median: 89.11ms)
  Query count: 8.5 (median: 7)

To disable this summary: export MERCURY_NO_SUMMARY=1
================================================================================
```

**Options:**
```bash
# Filter by app
python manage.py mercury_test myapp

# Filter by test file
python manage.py mercury_test myapp.tests.test_api

# Preserve test database
python manage.py mercury_test --keepdb

# Skip smart discovery (run all tests)
python manage.py mercury_test --no-discover

# Adjust verbosity (0-3)
python manage.py mercury_test --verbosity=2
```

### End-of-Run Summary

Mercury automatically tracks all monitored tests and prints a summary on exit:

```bash
# Summary enabled by default
python manage.py test

# Disable summary
MERCURY_NO_SUMMARY=1 python manage.py test
```

The summary shows:
- Pass/fail counts and percentages
- Top 5 slowest tests
- Common issues (N+1 patterns, threshold violations)
- Average and median metrics

**Note:** Summary only appears when 1+ tests use `monitor()`.

### HTML Report Export

Generate beautiful, shareable HTML reports when using the management command:

```bash
# Auto-generate filename (mercury_report_TIMESTAMP.html)
python manage.py mercury_test --html

# Specify custom filename
python manage.py mercury_test --html performance_report.html

# Combine with other options
python manage.py mercury_test myapp.tests --html report.html --keepdb
```

**Individual Test Export:**

You can also export individual test results to HTML:

```python
with monitor() as result:
    response = self.client.get('/api/users/')

# Export single result
result.to_html('single_test_report.html')
```

## Advanced Usage

### Inspect Results Programmatically

```python
with monitor() as result:
    response = self.client.get('/api/users/')

# Access metrics
assert result.response_time_ms < 100
assert result.query_count <= 10
assert len(result.n_plus_one_patterns) == 0

# Export to JSON
metrics = result.to_dict()
```

### Custom Assertions

```python
from django_mercury import monitor

with monitor() as result:
    response = self.client.get('/api/users/')

# Custom business logic
if result.query_count > 15 and len(result.n_plus_one_patterns) > 0:
    result.explain()
    raise AssertionError("Too many queries with N+1 patterns detected")
```

### Disable Auto-Failures (Manual Checking)

```python
# Catch the exception to prevent test failure
try:
    with monitor() as result:
        response = self.client.get('/api/users/')
except AssertionError as e:
    # Full report is in the exception
    print(e)
    # Decide what to do...
```

## Real-World Example

```python
from django_mercury import monitor
from django.test import TestCase
from myapp.models import User

class UserAPIPerformanceTest(TestCase):
    def setUp(self):
        # Create test data
        User.objects.bulk_create([
            User(username=f'user{i}') for i in range(100)
        ])

    def test_user_list_without_optimization(self):
        """This will fail - demonstrates N+1 problem."""
        with monitor(query_count=5) as result:
            # Bad: N+1 queries (1 + 100 profile lookups)
            users = User.objects.all()
            for user in users:
                _ = user.profile.bio  # Triggers query per user

        # AssertionError raised with N+1 pattern details

    def test_user_list_with_optimization(self):
        """This passes - select_related prevents N+1."""
        with monitor(query_count=5) as result:
            # Good: 1 query with JOIN
            users = User.objects.select_related('profile').all()
            for user in users:
                _ = user.profile.bio  # No additional queries

        # ✅ Passes threshold checks
```

## Contributing

We welcome contributions! Mercury is designed for extensibility:

### Development Setup
```bash
# Clone repo
git clone https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing.git
cd Django-Mercury-Performance-Testing

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
python -m unittest discover tests

# Format code
black django_mercury tests --line-length 100
isort django_mercury tests --profile black
```

### Code Standards
- **Type hints required** for all new code
- **Pure functions** preferred for testability
- **Docstrings** with examples for public APIs
- **Tests** for all new functionality

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

GNU General Public License v3.0 (GPL-3.0)

We chose GPL to ensure Mercury remains:
- **Free** - No cost barriers to learning
- **Open** - Transparent development and review
- **Fair** - Improvements benefit the entire community

See [LICENSE](LICENSE) for full text.

## FAQ

**Q: Do I need to configure anything?**
A: No. Mercury works with sensible defaults. Configure only when you need stricter/looser thresholds.

**Q: Does it work with pytest?**
A: Yes. Mercury works with any test runner - it's just a context manager.

**Q: What's the performance overhead?**
A: Minimal. Django's `CaptureQueriesContext` is already optimized. SQL normalization adds ~1ms per 100 queries.

**Q: Can I use this in production?**
A: Mercury is designed for tests, not production monitoring. Use Django Debug Toolbar or APM tools for production.

**Q: Does it work with async views?**
A: Not yet. Async support is planned for v0.2.0.

**Q: Can I customize the report format?**
A: Yes. Use `result.to_dict()` and format however you want. Custom formatters can be contributed as plugins.