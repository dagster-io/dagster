from dagster import asset, AssetSpec

# You can attach kinds via the `kinds` argument on the `@asset` decorator.
@asset(kinds=["snowflake", "dbt"])
def my_asset():
    ...

# You can also use `kinds` with `AssetSpec`
my_external_asset = AssetSpec(
    "my_external_asset",
    kinds=["snowflake", "dbt"]
)
