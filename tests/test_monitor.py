"""Tests for monitor context manager.

Note: Full integration tests with Django require Django to be configured.
These unit tests focus on the core logic (MonitorResult, _check_thresholds,
formatting functions) which can be tested without Django.
"""

import unittest
from io import StringIO

from django_mercury.monitor import (
    MonitorResult,
    _check_thresholds,
    _format_duration,
    _format_pattern_severity,
    _format_report,
    _truncate_sql,
)
from django_mercury.n_plus_one import N1Pattern


class MonitorResultTests(unittest.TestCase):
    """Tests for MonitorResult dataclass."""

    def test_monitor_result_default_values(self):
        """MonitorResult should have sensible defaults."""
        result = MonitorResult()

        self.assertEqual(result.response_time_ms, 0.0)
        self.assertEqual(result.query_count, 0)
        self.assertEqual(result.queries, [])
        self.assertEqual(result.n_plus_one_patterns, [])
        self.assertEqual(result.thresholds, {})
        self.assertEqual(result.failures, [])
        self.assertEqual(result.warnings, [])
        self.assertFalse(result.used_defaults)

    def test_monitor_result_str(self):
        """MonitorResult __str__ should show summary."""
        result = MonitorResult(
            response_time_ms=123.45, query_count=10, failures=["test failure"]
        )
        result_str = str(result)

        self.assertIn("123.45ms", result_str)
        self.assertIn("queries=10", result_str)
        self.assertIn("failures=1", result_str)

    def test_monitor_result_to_dict(self):
        """to_dict() should serialize all fields."""
        result = MonitorResult(
            response_time_ms=100.0,
            query_count=5,
            queries=[{"sql": "SELECT 1", "time": "0.001"}],
            n_plus_one_patterns=[
                N1Pattern("SELECT * FROM users WHERE id = ?", 3, ["q1", "q2", "q3"])
            ],
            thresholds={"response_time_ms": 100},
            failures=["failure"],
            warnings=["warning"],
        )

        result_dict = result.to_dict()

        self.assertEqual(result_dict["response_time_ms"], 100.0)
        self.assertEqual(result_dict["query_count"], 5)
        self.assertEqual(len(result_dict["queries"]), 1)
        self.assertEqual(len(result_dict["n_plus_one_patterns"]), 1)
        self.assertEqual(result_dict["n_plus_one_patterns"][0]["count"], 3)
        self.assertEqual(result_dict["failures"], ["failure"])
        self.assertEqual(result_dict["warnings"], ["warning"])

    def test_monitor_result_explain_no_crash(self):
        """explain() should not crash with default values."""
        result = MonitorResult(
            thresholds={"response_time_ms": 100, "query_count": 10, "n_plus_one_threshold": 10}
        )

        # Capture output to avoid cluttering test output
        output = StringIO()
        result.explain(file=output)

        self.assertIn("MERCURY PERFORMANCE REPORT", output.getvalue())


class CheckThresholdsTests(unittest.TestCase):
    """Tests for _check_thresholds() function."""

    def setUp(self):
        """Set up common test data."""
        self.thresholds = {
            "response_time_ms": 100,
            "query_count": 10,
            "n_plus_one_threshold": 10,
        }

    def test_response_time_pass(self):
        """Should not fail if response time under threshold."""
        result = MonitorResult(response_time_ms=50.0, thresholds=self.thresholds)

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 0)

    def test_response_time_failure(self):
        """Should fail if response time exceeds threshold."""
        result = MonitorResult(response_time_ms=200.0, thresholds=self.thresholds)

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 1)
        self.assertIn("Response time", result.failures[0])
        self.assertIn("200.00ms", result.failures[0])
        self.assertIn("100ms", result.failures[0])

    def test_query_count_pass(self):
        """Should not fail if query count under threshold."""
        result = MonitorResult(query_count=5, thresholds=self.thresholds)

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 0)

    def test_query_count_failure(self):
        """Should fail if query count exceeds threshold."""
        result = MonitorResult(query_count=20, thresholds=self.thresholds)

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 1)
        self.assertIn("Query count", result.failures[0])
        self.assertIn("20", result.failures[0])
        self.assertIn("10", result.failures[0])

    def test_multiple_failures(self):
        """Should report all threshold violations."""
        result = MonitorResult(
            response_time_ms=200.0, query_count=20, thresholds=self.thresholds
        )

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 2)

    def test_n_plus_one_failure(self):
        """Should fail if N+1 pattern count >= threshold."""
        result = MonitorResult(
            n_plus_one_patterns=[
                N1Pattern(
                    "SELECT * FROM users WHERE id = ?", 10, ["query1", "query2", "query3"]
                )
            ],
            thresholds=self.thresholds,
        )

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 1)
        self.assertIn("N+1 pattern", result.failures[0])
        self.assertIn("10 similar queries", result.failures[0])

    def test_n_plus_one_warning(self):
        """Should warn if N+1 pattern count >= 80% threshold."""
        result = MonitorResult(
            n_plus_one_patterns=[
                N1Pattern(
                    "SELECT * FROM users WHERE id = ?", 8, ["query1", "query2", "query3"]
                )
            ],
            thresholds=self.thresholds,
        )

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("WARNING", result.warnings[0])
        self.assertIn("8 similar queries", result.warnings[0])

    def test_n_plus_one_notice(self):
        """Should notice if N+1 pattern count >= 50% threshold."""
        result = MonitorResult(
            n_plus_one_patterns=[
                N1Pattern(
                    "SELECT * FROM users WHERE id = ?", 5, ["query1", "query2", "query3"]
                )
            ],
            thresholds=self.thresholds,
        )

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("notice", result.warnings[0])
        self.assertIn("5 similar queries", result.warnings[0])

    def test_n_plus_one_multiple_patterns(self):
        """Should handle multiple N+1 patterns with different severities."""
        result = MonitorResult(
            n_plus_one_patterns=[
                N1Pattern("SELECT * FROM users WHERE id = ?", 10, ["q1", "q2", "q3"]),  # fail (100%)
                N1Pattern("SELECT * FROM posts WHERE id = ?", 8, ["q4", "q5", "q6"]),  # warn (80%)
                N1Pattern("SELECT * FROM comments WHERE id = ?", 5, ["q7", "q8", "q9"]),  # notice (50%)
            ],
            thresholds=self.thresholds,
        )

        _check_thresholds(result)

        self.assertEqual(len(result.failures), 1)  # Only first pattern fails
        self.assertEqual(len(result.warnings), 2)  # Other two are warnings


class FormatDurationTests(unittest.TestCase):
    """Tests for _format_duration() helper."""

    def test_format_duration_microseconds(self):
        """Should format < 1ms as microseconds."""
        self.assertEqual(_format_duration(0.5), "500.00μs")
        self.assertEqual(_format_duration(0.1), "100.00μs")

    def test_format_duration_milliseconds(self):
        """Should format < 1000ms as milliseconds."""
        self.assertEqual(_format_duration(1.0), "1.00ms")
        self.assertEqual(_format_duration(123.45), "123.45ms")
        self.assertEqual(_format_duration(999.99), "999.99ms")

    def test_format_duration_seconds(self):
        """Should format >= 1000ms as seconds."""
        self.assertEqual(_format_duration(1000.0), "1.00s")
        self.assertEqual(_format_duration(2500.0), "2.50s")


class TruncateSqlTests(unittest.TestCase):
    """Tests for _truncate_sql() helper."""

    def test_truncate_sql_short(self):
        """Should not truncate short SQL."""
        sql = "SELECT * FROM users"
        self.assertEqual(_truncate_sql(sql, 50), sql)

    def test_truncate_sql_exact_length(self):
        """Should not truncate SQL at exact max length."""
        sql = "SELECT * FROM users WHERE id = 123"
        self.assertEqual(_truncate_sql(sql, len(sql)), sql)

    def test_truncate_sql_long(self):
        """Should truncate long SQL with ellipsis."""
        sql = "SELECT * FROM users WHERE id = 1 AND name = 'test' AND email = 'test@example.com'"
        truncated = _truncate_sql(sql, 30)

        self.assertEqual(len(truncated), 30)
        self.assertTrue(truncated.endswith("..."))
        self.assertEqual(truncated, "SELECT * FROM users WHERE i...")


class FormatPatternSeverityTests(unittest.TestCase):
    """Tests for _format_pattern_severity() helper."""

    def test_format_severity_failure(self):
        """Should format failure for count >= threshold."""
        self.assertEqual(_format_pattern_severity(10, 10), "❌ FAIL")
        self.assertEqual(_format_pattern_severity(15, 10), "❌ FAIL")

    def test_format_severity_warning(self):
        """Should format warning for count >= 80% threshold."""
        self.assertEqual(_format_pattern_severity(8, 10), "⚠️  WARN")  # 80% of 10
        self.assertEqual(_format_pattern_severity(9, 10), "⚠️  WARN")

    def test_format_severity_info(self):
        """Should format info for count < 80% threshold."""
        self.assertEqual(_format_pattern_severity(3, 10), "ℹ️  INFO")
        self.assertEqual(_format_pattern_severity(5, 10), "ℹ️  INFO")
        self.assertEqual(_format_pattern_severity(7, 10), "ℹ️  INFO")


class FormatReportTests(unittest.TestCase):
    """Tests for _format_report() function."""

    def test_format_report_basic(self):
        """Should format basic report with metrics."""
        result = MonitorResult(
            response_time_ms=123.45,
            query_count=5,
            thresholds={"response_time_ms": 100, "query_count": 10, "n_plus_one_threshold": 10},
        )

        report = _format_report(result)

        self.assertIn("MERCURY PERFORMANCE REPORT", report)
        self.assertIn("METRICS", report)
        self.assertIn("123.45ms", report)
        self.assertIn("5", report)
        self.assertIn("No N+1 patterns detected", report)

    def test_format_report_with_n_plus_one(self):
        """Should format N+1 patterns section."""
        result = MonitorResult(
            response_time_ms=50.0,
            query_count=5,
            n_plus_one_patterns=[
                N1Pattern(
                    "SELECT * FROM users WHERE id = ?", 5, ["query1", "query2", "query3"]
                )
            ],
            thresholds={"response_time_ms": 100, "query_count": 10, "n_plus_one_threshold": 10},
        )

        report = _format_report(result)

        self.assertIn("N+1 PATTERNS DETECTED", report)
        self.assertIn("[5x]", report)
        self.assertIn("SELECT * FROM users", report)

    def test_format_report_with_warnings(self):
        """Should format warnings section."""
        result = MonitorResult(
            response_time_ms=50.0,
            query_count=5,
            warnings=["Test warning"],
            thresholds={"response_time_ms": 100, "query_count": 10, "n_plus_one_threshold": 10},
        )

        report = _format_report(result)

        self.assertIn("WARNINGS", report)
        self.assertIn("Test warning", report)

    def test_format_report_with_failures(self):
        """Should format failures section."""
        result = MonitorResult(
            response_time_ms=50.0,
            query_count=5,
            failures=["Test failure"],
            thresholds={"response_time_ms": 100, "query_count": 10, "n_plus_one_threshold": 10},
        )

        report = _format_report(result)

        self.assertIn("FAILURES", report)
        self.assertIn("Test failure", report)

    def test_format_report_with_defaults(self):
        """Should indicate when using defaults."""
        result = MonitorResult(
            response_time_ms=50.0,
            query_count=5,
            used_defaults=True,
            thresholds={"response_time_ms": 100, "query_count": 10, "n_plus_one_threshold": 10},
        )

        report = _format_report(result)

        self.assertIn("Using default thresholds", report)


if __name__ == "__main__":
    unittest.main()
