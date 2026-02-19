"""Utility modules for Dagster Snowflake AI integration."""

from dagster_snowflake_ai.defs.snowflake.resources import SnowflakeResourceHelper
from dagster_snowflake_ai.utils.timezone_helpers import (
    convert_to_utc,
    parse_relative_time_with_tz,
    snowflake_timestamp,
)

quote_identifier = SnowflakeResourceHelper.quote_identifier
quote_schema_table = SnowflakeResourceHelper.quote_schema_table
sanitize_column_name = SnowflakeResourceHelper.sanitize_column_name
validate_column_name = SnowflakeResourceHelper.validate_column_name
build_safe_query = SnowflakeResourceHelper.build_safe_query

__all__ = [
    "convert_to_utc",
    "snowflake_timestamp",
    "parse_relative_time_with_tz",
    "quote_identifier",
    "quote_schema_table",
    "sanitize_column_name",
    "validate_column_name",
    "build_safe_query",
]
