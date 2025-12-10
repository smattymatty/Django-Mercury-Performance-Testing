"""Tests for configuration resolution.

Note: Django settings resolution is tested in Phase 5 integration tests
with a real Django project. These unit tests focus on inline and file-level config.
"""

import unittest
from django_mercury.config import resolve_thresholds, DEFAULTS


# File-level config for testing file-level resolution
MERCURY_PERFORMANCE_THRESHOLDS = {
    "response_time_ms": 500,
    "query_count": 50,
}


class ConfigResolutionTests(unittest.TestCase):
    """Tests for threshold resolution logic."""

    def test_inline_overrides_everything(self):
        """Inline kwargs should have highest priority."""
        thresholds, used_defaults = resolve_thresholds(
            response_time_ms=999, query_count=1, n_plus_one_threshold=5
        )

        self.assertEqual(thresholds["response_time_ms"], 999)
        self.assertEqual(thresholds["query_count"], 1)
        self.assertEqual(thresholds["n_plus_one_threshold"], 5)
        self.assertFalse(used_defaults)

    def test_partial_inline_overrides_merge(self):
        """Inline overrides should merge with other config, not replace entirely."""
        thresholds, used_defaults = resolve_thresholds(response_time_ms=999)

        self.assertEqual(thresholds["response_time_ms"], 999)
        # Other values come from file-level config in this test module
        self.assertEqual(thresholds["query_count"], 50)  # from file-level
        # n_plus_one_threshold not in file config, so comes from defaults
        self.assertEqual(
            thresholds["n_plus_one_threshold"], DEFAULTS["n_plus_one_threshold"]
        )
        self.assertFalse(used_defaults)

    def test_django_not_configured_gracefully_handled(self):
        """Should handle Django not being configured without crashing."""
        # Test that it doesn't crash even if Django isn't available
        # (In this test, it will find file-level config instead)
        thresholds, used_defaults = resolve_thresholds()

        # Should not crash and should return valid thresholds
        self.assertIsNotNone(thresholds)
        self.assertIn("response_time_ms", thresholds)
        self.assertIn("query_count", thresholds)
        self.assertIn("n_plus_one_threshold", thresholds)

    def test_file_level_config_detected(self):
        """File-level MERCURY_PERFORMANCE_THRESHOLDS should be detected."""
        # This test file has MERCURY_PERFORMANCE_THRESHOLDS defined at module level
        # Don't mock anything - let it find the real module variable
        thresholds, used_defaults = resolve_thresholds()

        # Should get file-level values
        self.assertEqual(thresholds["response_time_ms"], 500)
        self.assertEqual(thresholds["query_count"], 50)
        # n_plus_one_threshold should still be default (not in file config)
        self.assertEqual(
            thresholds["n_plus_one_threshold"], DEFAULTS["n_plus_one_threshold"]
        )
        self.assertFalse(used_defaults)

    def test_inline_overrides_file_level(self):
        """Inline overrides should win over file-level config."""
        # This test file has MERCURY_PERFORMANCE_THRESHOLDS with response_time_ms=500
        thresholds, used_defaults = resolve_thresholds(response_time_ms=123)

        # Inline should override file-level
        self.assertEqual(thresholds["response_time_ms"], 123)
        # But query_count should still come from file-level
        self.assertEqual(thresholds["query_count"], 50)
        self.assertFalse(used_defaults)


if __name__ == "__main__":
    unittest.main()
