"""Test resource patterns and utilities."""

from dagster_snowflake_ai.defs.resources import SnowflakeResourceHelper
from dagster_snowflake_ai.utils.timezone_helpers import (
    convert_to_utc,
    handle_pandas_timestamps,
    snowflake_timestamp,
)


class TestTimezoneHelpers:
    """Test timezone helper functions."""

    def test_convert_to_utc_naive(self):
        """Test converting naive datetime to UTC."""
        from datetime import datetime

        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        result = convert_to_utc(naive_dt)
        assert result.tzinfo is not None
        assert result.tzinfo.utcoffset(None).total_seconds() == 0

    def test_snowflake_timestamp(self):
        """Test converting to Snowflake TIMESTAMP_NTZ format."""
        from datetime import datetime, timezone

        tz_aware_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = snowflake_timestamp(tz_aware_dt)
        assert result.tzinfo is None  # Should be naive for TIMESTAMP_NTZ

    def test_handle_pandas_timestamps(self):
        """Test handling Pandas timestamps."""
        import pandas as pd

        ts = pd.Timestamp("2024-01-01 12:00:00-0500")
        series = pd.Series([ts])
        result = handle_pandas_timestamps(series)
        assert result.dt.tz is None  # Should be timezone-naive


class TestSnowflakeHelpers:
    """Test Snowflake helper functions."""

    def test_quote_identifier_number_start(self):
        """Test quoting identifier starting with number."""
        result = SnowflakeResourceHelper.quote_identifier("5_stars")
        assert result == '"5_stars"'

    def test_quote_identifier_reserved_word(self):
        """Test quoting reserved word."""
        result = SnowflakeResourceHelper.quote_identifier("SELECT")
        assert result == '"SELECT"'

    def test_quote_identifier_normal(self):
        """Test normal identifier doesn't need quoting."""
        result = SnowflakeResourceHelper.quote_identifier("normal_column")
        assert result == "normal_column"

    def test_sanitize_column_name(self):
        """Test sanitizing column names."""
        result = SnowflakeResourceHelper.sanitize_column_name("5 stars rating")
        assert result == "_5_stars_rating"
        assert result[0] == "_"  # Should start with underscore

    def test_validate_column_name(self):
        """Test validating column names."""
        assert SnowflakeResourceHelper.validate_column_name("5_stars") is True
        assert SnowflakeResourceHelper.validate_column_name("normal_column") is False
        assert SnowflakeResourceHelper.validate_column_name("SELECT") is True
