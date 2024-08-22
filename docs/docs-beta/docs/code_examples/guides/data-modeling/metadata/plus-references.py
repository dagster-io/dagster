from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud

from dagster import (
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
        # This function also supports customizable path mapping, but usually
        # the defaults are fine.
    )
)