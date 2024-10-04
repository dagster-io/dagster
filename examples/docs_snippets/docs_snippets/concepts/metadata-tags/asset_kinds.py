from dagster import asset


@asset(kinds={"python", "snowflake"})
def my_stored_in_snowflake_asset(): ...
