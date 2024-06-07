import os
from pathlib import Path

from dagster import Definitions, asset
from dagster._core.definitions.metadata import (
    link_to_source_control,
    with_source_code_references,
)


@asset
def my_asset(): ...


@asset
def another_asset(): ...


assets = with_source_code_references([my_asset, another_asset])

defs = Definitions(
    assets=link_to_source_control(
        assets_defs=assets,
        source_control_url="https://github.com/dagster-io/dagster",
        source_control_branch="main",
        repository_root_absolute_path=Path(__file__).parent,
    )
    if bool(os.getenv("IS_PRODUCTION"))
    else assets
)
