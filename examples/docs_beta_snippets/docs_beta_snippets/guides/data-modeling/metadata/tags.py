from dagster import AssetSpec, asset


# You can attach tags via the `tags` argument on the `@asset` decorator.
@asset(tags={"domain": "marketing", "pii": "true"})
def my_asset(): ...


# You can also use `tags` with `AssetSpec`
my_external_asset = AssetSpec(
    "my_external_asset", tags={"domain": "legal", "sensitive": ""}
)
