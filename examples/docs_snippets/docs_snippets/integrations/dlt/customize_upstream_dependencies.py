import dlt
from dagster_dlt import DagsterDltTranslator, build_dlt_asset_specs
from dagster_dlt.translator import DltResourceTranslatorData

from dagster import AssetKey, AssetSpec


# start_upstream_asset
@dlt.source
def example_dlt_source():
    def example_resource(): ...

    return example_resource


class CustomDagsterDltTranslator(DagsterDltTranslator):
    def get_asset_spec(self, data: DltResourceTranslatorData) -> AssetSpec:
        """Overrides asset spec to override upstream asset key to be a single source asset."""
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(data)
        # We set an upstream dependency for our assets
        return default_spec.replace_attributes(
            deps=[AssetKey("common_upstream_dlt_dependency")],
        )


dlt_specs = build_dlt_asset_specs(
    dlt_source=example_dlt_source(),
    dlt_pipeline=dlt.pipeline(
        pipeline_name="example_pipeline_name",
        dataset_name="example_dataset_name",
        destination="snowflake",
        progress="log",
    ),
    dagster_dlt_translator=CustomDagsterDltTranslator(),
)
# end_upstream_asset
