import dlt
from dagster_dlt import DagsterDltResource, dlt_assets

from dagster import AssetExecutionContext, AssetSpec


@dlt.source
def example_dlt_source():
    def example_resource(): ...

    return example_resource


@dlt_assets(
    dlt_source=example_dlt_source(),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="example_pipeline_name",
        dataset_name="example_dataset_name",
        destination="snowflake",
        progress="log",
    ),
)
def example_dlt_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


thinkific_source_assets = [
    AssetSpec(key, group_name="thinkific") for key in example_dlt_assets.dependency_keys
]
