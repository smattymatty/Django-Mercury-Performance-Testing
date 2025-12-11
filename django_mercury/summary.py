"""Global summary tracking for Mercury performance tests.

Automatically collects results from all monitor() usages and prints
a summary report at program exit.
"""

import atexit
import os
import statistics
from typing import List, Tuple

from .monitor import MonitorResult


class MercurySummaryTracker:
    """Global singleton to track all monitor results.

    Automatically registers atexit handler to print summary.
    Disable with MERCURY_NO_SUMMARY=1 environment variable.
    """

    _instance = None
    results: List[Tuple[str, MonitorResult]] = []

    def __init__(self):
        """Initialize tracker and register exit handler."""
        atexit.register(self.print_summary)

    @classmethod
    def instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_result(self, test_name: str, result: MonitorResult):
        """Record a test result.

        Args:
            test_name: Name of the test (e.g., "TestClass.test_method")
            result: MonitorResult instance with metrics
        """
        self.results.append((test_name, result))

    def export_html(self, filename: str) -> None:
        """Export all collected results to HTML report.

        Args:
            filename: Output HTML file path

        Example:
            from django_mercury.summary import MercurySummaryTracker
            tracker = MercurySummaryTracker.instance()
            tracker.export_html('performance_report.html')
        """
        from .export import export_summary_html

        export_summary_html(self.results, filename)

    def print_summary(self):
        """Print summary report at program exit.

        Skipped if:
        - No results collected
        - MERCURY_NO_SUMMARY=1 (or 'true', 'yes', 'on')

        Note: MERCURY_NO_SUMMARY=0 will NOT disable (must be explicitly truthy)
        """
        if not self.results:
            return

        # Check if summary is disabled (must be explicitly truthy value)
        no_summary = os.getenv('MERCURY_NO_SUMMARY', '').lower()
        if no_summary in ('1', 'true', 'yes', 'on'):
            return

        # Import Colors here to respect NO_COLOR env var at runtime
        from .monitor import Colors

        c = Colors
        lines = []

        # Header
        lines.append(f"\n{c.BOLD}{'=' * 80}{c.RESET}")
        lines.append(f"{c.BOLD}{c.CYAN}MERCURY SUMMARY{c.RESET}")
        lines.append(f"{c.BOLD}{'=' * 80}{c.RESET}\n")

        # Calculate stats
        total = len(self.results)
        passed = sum(1 for _, r in self.results if not r.failures)
        failed = total - passed

        # Overall stats
        lines.append(f"{c.BOLD}Total tests monitored:{c.RESET} {total}")
        lines.append(
            f"{c.GREEN}Passed:{c.RESET} {passed} ({passed/total*100:.0f}%)  "
            f"{c.RED}Failed:{c.RESET} {failed} ({failed/total*100:.0f}%)"
        )

        # Slowest tests (top 5)
        sorted_by_time = sorted(self.results, key=lambda x: x[1].response_time_ms, reverse=True)
        lines.append(f"\n{c.BOLD}Slowest tests:{c.RESET}")
        for i, (name, result) in enumerate(sorted_by_time[:5], 1):
            n1_indicator = f", {c.YELLOW}N+1{c.RESET}" if result.n_plus_one_patterns else ""
            lines.append(
                f"  {i}. {name} - "
                f"{c.DIM}{result.response_time_ms:.2f}ms{c.RESET} "
                f"({result.query_count} queries{n1_indicator})"
            )

        # Top issues
        n1_count = sum(1 for _, r in self.results if r.n_plus_one_patterns)
        time_exceeded = sum(
            1
            for _, r in self.results
            if r.response_time_ms > r.thresholds.get("response_time_ms", float("inf"))
        )
        query_exceeded = sum(
            1
            for _, r in self.results
            if r.query_count > r.thresholds.get("query_count", float("inf"))
        )

        if n1_count or time_exceeded or query_exceeded:
            lines.append(f"\n{c.BOLD}Top issues:{c.RESET}")
            if n1_count:
                lines.append(f"  {c.YELLOW}•{c.RESET} {n1_count} test(s) with N+1 patterns")
            if time_exceeded:
                lines.append(
                    f"  {c.YELLOW}•{c.RESET} {time_exceeded} test(s) exceeded response time threshold"
                )
            if query_exceeded:
                lines.append(
                    f"  {c.YELLOW}•{c.RESET} {query_exceeded} test(s) exceeded query count threshold"
                )

        # Average metrics
        response_times = [r.response_time_ms for _, r in self.results]
        query_counts = [r.query_count for _, r in self.results]

        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        avg_queries = statistics.mean(query_counts)
        median_queries = statistics.median(query_counts)

        lines.append(f"\n{c.BOLD}Average metrics:{c.RESET}")
        lines.append(
            f"  Response time: {c.DIM}{avg_time:.2f}ms{c.RESET} "
            f"(median: {median_time:.2f}ms)"
        )
        lines.append(
            f"  Query count: {c.DIM}{avg_queries:.1f}{c.RESET} " f"(median: {median_queries:.0f})"
        )

        # Footer with disable instruction
        lines.append(f"\n{c.DIM}To disable this summary: export MERCURY_NO_SUMMARY=1{c.RESET}")
        lines.append(f"{c.BOLD}{'=' * 80}{c.RESET}\n")

        print("\n".join(lines))
