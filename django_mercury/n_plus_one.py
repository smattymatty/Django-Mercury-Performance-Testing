"""N+1 query pattern detection.

Detects repeated queries with different parameter values that indicate
an N+1 query problem (fetching in a loop instead of using joins/prefetch).
"""

import re
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class N1Pattern:
    """Represents a detected N+1 query pattern."""

    normalized_query: str
    count: int
    sample_queries: List[str]  # first 3 examples


def normalize_query(sql: str) -> str:
    """Normalize SQL by replacing literals with placeholders.

    Replaces:
    - UUIDs: 'a1b2c3d4-...' -> '?'
    - Strings: 'foo' -> '?'
    - Numbers: 123 -> ?
    - IN clauses: IN (1, 2, 3) -> IN (?)

    Args:
        sql: Raw SQL query string

    Returns:
        Normalized query with placeholders
    """
    result = sql

    # UUIDs (must come first - more specific than general strings)
    result = re.sub(
        r"'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'",
        "'?'",
        result,
        flags=re.IGNORECASE,
    )

    # Strings (any quoted content)
    result = re.sub(r"'[^']*'", "'?'", result)

    # Numbers (word boundaries to avoid matching in identifiers)
    result = re.sub(r"\b\d+\b", "?", result)

    # IN clauses (any content in parentheses after IN)
    result = re.sub(r"IN\s*\([^)]+\)", "IN (?)", result, flags=re.IGNORECASE)

    return result


def detect_n_plus_one(queries: List[Dict[str, str]]) -> List[N1Pattern]:
    """Analyze queries for N+1 patterns.

    Args:
        queries: List of query dicts from CaptureQueriesContext
                 Expected format: [{'sql': str, 'time': str}, ...]

    Returns:
        List of N1Pattern objects for patterns with 3+ occurrences,
        sorted by count (worst offenders first)
    """
    normalized_groups: Dict[str, List[str]] = {}

    # Group queries by normalized form
    for q in queries:
        sql = q["sql"]
        normalized = normalize_query(sql)

        if normalized not in normalized_groups:
            normalized_groups[normalized] = []
        normalized_groups[normalized].append(sql)

    # Find patterns with 3+ occurrences
    patterns = []
    for normalized, originals in normalized_groups.items():
        if len(originals) >= 3:
            patterns.append(
                N1Pattern(
                    normalized_query=normalized,
                    count=len(originals),
                    sample_queries=originals[:3],  # first 3 examples
                )
            )

    # Sort by count descending (worst offenders first)
    patterns.sort(key=lambda p: p.count, reverse=True)

    return patterns
