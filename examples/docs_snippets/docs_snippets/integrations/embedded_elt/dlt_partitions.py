from typing import Iterable, Optional

import dlt
from dagster_embedded_elt.dlt import DagsterDltResource
from dagster_embedded_elt.dlt.computation import ComputationContext
from dagster_embedded_elt.dlt.dlt_computation import RunDlt

from dagster import MaterializeResult, StaticPartitionsDefinition

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


dlt_source = example_dlt_source()
dlt_pipeline = dlt.pipeline(
    pipeline_name="example_pipeline_name",
    dataset_name="example_dataset_name",
    destination="snowflake",
)


class PartitionedRunDlt(RunDlt):
    def stream(self, context: ComputationContext) -> Iterable[MaterializeResult]:
        color = context.partition_key
        yield from DagsterDltResource().stream(
            context=context, dlt_source=example_dlt_source(color=color)
        )


PartitionedRunDlt(
    name="example_dlt_assets",
    dlt_source=dlt_source,
    dlt_pipeline=dlt_pipeline,
    specs=RunDlt.default_specs(dlt_source, dlt_pipeline).replace(
        partitions_def=color_partitions
    ),
)
