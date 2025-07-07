import dagster as dg


@dg.asset
def asset_in_submodule() -> None: ...
