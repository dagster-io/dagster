import pandas as pd
from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    MetadataValue,
    asset,
)
from dagster_dbt import DbtCliResource, dbt_assets, get_asset_key_for_model

from .resources import (
    ENV,
    HEX_PROJECT_ID,
    GithubResource,
    PyPiResource,
    resource_def,
)

dbt_parse_invocation = resource_def[ENV.upper()]["dbt"].cli(["parse"]).wait()
dbt_manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")


START_DATE = "2023-04-10"


@dbt_assets(manifest=dbt_manifest_path)
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@asset(
    key_prefix=["dagster_pypi"],
    partitions_def=DailyPartitionsDefinition(start_date=START_DATE),
    metadata={"partition_expr": "download_date"},
)
def raw_pypi_downloads(context, pypi: PyPiResource) -> pd.DataFrame:
    df = pypi.get_pypi_download_counts(context.partition_key)
    context.add_output_metadata(
        {
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )
    return df


@asset(
    key_prefix=["dagster_pypi"],
    partitions_def=DailyPartitionsDefinition(start_date=START_DATE),
    metadata={"partition_expr": "date"},
)
def raw_github_stars(context, github: GithubResource) -> pd.DataFrame:
    df = github.get_github_stars(context.partition_key)
    context.add_output_metadata(
        {
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )

    return df


@asset(
    key_prefix=["dagster_pypi"],
    partitions_def=DailyPartitionsDefinition(start_date=START_DATE),
    metadata={"partition_expr": "download_date"},
)
def pypi_downloads(context, raw_pypi_downloads) -> pd.DataFrame:
    df = raw_pypi_downloads
    # Here we could perform some pandas transformations on data
    context.add_output_metadata(
        {
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )
    return df


@asset(
    key_prefix=["dagster_pypi"],
    partitions_def=DailyPartitionsDefinition(start_date=START_DATE),
    metadata={"partition_expr": "date"},
)
def github_stars(context, raw_github_stars) -> pd.DataFrame:
    df = raw_github_stars
    context.add_output_metadata(
        {
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )

    return df


@asset(
    deps=[
        get_asset_key_for_model([dbt_project_assets], "weekly_agg_activity"),
        get_asset_key_for_model([dbt_project_assets], "daily_agg_activity"),
        get_asset_key_for_model([dbt_project_assets], "monthly_agg_activity"),
    ],
    required_resource_keys={"hex"},
)
def hex_notebook(context) -> None:
    if ENV == "PROD":
        context.resources.hex.run_and_poll(project_id=HEX_PROJECT_ID, inputs=[])
    else:
        print("Skipping hex notebook in non-prod environment")
