from dagster import AssetKey


def dagster_name_fn(table_id: str) -> str:
    return table_id.replace(".", "_").replace("-", "_").replace("*", "_star")


def default_asset_key_fn(fqn: str) -> AssetKey:
    """Get the asset key for an sdf asset. An Sdf asset's key is its fully qualified name."""
    return AssetKey(fqn.split("."))
