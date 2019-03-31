"""Pipeline definitions for the airline_demo."""

from dagster import InputDefinition, OutputDefinition, List, Path, PipelineDefinition
from dagster_solids.spark import SparkSolidDefinition
from dagster_solids.snowflake import SnowflakeSolidDefinition


def define_event_ingest_pipeline():

    event_ingest = SparkSolidDefinition(
        'event_ingest',
        [
            InputDefinition(
                name='spark_inputs',
                dagster_type=List(Path),
                description='The Spark job input paths',
            )
        ],
        [
            OutputDefinition(
                name='spark_outputs',
                dagster_type=List(Path),
                description='The Spark job output paths',
            )
        ],
        'Ingest events from JSON to Parquet',
    )

    snowflake_query = SnowflakeSolidDefinition('hello_world_snowflake')

    return PipelineDefinition(
        name='event_ingest_pipeline', solids=[snowflake_query], dependencies={}
    )
