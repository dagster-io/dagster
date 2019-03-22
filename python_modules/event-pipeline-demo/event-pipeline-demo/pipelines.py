"""Pipeline definitions for the airline_demo."""
import logging

from dagster import (
    DependencyDefinition,
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidInstance,
)

# from .solids import convert_events


def define_event_ingest_pipeline():
    test_context = PipelineContextDefinition(
        context_fn=lambda _: ExecutionContext.console_logging(log_level=logging.DEBUG), resources={}
    )

    local_context = PipelineContextDefinition(
        context_fn=lambda _: ExecutionContext.console_logging(log_level=logging.DEBUG), resources={}
    )

    prod_context = PipelineContextDefinition(
        context_fn=lambda _: ExecutionContext.console_logging(log_level=logging.DEBUG), resources={}
    )

    return PipelineDefinition(
        name='event_ingest_pipeline',
        context_definitions={'test': test_context, 'local': local_context, 'prod': prod_context},
        solids=[],  # [convert_events],
        dependencies=[],
    )

