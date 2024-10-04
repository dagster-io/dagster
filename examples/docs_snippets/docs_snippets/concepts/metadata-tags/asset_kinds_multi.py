from dagster import AssetSpec, multi_asset


@multi_asset(
    specs=[
        AssetSpec("foo", kinds={"python", "snowflake"}),
        AssetSpec("bar", kinds={"python", "postgres"}),
    ]
)
def my_multi_asset():
    pass
