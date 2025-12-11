"""HTML export functionality for Mercury performance reports.

Generates standalone HTML files with inline CSS for easy sharing.
"""

import statistics
from datetime import datetime
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from .monitor import MonitorResult


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mercury Performance Report - {test_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}

        h1 {{
            color: #1a202c;
            font-size: 32px;
            margin-bottom: 8px;
        }}

        h2 {{
            color: #2d3748;
            font-size: 24px;
            margin-bottom: 16px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px 12px 0 0;
        }}

        .header h1 {{
            color: white;
        }}

        .status {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status.pass {{
            background: #d4edda;
            color: #155724;
        }}

        .status.fail {{
            background: #f8d7da;
            color: #721c24;
        }}

        .meta {{
            color: #718096;
            font-size: 14px;
            margin-top: 8px;
        }}

        .meta code {{
            background: #f7fafc;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            color: #667eea;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .metric {{
            background: #f7fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #cbd5e0;
        }}

        .metric.pass {{
            border-left-color: #48bb78;
        }}

        .metric.fail {{
            border-left-color: #f56565;
        }}

        .metric-label {{
            color: #718096;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: #1a202c;
        }}

        .metric-value.pass {{
            color: #38a169;
        }}

        .metric-value.fail {{
            color: #e53e3e;
        }}

        .metric-threshold {{
            color: #a0aec0;
            font-size: 13px;
            margin-top: 4px;
        }}

        .pattern {{
            background: #fff5f5;
            border-left: 4px solid #fc8181;
            padding: 16px;
            margin-bottom: 16px;
            border-radius: 4px;
        }}

        .pattern-header {{
            font-weight: 600;
            color: #742a2a;
            margin-bottom: 8px;
        }}

        .pattern-count {{
            display: inline-block;
            background: #feb2b2;
            color: #742a2a;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
        }}

        .pattern-sql {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 13px;
            color: #2d3748;
            background: white;
            padding: 12px;
            border-radius: 4px;
            margin-top: 8px;
            overflow-x: auto;
            line-height: 1.5;
        }}

        .sample-queries {{
            margin-top: 12px;
        }}

        .sample-label {{
            font-size: 12px;
            color: #718096;
            font-weight: 600;
            margin-bottom: 6px;
        }}

        .sample {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 12px;
            color: #4a5568;
            background: #f7fafc;
            padding: 8px;
            border-radius: 4px;
            margin-bottom: 6px;
            overflow-x: auto;
        }}

        .warning {{
            background: #fffaf0;
            border-left: 4px solid #ed8936;
            padding: 12px 16px;
            margin-bottom: 12px;
            border-radius: 4px;
        }}

        .warning-icon {{
            color: #c05621;
            font-weight: 700;
            margin-right: 8px;
        }}

        .warning-text {{
            color: #744210;
            font-size: 14px;
        }}

        .failure {{
            background: #fff5f5;
            border-left: 4px solid #fc8181;
            padding: 12px 16px;
            margin-bottom: 12px;
            border-radius: 4px;
        }}

        .failure-icon {{
            color: #c53030;
            font-weight: 700;
            margin-right: 8px;
        }}

        .failure-text {{
            color: #742a2a;
            font-size: 14px;
        }}

        .footer {{
            text-align: center;
            color: white;
            font-size: 13px;
            margin-top: 40px;
            opacity: 0.9;
        }}

        .footer a {{
            color: white;
            text-decoration: underline;
        }}

        .no-patterns {{
            color: #38a169;
            font-size: 16px;
            padding: 20px;
            text-align: center;
            background: #f0fff4;
            border-radius: 8px;
        }}

        .no-patterns::before {{
            content: "✓";
            display: inline-block;
            margin-right: 8px;
            font-weight: 700;
            font-size: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Card -->
        <div class="card header">
            <h1>Mercury Performance Report</h1>
            <div class="meta">
                <div><strong>Test:</strong> {test_name}</div>
                <div><strong>Location:</strong> <code>{test_location}</code></div>
                <div style="margin-top: 12px;">
                    <span class="status {status_class}">{status}</span>
                </div>
            </div>
        </div>

        <!-- Metrics Card -->
        <div class="card">
            <h2>Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric {time_class}">
                    <div class="metric-label">Response Time</div>
                    <div class="metric-value {time_class}">{response_time}ms</div>
                    <div class="metric-threshold">Threshold: {time_threshold}ms</div>
                </div>
                <div class="metric {query_class}">
                    <div class="metric-label">Query Count</div>
                    <div class="metric-value {query_class}">{query_count}</div>
                    <div class="metric-threshold">Threshold: {query_threshold}</div>
                </div>
            </div>
        </div>

        {n_plus_one_section}

        {warnings_section}

        {failures_section}

        <div class="footer">
            Generated by <a href="https://github.com/yourusername/django-mercury-performance" target="_blank">Django Mercury Performance Testing</a> v0.1.1
        </div>
    </div>
</body>
</html>
"""


def export_html(result: "MonitorResult", filename: str) -> None:
    """Export MonitorResult to standalone HTML file.

    Args:
        result: MonitorResult instance with test metrics
        filename: Path to output HTML file

    Example:
        with monitor() as result:
            response = self.client.get('/api/users/')

        result.to_html('performance_report.html')
    """
    # Determine status
    status = "PASSED" if not result.failures else "FAILED"
    status_class = "pass" if not result.failures else "fail"

    # Color-code metrics
    time_class = (
        "pass" if result.response_time_ms <= result.thresholds["response_time_ms"] else "fail"
    )
    query_class = "pass" if result.query_count <= result.thresholds["query_count"] else "fail"

    # Format N+1 section
    n_plus_one_section = _format_n_plus_one_html(result)

    # Format warnings section
    warnings_section = _format_warnings_html(result.warnings) if result.warnings else ""

    # Format failures section
    failures_section = _format_failures_html(result.failures) if result.failures else ""

    # Generate HTML
    html = HTML_TEMPLATE.format(
        test_name=_escape_html(result.test_name or "Unknown Test"),
        test_location=_escape_html(result.test_location or "Unknown Location"),
        status=status,
        status_class=status_class,
        response_time=f"{result.response_time_ms:.2f}",
        time_threshold=result.thresholds["response_time_ms"],
        time_class=time_class,
        query_count=result.query_count,
        query_threshold=result.thresholds["query_count"],
        query_class=query_class,
        n_plus_one_section=n_plus_one_section,
        warnings_section=warnings_section,
        failures_section=failures_section,
    )

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


def _format_n_plus_one_html(result: "MonitorResult") -> str:
    """Format N+1 patterns section as HTML."""
    if not result.n_plus_one_patterns:
        return """
        <div class="card">
            <h2>N+1 Query Patterns</h2>
            <div class="no-patterns">No N+1 patterns detected</div>
        </div>
        """

    patterns_html = []
    for pattern in result.n_plus_one_patterns:
        # Determine severity
        threshold = result.thresholds["n_plus_one_threshold"]
        if pattern.count >= threshold:
            severity = "FAILURE"
        elif pattern.count >= int(threshold * 0.8):
            severity = "WARNING"
        else:
            severity = "NOTICE"

        # Format sample queries
        samples_html = ""
        if pattern.sample_queries:
            samples = []
            for query in pattern.sample_queries[:3]:
                samples.append(f'<div class="sample">{_escape_html(query)}</div>')
            samples_html = f"""
            <div class="sample-queries">
                <div class="sample-label">Sample Queries:</div>
                {''.join(samples)}
            </div>
            """

        pattern_html = f"""
        <div class="pattern">
            <div class="pattern-header">
                {severity}: <span class="pattern-count">{pattern.count}x</span>
            </div>
            <div class="pattern-sql">{_escape_html(pattern.normalized_query)}</div>
            {samples_html}
        </div>
        """
        patterns_html.append(pattern_html)

    return f"""
    <div class="card">
        <h2>N+1 Query Patterns Detected</h2>
        {''.join(patterns_html)}
    </div>
    """


def _format_warnings_html(warnings: list) -> str:
    """Format warnings section as HTML."""
    if not warnings:
        return ""

    warnings_html = []
    for warning in warnings:
        warnings_html.append(
            f"""
        <div class="warning">
            <span class="warning-icon">⚠</span>
            <span class="warning-text">{_escape_html(warning)}</span>
        </div>
        """
        )

    return f"""
    <div class="card">
        <h2>Warnings</h2>
        {''.join(warnings_html)}
    </div>
    """


def _format_failures_html(failures: list) -> str:
    """Format failures section as HTML."""
    if not failures:
        return ""

    failures_html = []
    for failure in failures:
        # Handle multi-line failures (preserve formatting)
        failure_text = _escape_html(failure).replace("\n", "<br>")
        failures_html.append(
            f"""
        <div class="failure">
            <span class="failure-icon">✗</span>
            <span class="failure-text">{failure_text}</span>
        </div>
        """
        )

    return f"""
    <div class="card">
        <h2>Failures</h2>
        {''.join(failures_html)}
    </div>
    """


def _escape_html(text: str) -> str:
    """Escape HTML special characters.

    Args:
        text: Text to escape

    Returns:
        HTML-safe text
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


# ============================================================================
# Summary HTML Export (Multiple Tests)
# ============================================================================

SUMMARY_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mercury Performance Test Summary - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}

        h1 {{
            color: #1a202c;
            font-size: 36px;
            margin-bottom: 12px;
        }}

        h2 {{
            color: #2d3748;
            font-size: 24px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }}

        h3 {{
            color: #4a5568;
            font-size: 18px;
            margin: 16px 0 12px 0;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }}

        .header h1 {{
            color: white;
        }}

        .timestamp {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
            margin-top: 8px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .stat {{
            background: #f7fafc;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #cbd5e0;
        }}

        .stat.pass {{
            border-left-color: #48bb78;
        }}

        .stat.fail {{
            border-left-color: #f56565;
        }}

        .stat-label {{
            color: #718096;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: #1a202c;
        }}

        .stat-value.pass {{
            color: #38a169;
        }}

        .stat-value.fail {{
            color: #e53e3e;
        }}

        .test-list {{
            list-style: none;
        }}

        .test-item {{
            background: #f7fafc;
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 8px;
            border-left: 4px solid #cbd5e0;
        }}

        .test-item.pass {{
            border-left-color: #48bb78;
        }}

        .test-item.fail {{
            border-left-color: #f56565;
        }}

        .test-name {{
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 6px;
        }}

        .test-name.pass::before {{
            content: "✓ ";
            color: #38a169;
            font-weight: 700;
        }}

        .test-name.fail::before {{
            content: "✗ ";
            color: #e53e3e;
            font-weight: 700;
        }}

        .test-metrics {{
            color: #718096;
            font-size: 14px;
        }}

        .test-metrics span {{
            margin-right: 16px;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}

        .badge.n1 {{
            background: #fed7d7;
            color: #742a2a;
        }}

        .badge.slow {{
            background: #fef5e7;
            color: #7d6608;
        }}

        details {{
            margin-bottom: 12px;
        }}

        summary {{
            cursor: pointer;
            padding: 12px;
            background: #f7fafc;
            border-radius: 6px;
            font-weight: 600;
            color: #2d3748;
            user-select: none;
        }}

        summary:hover {{
            background: #edf2f7;
        }}

        .detail-content {{
            padding: 16px;
            margin-top: 8px;
            background: #ffffff;
            border-left: 3px solid #e2e8f0;
        }}

        .pattern-summary {{
            background: #fff5f5;
            border-left: 4px solid #fc8181;
            padding: 16px;
            margin-bottom: 16px;
            border-radius: 6px;
        }}

        .pattern-query {{
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 13px;
            color: #2d3748;
            background: white;
            padding: 10px;
            border-radius: 4px;
            margin: 8px 0;
            overflow-x: auto;
        }}

        .pattern-tests {{
            margin-top: 10px;
            font-size: 13px;
            color: #718096;
        }}

        .footer {{
            text-align: center;
            color: white;
            font-size: 13px;
            margin-top: 40px;
            opacity: 0.9;
        }}

        .footer a {{
            color: white;
            text-decoration: underline;
        }}

        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: #48bb78;
            transition: width 0.3s ease;
        }}

        .progress-fill.fail {{
            background: #f56565;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="card header">
            <h1>⚡ Mercury Performance Test Summary</h1>
            <div class="timestamp">Generated: {timestamp}</div>
        </div>

        <!-- Dashboard Stats -->
        <div class="card">
            <h2>Test Run Statistics</h2>
            <div class="stats-grid">
                <div class="stat">
                    <div class="stat-label">Total Tests</div>
                    <div class="stat-value">{total_tests}</div>
                </div>
                <div class="stat pass">
                    <div class="stat-label">Passed</div>
                    <div class="stat-value pass">{passed_tests}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pass_percent}%"></div>
                    </div>
                </div>
                <div class="stat fail">
                    <div class="stat-label">Failed</div>
                    <div class="stat-value fail">{failed_tests}</div>
                    <div class="progress-bar">
                        <div class="progress-fill fail" style="width: {fail_percent}%"></div>
                    </div>
                </div>
                <div class="stat">
                    <div class="stat-label">Avg Response Time</div>
                    <div class="stat-value">{avg_time:.1f}<small style="font-size: 16px;">ms</small></div>
                </div>
                <div class="stat">
                    <div class="stat-label">Avg Query Count</div>
                    <div class="stat-value">{avg_queries:.1f}</div>
                </div>
            </div>
        </div>

        {slowest_section}

        {n_plus_one_section}

        {all_tests_section}

        <div class="footer">
            Generated by <a href="https://github.com/yourusername/django-mercury-performance" target="_blank">Django Mercury Performance Testing</a> v0.1.1
        </div>
    </div>
</body>
</html>
"""


def export_summary_html(results: List[Tuple[str, "MonitorResult"]], filename: str) -> None:
    """Export summary of multiple test results to HTML.

    Args:
        results: List of (test_name, MonitorResult) tuples
        filename: Output HTML file path

    Example:
        from django_mercury.summary import MercurySummaryTracker
        tracker = MercurySummaryTracker.instance()
        # After running tests...
        export_summary_html(tracker.results, 'report.html')
    """
    if not results:
        # Create empty report
        html = SUMMARY_HTML_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            pass_percent=0,
            fail_percent=0,
            avg_time=0,
            avg_queries=0,
            slowest_section="",
            n_plus_one_section="",
            all_tests_section="<div class='card'><h2>No tests found</h2></div>",
        )
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        return

    # Calculate stats
    total = len(results)
    passed = sum(1 for _, r in results if not r.failures)
    failed = total - passed
    pass_percent = (passed / total * 100) if total > 0 else 0
    fail_percent = (failed / total * 100) if total > 0 else 0

    response_times = [r.response_time_ms for _, r in results]
    query_counts = [r.query_count for _, r in results]
    avg_time = statistics.mean(response_times)
    avg_queries = statistics.mean(query_counts)

    # Generate sections
    slowest_section = _format_slowest_section(results)
    n_plus_one_section = _format_n_plus_one_summary(results)
    all_tests_section = _format_all_tests_section(results)

    # Generate HTML
    html = SUMMARY_HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_tests=total,
        passed_tests=passed,
        failed_tests=failed,
        pass_percent=pass_percent,
        fail_percent=fail_percent,
        avg_time=avg_time,
        avg_queries=avg_queries,
        slowest_section=slowest_section,
        n_plus_one_section=n_plus_one_section,
        all_tests_section=all_tests_section,
    )

    # Write to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


def _format_slowest_section(results: List[Tuple[str, "MonitorResult"]]) -> str:
    """Format slowest tests section."""
    sorted_results = sorted(results, key=lambda x: x[1].response_time_ms, reverse=True)
    top_10 = sorted_results[:10]

    items = []
    for test_name, result in top_10:
        has_failures = "fail" if result.failures else "pass"
        has_n1 = ' <span class="badge n1">N+1</span>' if result.n_plus_one_patterns else ""

        items.append(
            f"""
        <li class="test-item {has_failures}">
            <div class="test-name {has_failures}">{_escape_html(test_name)}</div>
            <div class="test-metrics">
                <span><strong>{result.response_time_ms:.2f}ms</strong></span>
                <span>{result.query_count} queries</span>
                {has_n1}
            </div>
        </li>
        """
        )

    return f"""
    <div class="card">
        <h2>🐌 Slowest Tests (Top 10)</h2>
        <ul class="test-list">
            {''.join(items)}
        </ul>
    </div>
    """


def _format_n_plus_one_summary(results: List[Tuple[str, "MonitorResult"]]) -> str:
    """Format N+1 patterns aggregated across all tests."""
    # Aggregate N+1 patterns
    pattern_map = {}  # normalized_query -> (count, [test_names])

    for test_name, result in results:
        for pattern in result.n_plus_one_patterns:
            key = pattern.normalized_query
            if key not in pattern_map:
                pattern_map[key] = (pattern.count, [test_name], pattern.sample_queries[:2])
            else:
                old_count, test_list, samples = pattern_map[key]
                pattern_map[key] = (old_count + pattern.count, test_list + [test_name], samples)

    if not pattern_map:
        return """
        <div class="card">
            <h2>🔄 N+1 Query Patterns</h2>
            <div style="text-align: center; padding: 30px; color: #38a169;">
                ✓ No N+1 patterns detected across all tests
            </div>
        </div>
        """

    # Sort by total count
    sorted_patterns = sorted(pattern_map.items(), key=lambda x: x[1][0], reverse=True)

    items = []
    for query, (count, test_names, samples) in sorted_patterns[:15]:  # Top 15
        unique_tests = list(set(test_names))
        test_list = "<br>".join(f"• {_escape_html(t)}" for t in unique_tests[:5])
        if len(unique_tests) > 5:
            test_list += f"<br>• ... and {len(unique_tests) - 5} more"

        sample_html = ""
        if samples:
            sample_html = "<br>".join(
                f'<div class="pattern-query">{_escape_html(s)}</div>' for s in samples[:1]
            )

        items.append(
            f"""
        <div class="pattern-summary">
            <div style="font-weight: 600; color: #742a2a; margin-bottom: 8px;">
                {count}x occurrences across {len(unique_tests)} test(s)
            </div>
            <div class="pattern-query">{_escape_html(query[:150])}{'' if len(query) <= 150 else '...'}</div>
            {sample_html}
            <div class="pattern-tests">
                <strong>Affected tests:</strong><br>
                {test_list}
            </div>
        </div>
        """
        )

    return f"""
    <div class="card">
        <h2>🔄 N+1 Query Patterns (Aggregated)</h2>
        <div style="margin-bottom: 16px; color: #742a2a; font-size: 14px;">
            Found {len(pattern_map)} unique pattern(s) across all tests
        </div>
        {''.join(items)}
    </div>
    """


def _format_all_tests_section(results: List[Tuple[str, "MonitorResult"]]) -> str:
    """Format all test results with expandable details."""
    items = []

    for test_name, result in results:
        has_failures = "fail" if result.failures else "pass"
        status_icon = "✓" if not result.failures else "✗"
        has_n1 = ' <span class="badge n1">N+1</span>' if result.n_plus_one_patterns else ""

        # Build detail content
        detail_parts = []

        # Metrics
        detail_parts.append(
            f"""
            <div style="background: #f7fafc; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                <strong>Metrics:</strong><br>
                • Response time: {result.response_time_ms:.2f}ms (threshold: {result.thresholds['response_time_ms']}ms)<br>
                • Query count: {result.query_count} (threshold: {result.thresholds['query_count']})<br>
                • Location: <code style="font-size: 12px;">{_escape_html(result.test_location or 'N/A')}</code>
            </div>
            """
        )

        # N+1 patterns
        if result.n_plus_one_patterns:
            n1_list = "<br>".join(
                f"• {p.count}x: {_escape_html(p.normalized_query[:100])}"
                for p in result.n_plus_one_patterns[:3]
            )
            detail_parts.append(
                f"""
                <div style="background: #fff5f5; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                    <strong style="color: #742a2a;">N+1 Patterns:</strong><br>
                    {n1_list}
                </div>
                """
            )

        # Failures
        if result.failures:
            failures_list = "<br><br>".join(_escape_html(f) for f in result.failures)
            detail_parts.append(
                f"""
                <div style="background: #fff5f5; padding: 12px; border-radius: 6px; border-left: 3px solid #f56565;">
                    <strong style="color: #742a2a;">Failures:</strong><br>
                    {failures_list.replace(chr(10), '<br>')}
                </div>
                """
            )

        detail_content = "".join(detail_parts)

        items.append(
            f"""
        <details>
            <summary>
                <span style="color: {'#38a169' if not result.failures else '#e53e3e'}; font-weight: 700;">{status_icon}</span>
                {_escape_html(test_name)} -
                <span style="color: #718096;">{result.response_time_ms:.2f}ms, {result.query_count} queries</span>
                {has_n1}
            </summary>
            <div class="detail-content">
                {detail_content}
            </div>
        </details>
        """
        )

    return f"""
    <div class="card">
        <h2>📋 All Test Results ({len(results)} tests)</h2>
        {''.join(items)}
    </div>
    """
