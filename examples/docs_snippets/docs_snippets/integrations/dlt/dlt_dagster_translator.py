import dlt
from dagster_dlt import DagsterDltResource, DagsterDltTranslator, dlt_assets
from dagster_dlt.translator import DltResourceTranslatorData

from dagster import AssetExecutionContext, AssetKey, AssetSpec


@dlt.source
def example_dlt_source():
    def example_resource(): ...

    return example_resource


class CustomDagsterDltTranslator(DagsterDltTranslator):
    def get_asset_spec(self, data: DltResourceTranslatorData) -> AssetSpec:
        """Overrides asset spec to override asset key to be the dlt resource name."""
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=AssetKey(f"{data.resource.name}"),
        )


@dlt_assets(
    name="example_dlt_assets",
    dlt_source=example_dlt_source(),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="example_pipeline_name",
        dataset_name="example_dataset_name",
        destination="snowflake",
        progress="log",
    ),
    dagster_dlt_translator=CustomDagsterDltTranslator(),
)
def dlt_example_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)
