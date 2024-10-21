from dagster import asset


@asset(kinds={"python", "snowflake"})
def my_asset():
    pass
