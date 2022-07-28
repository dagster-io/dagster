from dagster._legacy import AssetGroup

asset_group = AssetGroup.from_package_name(
    "docs_snippets.concepts.assets.package_with_assets"
)
