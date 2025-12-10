"""Tests for N+1 query detection."""

import unittest
from django_mercury.n_plus_one import normalize_query, detect_n_plus_one


class NormalizeQueryTests(unittest.TestCase):
    """Tests for SQL query normalization."""

    def test_normalizes_integers(self):
        """Integers should be replaced with placeholders."""
        sql = "SELECT * FROM users WHERE id = 123"
        result = normalize_query(sql)
        self.assertEqual(result, "SELECT * FROM users WHERE id = ?")

    def test_normalizes_multiple_integers(self):
        """Multiple integers should all be replaced."""
        sql = "SELECT * FROM users WHERE id = 123 AND age = 45"
        result = normalize_query(sql)
        self.assertEqual(result, "SELECT * FROM users WHERE id = ? AND age = ?")

    def test_normalizes_strings(self):
        """Single-quoted strings should be replaced."""
        sql = "SELECT * FROM users WHERE name = 'alice'"
        result = normalize_query(sql)
        self.assertEqual(result, "SELECT * FROM users WHERE name = '?'")

    def test_normalizes_multiple_strings(self):
        """Multiple strings should all be replaced."""
        sql = "SELECT * FROM users WHERE name = 'alice' AND city = 'NYC'"
        result = normalize_query(sql)
        self.assertEqual(result, "SELECT * FROM users WHERE name = '?' AND city = '?'")

    def test_normalizes_uuids(self):
        """UUIDs should be replaced with placeholders."""
        sql = "SELECT * FROM users WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'"
        result = normalize_query(sql)
        self.assertEqual(result, "SELECT * FROM users WHERE id = '?'")

    def test_normalizes_uppercase_uuids(self):
        """UUIDs in uppercase should also be normalized."""
        sql = "SELECT * FROM users WHERE id = 'A1B2C3D4-E5F6-7890-ABCD-EF1234567890'"
        result = normalize_query(sql)
        self.assertEqual(result, "SELECT * FROM users WHERE id = '?'")

    def test_normalizes_in_clauses(self):
        """IN clauses should be normalized."""
        sql = "SELECT * FROM users WHERE id IN (1, 2, 3)"
        result = normalize_query(sql)
        self.assertEqual(result, "SELECT * FROM users WHERE id IN (?)")

    def test_normalizes_in_clauses_case_insensitive(self):
        """IN clauses should work regardless of case."""
        sql = "SELECT * FROM users WHERE id in (1, 2, 3)"
        result = normalize_query(sql)
        self.assertEqual(result, "SELECT * FROM users WHERE id IN (?)")

    def test_preserves_structure(self):
        """Table names and column names should be preserved."""
        sql = "SELECT id, name FROM users WHERE id = 123"
        result = normalize_query(sql)
        self.assertIn("users", result)
        self.assertIn("id", result)
        self.assertIn("name", result)


class DetectNPlusOneTests(unittest.TestCase):
    """Tests for N+1 pattern detection."""

    def test_detects_n_plus_one_pattern(self):
        """3+ similar queries should be detected as N+1."""
        queries = [
            {"sql": "SELECT * FROM profile WHERE user_id = 1", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 2", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 3", "time": "0.001"},
        ]

        patterns = detect_n_plus_one(queries)

        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].count, 3)
        self.assertIn("user_id = ?", patterns[0].normalized_query)

    def test_no_pattern_under_threshold(self):
        """Less than 3 similar queries should not be flagged."""
        queries = [
            {"sql": "SELECT * FROM profile WHERE user_id = 1", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 2", "time": "0.001"},
        ]

        patterns = detect_n_plus_one(queries)

        self.assertEqual(len(patterns), 0)

    def test_different_queries_not_grouped(self):
        """Completely different queries should not be grouped."""
        queries = [
            {"sql": "SELECT * FROM users WHERE id = 1", "time": "0.001"},
            {"sql": "SELECT * FROM profiles WHERE id = 2", "time": "0.001"},
            {"sql": "SELECT * FROM posts WHERE id = 3", "time": "0.001"},
        ]

        patterns = detect_n_plus_one(queries)

        self.assertEqual(len(patterns), 0)

    def test_returns_sample_queries(self):
        """Pattern should include first 3 example queries."""
        queries = [
            {"sql": "SELECT * FROM profile WHERE user_id = 1", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 2", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 3", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 4", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 5", "time": "0.001"},
        ]

        patterns = detect_n_plus_one(queries)

        self.assertEqual(len(patterns[0].sample_queries), 3)
        self.assertEqual(patterns[0].sample_queries[0], queries[0]["sql"])
        self.assertEqual(patterns[0].sample_queries[1], queries[1]["sql"])
        self.assertEqual(patterns[0].sample_queries[2], queries[2]["sql"])

    def test_sorts_by_count_descending(self):
        """Multiple patterns should be sorted by count (worst first)."""
        queries = [
            # Pattern 1: 5 queries
            {"sql": "SELECT * FROM profile WHERE user_id = 1", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 2", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 3", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 4", "time": "0.001"},
            {"sql": "SELECT * FROM profile WHERE user_id = 5", "time": "0.001"},
            # Pattern 2: 3 queries
            {"sql": "SELECT * FROM posts WHERE author_id = 10", "time": "0.001"},
            {"sql": "SELECT * FROM posts WHERE author_id = 20", "time": "0.001"},
            {"sql": "SELECT * FROM posts WHERE author_id = 30", "time": "0.001"},
        ]

        patterns = detect_n_plus_one(queries)

        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].count, 5)  # profile pattern first
        self.assertEqual(patterns[1].count, 3)  # posts pattern second


if __name__ == "__main__":
    unittest.main()
