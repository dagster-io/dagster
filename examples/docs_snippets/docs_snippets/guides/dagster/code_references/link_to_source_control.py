from pathlib import Path

from dagster import (
    AnchorBasedFilePathMapping,
    Definitions,
    asset,
    link_code_references_to_git,
    with_source_code_references,
)


@asset
def my_asset(): ...


@asset
def another_asset(): ...


defs = Definitions(
    assets=link_code_references_to_git(
        assets_defs=with_source_code_references([my_asset, another_asset]),
        git_url="https://github.com/dagster-io/dagster",
        git_branch="main",
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="src/repo.py",
        ),
    )
)
