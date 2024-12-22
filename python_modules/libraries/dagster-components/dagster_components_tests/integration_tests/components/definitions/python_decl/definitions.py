from dagster import asset


@asset
def an_asset_from_python_decl() -> None: ...
