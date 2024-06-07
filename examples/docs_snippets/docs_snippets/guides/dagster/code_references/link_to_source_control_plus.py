import os
from pathlib import Path

from dagster_cloud.metadata.source_code import link_to_git_if_cloud

from dagster import Definitions, asset
from dagster._core.definitions.metadata import with_source_code_references


@asset
def my_asset(): ...


@asset
def another_asset(): ...


defs = Definitions(
    assets=link_to_git_if_cloud(
        assets_defs=with_source_code_references([my_asset, another_asset]),
        # Inferred from searching for .git directory in parent directories
        # of the module containing this code - may also be set explicitly
        repository_root_absolute_path=Path(__file__).parent,
    )
)
