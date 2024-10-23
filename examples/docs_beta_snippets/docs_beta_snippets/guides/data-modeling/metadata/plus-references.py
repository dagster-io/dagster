from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud

import dagster as dg


@dg.asset
def my_asset(): ...


@dg.asset
def another_asset(): ...


defs = dg.Definitions(
    # highlight-start
    assets=link_code_references_to_git_if_cloud(
        assets_defs=dg.with_source_code_references([my_asset, another_asset]),
        # This function also supports customizable path mapping, but usually
        # the defaults are fine.
    )
    # highlight-end
)
