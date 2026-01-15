"""Dagster resources combining Snowflake, dbt, and ingestion resources."""

from collections.abc import Generator
from contextlib import contextmanager

import dagster as dg
from dagster_snowflake import SnowflakeResource

from dagster_snowflake_ai.defs.dbt import get_dbt_resource
from dagster_snowflake_ai.defs.ingestion.resources import WebScraperResource
from dagster_snowflake_ai.defs.snowflake.resources import SnowflakeResourceHelper


@contextmanager
def get_snowflake_connection_with_schema(
    snowflake: "SnowflakeResource",
) -> Generator[tuple[object, str], None, None]:
    """Get Snowflake connection and current schema.

    This is a convenience wrapper that yields both the connection and schema name
    for use in SQL queries that need to reference the schema explicitly.
    """
    with SnowflakeResourceHelper.get_connection_with_schema(snowflake) as result:
        yield result


if SnowflakeResource is not None:
    resources = {
        "snowflake": SnowflakeResource(
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
            warehouse=dg.EnvVar("SNOWFLAKE_WAREHOUSE"),
            schema=dg.EnvVar("SNOWFLAKE_SCHEMA"),
        ),
        "dbt": get_dbt_resource(),
        "web_scraper": WebScraperResource(),
    }
else:
    resources = {
        "dbt": get_dbt_resource(),
        "web_scraper": WebScraperResource(),
    }
