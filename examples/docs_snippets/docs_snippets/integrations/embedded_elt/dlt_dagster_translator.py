import dlt
from dagster_embedded_elt.dlt.dlt_computation import RunDlt


@dlt.source
def example_dlt_source():
    def example_resource(): ...

    return example_resource


dlt_source = example_dlt_source()
dlt_pipeline = dlt.pipeline(
    pipeline_name="example_pipeline_name",
    dataset_name="example_dataset_name",
    destination="snowflake",
    progress="log",
)
source_asset_key = "common_upstream_dlt_dependency"
RunDlt(
    name="example_dlt_assets",
    dlt_source=dlt_source,
    dlt_pipeline=dlt_pipeline,
    specs=[
        RunDlt.default_spec(dlt_source, dlt_pipeline, dlt_resource)._replace(
            key=dlt_resource.name,  # overrides asset key to be resource name
            deps=[source_asset_key],  # overrides upstream to be single source asset
        )
        for dlt_resource in dlt_source.resources.values()
    ],
)
