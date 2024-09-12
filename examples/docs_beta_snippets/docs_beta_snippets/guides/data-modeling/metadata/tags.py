import dagster as dg


# You can attach tags via the `tags` argument on the `@asset` decorator.
@dg.asset(tags={"domain": "marketing", "pii": "true"})
def my_asset(): ...


# You can also use `tags` with `AssetSpec`
my_external_asset = dg.AssetSpec(
    "my_external_asset", tags={"domain": "legal", "sensitive": ""}
)
