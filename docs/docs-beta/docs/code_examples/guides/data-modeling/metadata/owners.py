from dagster import asset, AssetSpec

# You can attach owners via the `owners` argument on the `@asset` decorator.
@asset(owners=["richard.hendricks@hooli.com", "team:data-eng"])
def my_asset():
    ...

# You can also use `owners` with `AssetSpec`
my_external_asset = AssetSpec(
    "my_external_asset",
    owners=["bighead@hooli.com", "team:roof", "team:corpdev"]
)
