import os
from pathlib import Path

from dagster_cloud.metadata.source_code import (  # type: ignore
    link_code_references_to_git_if_cloud,
)

from dagster import (
    AnchorBasedFilePathMapping,
    Definitions,
    asset,
    with_source_code_references,
)


@asset
def my_asset(): ...


@asset
def another_asset(): ...


defs = Definitions(
    assets=link_code_references_to_git_if_cloud(
        assets_defs=with_source_code_references([my_asset, another_asset]),
        # Inferred from searching for .git directory in parent directories
        # of the module containing this code - may also be set explicitly
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="src/repo.py",
        ),
    )
)
