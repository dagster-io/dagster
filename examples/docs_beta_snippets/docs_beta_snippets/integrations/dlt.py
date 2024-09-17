import dlt
from dagster_embedded_elt.dlt import DagsterDltResource, dlt_assets
from dlt_sources.github import github_reactions

import dagster as dg


@dlt_assets(
    dlt_source=github_reactions("dagster-io", "dagster"),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="github_issues",
        dataset_name="github",
        destination="snowflake",
    ),
    name="github",
    group_name="github",
)
def github_issues_to_snowflake_assets(
    context: dg.AssetExecutionContext, dlt: DagsterDltResource
):
    yield from dlt.run(context=context)


defs = dg.Definitions(
    assets=[
        github_issues_to_snowflake_assets,
    ],
    resources={
        "dlt": DagsterDltResource(),
    },
)
