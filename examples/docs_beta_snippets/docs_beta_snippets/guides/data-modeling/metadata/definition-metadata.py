from dagster import asset, AssetSpec, MetadataValue

# You can attach metadata via the `metadata` argument on the `@asset` decorator.
@asset(metadata={
    "link_to_docs": MetadataValue.url("https://..."),
    "snippet": MetadataValue.md("# Embedded markdown\n...")
})
def my_asset():
    ...

# You can also use `metadata` with `AssetSpec`
my_external_asset = AssetSpec(
    "my_external_asset",
    metadata={
        "link_to_docs": MetadataValue.url("https://..."),
        "snippet": MetadataValue.md("# Embedded markdown\n...")
    }
)
