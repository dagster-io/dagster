import dagster as dg


# You can attach owners via the `owners` argument on the `@asset` decorator.
@dg.asset(owners=["richard.hendricks@hooli.com", "team:data-eng"])
def my_asset(): ...


# You can also use `owners` with `AssetSpec`
my_external_asset = dg.AssetSpec(
    "my_external_asset", owners=["bighead@hooli.com", "team:roof", "team:corpdev"]
)
