import dlt
from dagster_dlt import DagsterDltResource, DagsterDltTranslator, dlt_assets
from dagster_dlt.translator import DltResourceTranslatorData

from dagster import AssetExecutionContext, asset


@dlt.source
def example_dlt_source():
    def example_resource(): ...

    return example_resource


example_dlt_pipeline = dlt.pipeline(
    pipeline_name="example_pipeline_name",
    dataset_name="example_dataset_name",
    destination="snowflake",
    progress="log",
)


@dlt_assets(
    dlt_source=example_dlt_source(),
    dlt_pipeline=example_dlt_pipeline,
)
def example_dlt_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)


example_dlt_resource_asset_key = next(
    iter(
        [
            DagsterDltTranslator().get_asset_spec(
                data=DltResourceTranslatorData(
                    resource=dlt_source_resource,
                    pipeline=example_dlt_pipeline,
                )
            )
            for dlt_source_resource in example_dlt_source().selected_resources.values()
            if dlt_source_resource.name == "example_resource"
        ]
    )
)


@asset(deps=[example_dlt_resource_asset_key])
def example_downstream_asset(): ...
