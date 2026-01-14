"""Environment helpers for Dagster deployments."""

import os


def get_database() -> str:
    """Get the database name from environment variable.

    Returns:
        The database name from SNOWFLAKE_DATABASE env var, or "SANDBOX" as default
    """
    return os.getenv("SNOWFLAKE_DATABASE", "SANDBOX")


def get_schema() -> str:
    """Get the schema name from environment variable.

    Returns:
        The schema name from SNOWFLAKE_SCHEMA env var, or "PUBLIC" as default
    """
    return os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")


def get_warehouse() -> str:
    """Get the warehouse name from environment variable.

    Returns:
        The warehouse name from SNOWFLAKE_WAREHOUSE env var, or "COMPUTE_WH" as default
    """
    return os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
