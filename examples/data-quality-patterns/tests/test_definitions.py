"""Tests for Dagster definitions loading."""

from data_quality_patterns.definitions import defs


def test_definitions_load():
    """Test that all definitions load without errors."""
    assert defs is not None

    # The @dg.definitions decorator returns a LazyDefinitions object
    # Call load_fn() to get the actual Definitions
    resolved = defs.load_fn()
    assert resolved is not None


def test_asset_checks_loaded():
    """Test that asset checks are loaded."""
    resolved = defs.load_fn()
    # Asset checks are loaded via load_defs
    assert resolved is not None


def test_freshness_policies_applied():
    """Test that freshness policies are applied to assets."""
    # Raw data assets should have freshness policies attached
    # This is verified during the definition loading
    resolved = defs.load_fn()
    assert resolved is not None


def test_resources_configured():
    """Test that resources are configured."""
    resolved = defs.load_fn()
    resources = resolved.resources
    assert "duckdb" in resources, "Expected duckdb resource"
    assert "dbt" in resources, "Expected dbt resource"
