from collections.abc import Iterable

import dlt
from dagster_dlt import DagsterDltResource, DagsterDltTranslator, dlt_assets
from dlt.extract.resource import DltResource

from dagster import AssetExecutionContext, AssetKey


@dlt.source
def example_dlt_source():
    def example_resource(): ...

    return example_resource


class CustomDagsterDltTranslator(DagsterDltTranslator):
    def get_asset_key(self, resource: DltResource) -> AssetKey:
        """Overrides asset key to be the dlt resource name."""
        return AssetKey(f"{resource.name}")

    def get_deps_asset_keys(self, resource: DltResource) -> Iterable[AssetKey]:
        """Overrides upstream asset key to be a single source asset."""
        return [AssetKey("common_upstream_dlt_dependency")]


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
