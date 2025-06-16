import dagster as dg


@dg.asset
def asset_only_in_asset_py_with_component_py() -> None: ...
