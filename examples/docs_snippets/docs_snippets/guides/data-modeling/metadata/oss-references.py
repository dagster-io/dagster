import os
from pathlib import Path

import dagster as dg


@dg.asset
def my_asset(): ...


@dg.asset
def another_asset(): ...


assets = dg.with_source_code_references([my_asset, another_asset])

defs = dg.Definitions(
    # highlight-start
    assets=dg.link_code_references_to_git(
        assets_defs=assets,
        git_url="https://github.com/dagster-io/dagster",
        git_branch="main",
        file_path_mapping=dg.AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="src/repo.py",
        ),
    )
    # Only link to GitHub in production. link locally otherwise
    # highlight-end
    if bool(os.getenv("IS_PRODUCTION"))
    else assets
)
