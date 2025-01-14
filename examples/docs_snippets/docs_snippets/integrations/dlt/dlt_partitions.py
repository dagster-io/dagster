from typing import Optional

import dlt
from dagster_dlt import DagsterDltResource, dlt_assets

from dagster import AssetExecutionContext, StaticPartitionsDefinition

color_partitions = StaticPartitionsDefinition(["red", "green", "blue"])


@dlt.source
def example_dlt_source(color: Optional[str] = None):
    def load_colors():
        if color:
            # partition-specific processing
            ...
        else:
            # non-partitioned processing
            ...


@dlt_assets(
    dlt_source=example_dlt_source(),
    name="example_dlt_assets",
    dlt_pipeline=dlt.pipeline(
        pipeline_name="example_pipeline_name",
        dataset_name="example_dataset_name",
        destination="snowflake",
    ),
    partitions_def=color_partitions,
)
def compute(context: AssetExecutionContext, dlt: DagsterDltResource):
    color = context.partition_key
    yield from dlt.run(context=context, dlt_source=example_dlt_source(color=color))
