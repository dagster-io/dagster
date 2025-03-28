import dagster as dg


# You can attach metadata via the `metadata` argument on the `@asset` decorator.
@dg.asset(
    metadata={
        "link_to_docs": dg.MetadataValue.url("https://..."),
        "snippet": dg.MetadataValue.md("# Embedded markdown\n..."),
    }
)
def my_asset(): ...


# You can also use `metadata` with `AssetSpec`
my_external_asset = dg.AssetSpec(
    "my_external_asset",
    metadata={
        "link_to_docs": dg.MetadataValue.url("https://..."),
        "snippet": dg.MetadataValue.md("# Embedded markdown\n..."),
    },
)
