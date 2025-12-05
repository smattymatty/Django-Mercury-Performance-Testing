# backend/performance_testing/python_bindings/django_integration.py - Django Test Integration
# Provides a performance-aware APITestCase for comprehensive testing of Django views, models, and serializers.

# --- Standard Library Imports ---
import json
from typing import Any, Dict, Optional, Union, Callable
from django.conf import settings
import copy
from .constants import DEFAULT_THRESHOLDS

# --- Third-Party Imports ---
from rest_framework.test import APITestCase

# --- Local Imports ---
try:
    from .colors import EduLiteColorScheme, colors, get_status_icon
    from .monitor import (
        EnhancedPerformanceMetrics_Python,
        EnhancedPerformanceMonitor,
        monitor_django_model,
        monitor_django_view,
        monitor_serializer,
    )
    from .logging_config import get_logger
except ImportError:
    # Fallback for direct execution
    from colors import EduLiteColorScheme, colors, get_status_icon
    from monitor import (
        EnhancedPerformanceMetrics_Python,
        EnhancedPerformanceMonitor,
        monitor_django_model,
        monitor_django_view,
        monitor_serializer,
    )
    import logging

    get_logger = lambda name: logging.getLogger(name)

logger = get_logger("django_integration")

def _deep_merge(dest: dict, src: dict):
    """
    Recursively merge src into dest.
    """
    for key, val in src.items():
        if key in dest and isinstance(dest[key], dict) and isinstance(val, dict):
            _deep_merge(dest[key], val)
        else:
            dest[key] = val


def get_performance_thresholds():
    """
    Return a merged dict: DEFAULT_THRESHOLDS overridden by
    settings.MERCURY_PERFORMANCE_THRESHOLDS if available.
    """
    user_thresholds = getattr(settings, "MERCURY_PERFORMANCE_THRESHOLDS", {}) or {}
    merged = copy.deepcopy(DEFAULT_THRESHOLDS)
    _deep_merge(merged, user_thresholds)
    return merged





# --- Base Performance Test Case ---


class DjangoPerformanceAPITestCase(APITestCase):
    """
    An enhanced APITestCase with built-in, Django-aware performance monitoring.

    This class extends the standard APITestCase to provide a suite of tools for
    detailed performance analysis, including custom assertions, monitoring contexts,
    and reporting dashboards.
    """

    # -- Core Assertion Methods --

    def assertPerformance(
        self,
        monitor: EnhancedPerformanceMonitor,
        max_response_time: Optional[float] = None,
        max_memory_mb: Optional[float] = None,
        max_queries: Optional[int] = None,
        min_cache_hit_ratio: Optional[float] = None,
        msg: Optional[str] = None,
    ) -> None:
        """
        Asserts that comprehensive performance metrics meet specified expectations.

        Args:
            monitor (EnhancedPerformanceMonitor): The monitor instance after context exit.
            max_response_time (Optional[float]): Max response time in milliseconds.
            max_memory_mb (Optional[float]): Max memory usage in megabytes.
            max_queries (Optional[int]): Max number of database queries.
            min_cache_hit_ratio (Optional[float]): Minimum cache hit ratio.
            msg (Optional[str]): A custom message for assertion failure.
        """
        try:
            monitor.assert_performance(
                max_response_time, max_memory_mb, max_queries, min_cache_hit_ratio
            )
        except AssertionError as e:
            if msg:
                raise AssertionError(f"{msg}: {e}") from e
            raise

    def assertResponseTimeLess(
        self,
        metrics_or_monitor: Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python],
        milliseconds: float,
        msg: Optional[str] = None,
    ) -> None:
        """Asserts that the response time is less than a specified threshold."""
        metrics = (
            metrics_or_monitor.metrics
            if hasattr(metrics_or_monitor, "metrics")
            else metrics_or_monitor
        )
        if (actual := metrics.response_time) >= milliseconds:
            self.fail(
                f"{msg or ''}: Response time {actual:.2f}ms is not less than {milliseconds}ms"
            )

    def assertMemoryLess(
        self,
        metrics_or_monitor: Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python],
        megabytes: float,
        msg: Optional[str] = None,
    ) -> None:
        """Asserts that memory usage is less than a specified threshold."""
        metrics = (
            metrics_or_monitor.metrics
            if hasattr(metrics_or_monitor, "metrics")
            else metrics_or_monitor
        )
        if (actual := metrics.memory_usage) >= megabytes:
            self.fail(f"{msg or ''}: Memory usage {actual:.2f}MB is not less than {megabytes}MB")

    def assertQueriesLess(
        self,
        metrics_or_monitor: Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python],
        count: int,
        msg: Optional[str] = None,
    ) -> None:
        """Asserts that the database query count is less than a specified threshold."""
        metrics = (
            metrics_or_monitor.metrics
            if hasattr(metrics_or_monitor, "metrics")
            else metrics_or_monitor
        )
        if (actual := getattr(metrics, "query_count", 0)) >= count:
            self.fail(f"{msg or ''}: Query count {actual} is not less than {count}")

    # -- Status-Based Assertions --

    def assertPerformanceFast(
        self,
        metrics_or_monitor: Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python],
        msg: Optional[str] = None,
    ) -> None:
        """Asserts that performance is rated as 'fast' (typically < 100ms)."""
        metrics = (
            metrics_or_monitor.metrics
            if hasattr(metrics_or_monitor, "metrics")
            else metrics_or_monitor
        )
        if not metrics.is_fast:
            self.fail(f"{msg or ''}: Performance is not fast: {metrics.response_time:.2f}ms")

    def assertPerformanceNotSlow(
        self,
        metrics_or_monitor: Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python],
        msg: Optional[str] = None,
    ) -> None:
        """Asserts that performance is not rated as 'slow' (typically >= 500ms)."""
        metrics = (
            metrics_or_monitor.metrics
            if hasattr(metrics_or_monitor, "metrics")
            else metrics_or_monitor
        )
        if metrics.is_slow:
            self.fail(f"{msg or ''}: Performance is slow: {metrics.response_time:.2f}ms")

    def assertMemoryEfficient(
        self,
        metrics_or_monitor: Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python],
        msg: Optional[str] = None,
    ) -> None:
        """Asserts that memory usage is not considered intensive."""
        metrics = (
            metrics_or_monitor.metrics
            if hasattr(metrics_or_monitor, "metrics")
            else metrics_or_monitor
        )
        if metrics.is_memory_intensive:
            self.fail(f"{msg or ''}: Memory usage is intensive: {metrics.memory_usage:.2f}MB")

    # -- Django-Specific Assertions --

    def assertNoNPlusOne(
        self,
        metrics_or_monitor: Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python],
        msg: Optional[str] = None,
    ) -> None:
        """Asserts that no N+1 query patterns were detected."""
        metrics = (
            metrics_or_monitor.metrics
            if hasattr(metrics_or_monitor, "metrics")
            else metrics_or_monitor
        )
        if hasattr(metrics, "django_issues") and metrics.django_issues.has_n_plus_one:
            self.fail(f"{msg or ''}: N+1 query pattern detected.")

    def assertGoodCachePerformance(
        self,
        metrics_or_monitor: Union[EnhancedPerformanceMonitor, EnhancedPerformanceMetrics_Python],
        min_hit_ratio: float = 0.7,
        msg: Optional[str] = None,
    ) -> None:
        """Asserts that the cache hit ratio meets a minimum threshold."""
        metrics = (
            metrics_or_monitor.metrics
            if hasattr(metrics_or_monitor, "metrics")
            else metrics_or_monitor
        )
        if hasattr(metrics, "cache_hit_ratio") and metrics.cache_hit_ratio < min_hit_ratio:
            self.fail(
                f"{msg or ''}: Cache hit ratio {metrics.cache_hit_ratio:.1%} is below {min_hit_ratio:.1%}"
            )

    # --- Monitor Creation Methods ---

    def monitor_django_view(self, operation_name: str) -> EnhancedPerformanceMonitor:
        """Creates a performance monitor with full hooks for a Django view."""
        return monitor_django_view(operation_name)

    def monitor_django_model(self, operation_name: str) -> EnhancedPerformanceMonitor:
        """Creates a performance monitor for a Django model operation."""
        return monitor_django_model(operation_name)

    def monitor_serializer(self, operation_name: str) -> EnhancedPerformanceMonitor:
        """Creates a performance monitor for a serializer."""
        return monitor_serializer(operation_name)

    # --- Measurement and Analysis ---

    def measure_django_view(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        format: Optional[str] = None,
        operation_name: Optional[str] = None,
        **kwargs,
    ) -> EnhancedPerformanceMetrics_Python:
        """
        Measures the performance of a Django view with comprehensive monitoring.

        Args:
            url (str): The URL of the view to measure.
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            data (Optional[Dict[str, Any]]): Data for POST, PUT, or PATCH requests.
            format (Optional[str]): The request format (e.g., 'json').
            operation_name (Optional[str]): A custom name for the operation.
            **kwargs: Additional arguments for the client request.

        Returns:
            EnhancedPerformanceMetrics_Python: The captured performance metrics.
        """
        op_name = operation_name or f"{method} {url}"
        with monitor_django_view(op_name) as monitor:
            client_method = getattr(self.client, method.lower())
            response = (
                client_method(url, data=data, format=format, **kwargs)
                if data
                else client_method(url, **kwargs)
            )
        monitor.metrics._response = response
        return monitor.metrics

    def run_comprehensive_analysis(
        self,
        operation_name: str,
        test_function: Callable,
        operation_type: str = "general",
        expect_response_under: Optional[float] = None,
        expect_memory_under: Optional[float] = None,
        expect_queries_under: Optional[int] = None,
        expect_cache_hit_ratio_above: Optional[float] = None,
        print_analysis: bool = True,
        auto_detect_n_plus_one: bool = True,
        show_scoring: bool = True,
        test_file: Optional[str] = None,
        test_line: Optional[int] = None,
        test_method: Optional[str] = None,
        enable_educational_guidance: bool = False,
        operation_context: Optional[Dict[str, Any]] = None,
    ) -> EnhancedPerformanceMetrics_Python:
        """
        Runs a comprehensive, Django-aware performance analysis with a scoring system.

        Args:
            operation_name (str): The name of the operation being tested.
            test_function (Callable): The function to execute and monitor.
            operation_type (str): The type of operation (e.g., 'list_view').
            expect_response_under (Optional[float]): Expected max response time in ms.
            expect_memory_under (Optional[float]): Expected max memory usage in MB.
            expect_queries_under (Optional[int]): Expected max query count.
            expect_cache_hit_ratio_above (Optional[float]): Expected min cache hit ratio.
            print_analysis (bool): Whether to print the analysis report.
            auto_detect_n_plus_one (bool): Whether to automatically detect N+1 issues.
            show_scoring (bool): Whether to include scoring in the report.

        Returns:
            EnhancedPerformanceMetrics_Python: The captured performance metrics.
        """
        if print_analysis:
            logger.info(f"Starting enhanced analysis for operation: {operation_name}")
            print(
                f"{get_status_icon('info')} {colors.colorize(f'🔍 Enhanced Analysis: {operation_name}', EduLiteColorScheme.INFO, bold=True)}"
            )

        monitor = monitor_django_view(
            f"{operation_name}.comprehensive", operation_type=operation_type
        )
        if expect_response_under:
            monitor.expect_response_under(expect_response_under)
        if expect_memory_under:
            monitor.expect_memory_under(expect_memory_under)
        if expect_queries_under:
            monitor.expect_queries_under(expect_queries_under)
        if expect_cache_hit_ratio_above:
            monitor.expect_cache_hit_ratio_above(expect_cache_hit_ratio_above)

        # Set test context if provided
        if test_file and test_line and test_method:
            monitor.set_test_context(test_file, test_line, test_method)

        # Enable educational guidance if requested
        if enable_educational_guidance:
            monitor.enable_educational_guidance(operation_context)

        with monitor:
            result = test_function()

        metrics = monitor.metrics
        if auto_detect_n_plus_one and metrics.django_issues.has_n_plus_one:
            analysis = metrics.django_issues.n_plus_one_analysis
            # Fix false positive: No N+1 possible with 0 queries
            if analysis.severity_level > 0 and analysis.query_count > 0:
                logger.warning(
                    f"N+1 query pattern detected: {analysis.severity_text} severity with {analysis.query_count} queries"
                )
                print(
                    colors.colorize(
                        "🚨 POTENTIAL N+1 QUERY PROBLEM! 🚨", EduLiteColorScheme.CRITICAL, bold=True
                    )
                )
                print(
                    f"{colors.colorize(f'Severity: {analysis.severity_text} ({analysis.query_count} queries)', EduLiteColorScheme.CRITICAL, bold=True)}"
                )
                print(
                    f"{colors.colorize(f'Cause: {analysis.cause_text}', EduLiteColorScheme.WARNING)}"
                )
                print(
                    f"{colors.colorize(f'Fix: {analysis.fix_suggestion}', EduLiteColorScheme.OPTIMIZATION)}"
                )

        if print_analysis:
            print(
                metrics.get_performance_report_with_scoring()
                if show_scoring
                else metrics.detailed_report()
            )

        metrics._test_result = result
        return metrics

    # --- Dashboard and Reporting ---

    def create_enhanced_performance_dashboard_with_scoring(
        self,
        metrics: EnhancedPerformanceMetrics_Python,
        title: str = "Enhanced Performance Dashboard",
    ) -> None:
        """Creates and prints a performance dashboard that includes scoring."""
        print(metrics.get_performance_report_with_scoring())

    def create_enhanced_dashboard(
        self,
        metrics: EnhancedPerformanceMetrics_Python,
        title: str = "Enhanced Performance Dashboard",
    ) -> None:
        """
        Creates and prints a comprehensive performance dashboard with Django-specific insights.

        Args:
            metrics (EnhancedPerformanceMetrics_Python): The performance metrics to display.
            title (str): The title for the dashboard.
        """
        response_info = "N/A"
        if hasattr(metrics, "_test_result") and metrics._test_result:
            try:
                response_data = getattr(metrics._test_result, "data", {})
                if response_data:
                    response_json = json.dumps(response_data)
                    response_size_kb = len(response_json.encode("utf-8")) / 1024
                    response_info = (
                        f"{response_size_kb:.1f}KB"
                        if response_size_kb >= 1
                        else f"{len(response_json.encode('utf-8'))}B"
                    )
            except Exception:
                pass

        border_color = EduLiteColorScheme.BORDER
        accent_color = EduLiteColorScheme.ACCENT
        text_color = EduLiteColorScheme.TEXT

        logger.debug(f"Creating performance dashboard: {title}")
        print(colors.colorize(f"🎨 {title}", accent_color, bold=True))
        print(colors.colorize("╭" + "─" * 61 + "╮", border_color))
        print(
            f"{colors.colorize('│', border_color)} {colors.colorize('🚀 Performance Status:', text_color, bold=True)} {colors.format_performance_status(metrics.performance_status.value):<20}"
        )
        print(
            f"{colors.colorize('│', border_color)} {colors.colorize('📊 Response Time:', text_color)} {colors.format_metric_value(metrics.response_time, 'ms'):<25}"
        )
        print(
            f"{colors.colorize('│', border_color)} {colors.colorize('🧠 Memory Usage:', text_color)} {colors.format_metric_value(metrics.memory_usage, 'MB'):<25}"
        )
        print(
            f"{colors.colorize('│', border_color)} {colors.colorize('🗃️ Database Queries:', text_color)} {metrics.query_count:<25}"
        )
        print(
            f"{colors.colorize('│', border_color)} {colors.colorize('💾 Cache Hit Ratio:', text_color)} {f'{metrics.cache_hit_ratio:.1%}':<25}"
        )
        print(
            f"{colors.colorize('│', border_color)} {colors.colorize('📄 Response Size:', text_color)} {response_info:<25}"
        )
        print(colors.colorize("╰" + "─" * 61 + "╯", border_color))

        if metrics.django_issues.has_issues:
            print(
                colors.colorize(
                    "🚨 Django Performance Issues:", EduLiteColorScheme.CRITICAL, bold=True
                )
            )
            for issue in metrics.django_issues.get_issue_summary():
                print(f"   • {colors.colorize(issue, EduLiteColorScheme.CRITICAL)}")
