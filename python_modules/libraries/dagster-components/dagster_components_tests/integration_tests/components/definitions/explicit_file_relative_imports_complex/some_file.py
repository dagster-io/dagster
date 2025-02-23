from dagster import asset

from .submodule import asset_in_submodule as asset_in_submodule  # noqa: TID252


@asset
def asset_in_some_file() -> None: ...
