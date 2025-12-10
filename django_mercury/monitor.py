"""Performance monitoring context manager for Django tests.

Provides a simple context manager that captures response time, query count,
and detects N+1 query patterns. Automatically validates against configurable
thresholds and raises AssertionError on violations.
"""

import inspect
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

from .config import resolve_thresholds
from .n_plus_one import N1Pattern, detect_n_plus_one


@dataclass
class MonitorResult:
    """Results from a performance monitoring session.

    Immutable after monitoring completes. All fields are populated
    by the monitor context manager on exit.

    Attributes:
        response_time_ms: Elapsed time in milliseconds
        query_count: Number of database queries executed
        queries: Raw query dicts from Django's CaptureQueriesContext
        n_plus_one_patterns: Detected N+1 patterns (sorted by severity)
        thresholds: Resolved threshold values used for this monitor
        used_defaults: True if no custom config was found
        failures: List of threshold violations (causes AssertionError)
        warnings: List of performance warnings (informational only)
        test_name: Name of the test method (e.g., "TestClass.test_method")
        test_location: Clickable file:line location (e.g., "tests/test_api.py:42")

    Example:
        with monitor() as m:
            response = self.client.get('/api/users/')

        # Inspect results
        print(f"Time: {m.response_time_ms:.2f}ms")
        print(f"Queries: {m.query_count}")

        # Detailed report
        m.explain()
    """

    # Metrics (populated on exit)
    response_time_ms: float = 0.0
    query_count: int = 0
    queries: List[Dict[str, str]] = field(default_factory=list)
    n_plus_one_patterns: List[N1Pattern] = field(default_factory=list)

    # Configuration (populated on entry)
    thresholds: Dict[str, int] = field(default_factory=dict)
    used_defaults: bool = False

    # Results (populated by _check_thresholds)
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Context info (populated on entry)
    test_name: str = ""
    test_location: str = ""

    def explain(self, file=None) -> None:
        """Print detailed performance report.

        Args:
            file: Output stream (default: stdout)

        Prints a formatted report showing:
        - Metrics (time, queries)
        - N+1 patterns with examples
        - Warnings and failures
        - Configuration source
        """
        report = _format_report(self)
        print(report, file=file)

    def __str__(self) -> str:
        """Quick summary for debugging."""
        return (
            f"MonitorResult(time={self.response_time_ms:.2f}ms, "
            f"queries={self.query_count}, "
            f"n+1_patterns={len(self.n_plus_one_patterns)}, "
            f"failures={len(self.failures)})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Useful for JSON export or custom formatters.

        Returns:
            Dictionary with all fields, with N1Pattern objects
            converted to dicts.
        """
        return {
            "response_time_ms": self.response_time_ms,
            "query_count": self.query_count,
            "queries": self.queries,
            "n_plus_one_patterns": [
                {
                    "normalized_query": p.normalized_query,
                    "count": p.count,
                    "sample_queries": p.sample_queries,
                }
                for p in self.n_plus_one_patterns
            ],
            "thresholds": self.thresholds,
            "used_defaults": self.used_defaults,
            "failures": self.failures,
            "warnings": self.warnings,
            "test_name": self.test_name,
            "test_location": self.test_location,
        }


@contextmanager
def monitor(**inline_overrides: Any) -> Iterator[MonitorResult]:
    """Monitor Django test performance with automatic threshold checking.

    Context manager that captures response time, query count, and
    detects N+1 query patterns. Automatically raises AssertionError
    if any thresholds are exceeded.

    Args:
        **inline_overrides: Direct threshold overrides
            - response_time_ms: Max response time in milliseconds
            - query_count: Max number of queries
            - n_plus_one_threshold: Min count to fail on N+1 pattern

    Yields:
        MonitorResult: Results object (populated on exit)

    Raises:
        AssertionError: If any thresholds exceeded on context exit

    Configuration Priority:
        1. Inline kwargs (highest)
        2. File-level MERCURY_PERFORMANCE_THRESHOLDS
        3. Django settings.MERCURY_PERFORMANCE_THRESHOLDS
        4. DEFAULTS (lowest)

    Example:
        # Basic usage
        with monitor() as m:
            response = self.client.get('/api/users/')

        # Custom thresholds
        with monitor(response_time_ms=50, query_count=5) as m:
            response = self.client.get('/api/users/')

        # Inspect results after context (if no failures)
        try:
            with monitor() as m:
                response = self.client.get('/api/users/')
        except AssertionError:
            pass  # Full report included in exception

        # Or check results manually
        m.explain()

    Note:
        - Requires Django to be configured (uses connection.queries)
        - Best used in Django TestCase subclasses
        - On failure, full report is automatically included in AssertionError
    """
    result = MonitorResult()

    # Phase 1: Resolve configuration and capture context (on entry)
    result.thresholds, result.used_defaults = resolve_thresholds(**inline_overrides)

    # Capture test name and location from call stack
    stack = inspect.stack()
    for frame_info in stack[1:]:  # Skip monitor() itself
        frame = frame_info.frame
        # Look for test method (starts with 'test_' or is in a TestCase)
        code = frame.f_code
        func_name = code.co_name

        if func_name.startswith('test_') or '_test_' in func_name.lower():
            # Found test method
            file_path = code.co_filename
            line_number = frame_info.lineno

            # Get relative path from cwd
            try:
                rel_path = os.path.relpath(file_path)
            except ValueError:
                rel_path = file_path

            # Get class name if available
            if 'self' in frame.f_locals:
                cls = frame.f_locals['self'].__class__
                result.test_name = f"{cls.__name__}.{func_name}"
            else:
                result.test_name = func_name

            result.test_location = f"{rel_path}:{line_number}"
            break

    # Warn if using defaults
    if result.used_defaults:
        result.warnings.append(
            "No MERCURY_PERFORMANCE_THRESHOLDS config found. Using defaults. "
            "Configure in settings.py or test file to remove this warning."
        )

    # Phase 2: Capture metrics (during body)
    start_time = time.perf_counter()

    # Import Django components here to avoid import errors if Django not configured
    try:
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
    except ImportError as e:
        raise ImportError(
            "Django Mercury requires Django to be installed and configured. "
            f"Original error: {e}"
        ) from e

    with CaptureQueriesContext(connection) as query_context:
        yield result  # User code runs here

    end_time = time.perf_counter()

    # Phase 3: Process results (on exit)
    result.response_time_ms = (end_time - start_time) * 1000
    result.query_count = len(query_context)
    result.queries = list(query_context.captured_queries)

    # Detect N+1 patterns
    result.n_plus_one_patterns = detect_n_plus_one(result.queries)

    # Check thresholds
    _check_thresholds(result)

    # Raise if failures (with full report embedded)
    if result.failures:
        report = _format_report(result)
        raise AssertionError(report)


def _check_thresholds(result: MonitorResult) -> None:
    """Check all thresholds and populate result.failures and result.warnings.

    Pure function that modifies the result object in-place. Separated from
    the monitor context manager to make it testable independently.

    Args:
        result: MonitorResult with metrics and thresholds populated

    Side Effects:
        Populates result.failures and result.warnings lists

    Threshold Checks:
        1. Response time: Fail if exceeds threshold
        2. Query count: Fail if exceeds threshold
        3. N+1 patterns (dynamic based on n_plus_one_threshold):
           - >= 100%: Failure
           - >= 80%: Warning
           - >= 50% (minimum 3): Notice
    """
    thresholds = result.thresholds

    # Check 1: Response time
    if result.response_time_ms > thresholds["response_time_ms"]:
        over = result.response_time_ms - thresholds["response_time_ms"]
        result.failures.append(
            f"⏱️  Response time {result.response_time_ms:.2f}ms "
            f"exceeded threshold {thresholds['response_time_ms']}ms "
            f"(+{over:.2f}ms over)"
        )

    # Check 2: Query count
    if result.query_count > thresholds["query_count"]:
        over = result.query_count - thresholds["query_count"]
        result.failures.append(
            f"🔢 Query count {result.query_count} "
            f"exceeded threshold {thresholds['query_count']} "
            f"(+{over} extra queries)"
        )

    # Check 3: N+1 patterns (3 severity levels)
    n1_threshold = thresholds["n_plus_one_threshold"]
    warn_threshold = int(n1_threshold * 0.8)  # 80% of failure threshold
    notice_threshold = max(3, int(n1_threshold * 0.5))  # 50% or 3, whichever is higher

    for pattern in result.n_plus_one_patterns:
        if pattern.count >= n1_threshold:
            # Severity 1: Failure (threshold exceeded)
            examples = "\n".join(
                f"      → {_truncate_sql(q, 70)}" for q in pattern.sample_queries[:3]
            )
            result.failures.append(
                f"🔄 N+1 pattern detected: {pattern.count} similar queries "
                f"(threshold: {n1_threshold})\n"
                f"   Pattern: {_truncate_sql(pattern.normalized_query, 80)}\n"
                f"   Examples:\n{examples}"
            )
        elif pattern.count >= warn_threshold:
            # Severity 2: Warning (80% of threshold - approaching failure)
            result.warnings.append(
                f"⚠️  N+1 WARNING: {pattern.count} similar queries detected "
                f"(approaching threshold: {n1_threshold})\n"
                f"   Pattern: {_truncate_sql(pattern.normalized_query, 80)}\n"
                f"   Consider using select_related() or prefetch_related()"
            )
        elif pattern.count >= notice_threshold:
            # Severity 3: Notice (50% of threshold - informational)
            result.warnings.append(
                f"ℹ️  N+1 notice: {pattern.count} similar queries\n"
                f"   Pattern: {_truncate_sql(pattern.normalized_query, 80)}"
            )


def _format_report(result: MonitorResult) -> str:
    """Format a detailed performance report.

    Args:
        result: MonitorResult with all fields populated

    Returns:
        Formatted multi-line string report
    """
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("MERCURY PERFORMANCE REPORT")
    lines.append("=" * 60)

    # Test context (if available)
    if result.test_name or result.test_location:
        lines.append("")
        if result.test_name:
            lines.append(f"🧪 Test: {result.test_name}")
        if result.test_location:
            lines.append(f"📍 Location: {result.test_location}")

    # Metrics section
    lines.append("\n📊 METRICS:")
    lines.append(
        f"   Response time: {_format_duration(result.response_time_ms)} "
        f"(threshold: {_format_duration(result.thresholds['response_time_ms'])})"
    )
    lines.append(
        f"   Query count:   {result.query_count} "
        f"(threshold: {result.thresholds['query_count']})"
    )

    # N+1 patterns section
    if result.n_plus_one_patterns:
        lines.append("\n🔄 N+1 PATTERNS DETECTED:")
        for pattern in result.n_plus_one_patterns:
            severity = _format_pattern_severity(
                pattern.count, result.thresholds["n_plus_one_threshold"]
            )
            lines.append(
                f"   {severity} [{pattern.count}x] "
                f"{_truncate_sql(pattern.normalized_query, 70)}"
            )
            for sample in pattern.sample_queries[:3]:
                lines.append(f"        → {_truncate_sql(sample, 65)}")
    else:
        lines.append("\n✅ No N+1 patterns detected")

    # Warnings section
    if result.warnings:
        lines.append("\n⚠️  WARNINGS:")
        for warning in result.warnings:
            # Indent multi-line warnings
            for line in warning.split("\n"):
                lines.append(f"   {line}")

    # Failures section
    if result.failures:
        lines.append("\n❌ FAILURES:")
        for failure in result.failures:
            # Indent multi-line failures
            for line in failure.split("\n"):
                lines.append(f"   {line}")

    # Config source
    if result.used_defaults:
        lines.append("\n⚙️  Using default thresholds (no config found)")

    lines.append("\n" + "=" * 60 + "\n")
    return "\n".join(lines)


def _format_duration(ms: float) -> str:
    """Format duration in ms to human-readable string.

    Args:
        ms: Duration in milliseconds

    Returns:
        Formatted string (e.g., "123.45ms", "2.50s", "500.00μs")
    """
    if ms < 1:
        return f"{ms * 1000:.2f}μs"
    elif ms < 1000:
        return f"{ms:.2f}ms"
    else:
        return f"{ms / 1000:.2f}s"


def _truncate_sql(sql: str, max_length: int) -> str:
    """Truncate SQL query to max length.

    Args:
        sql: SQL query string
        max_length: Maximum length before truncation

    Returns:
        Truncated SQL with ellipsis if needed
    """
    if len(sql) <= max_length:
        return sql
    return sql[: max_length - 3] + "..."


def _format_pattern_severity(count: int, threshold: int) -> str:
    """Format N+1 pattern severity with emoji.

    Args:
        count: Number of similar queries
        threshold: N+1 failure threshold

    Returns:
        Severity label with emoji (e.g., "❌ FAIL", "⚠️  WARN", "ℹ️  INFO")
    """
    if count >= threshold:
        return "❌ FAIL"
    elif count >= 5:
        return "⚠️  WARN"
    else:
        return "ℹ️  INFO"
