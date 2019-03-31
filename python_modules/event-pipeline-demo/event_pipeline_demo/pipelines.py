"""Pipeline definitions for the airline_demo."""

import logging

from dagster import ExecutionContext, PipelineContextDefinition, List, Path, PipelineDefinition
from dagster_framework.spark import SparkSolidDefinition
from dagster_framework.snowflake import SnowflakeSolidDefinition

from .resources import s3_download_manager


def define_event_ingest_pipeline():
    local_context = PipelineContextDefinition(
        context_fn=lambda _: ExecutionContext.console_logging(log_level=logging.DEBUG),
        resources={'download_manager': s3_download_manager},
    )

    # download_from_s3 = download_from_s3()

    event_ingest = SparkSolidDefinition('event_ingest', 'Ingest events from JSON to Parquet')

    snowflake_query = SnowflakeSolidDefinition('hello_world_snowflake', ['select 1;', 'select 2;'])

    return PipelineDefinition(
        name='event_ingest_pipeline', solids=[snowflake_query], dependencies={}
    )
