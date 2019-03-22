"""Pipeline definitions for the airline_demo."""
import logging

from dagster import (
    DependencyDefinition,
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidInstance,
)

from .solids import define_spark_solid


def define_event_ingest_pipeline():

    event_ingest = define_spark_solid('event_ingest', 'Ingest events from JSON to Parquet')

    return PipelineDefinition(
        name='event_ingest_pipeline',
        # context_definitions={'test': test_context, 'local': local_context, 'prod': prod_context},
        solids=[event_ingest],
        dependencies={},
    )

