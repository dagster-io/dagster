"""Pipeline definitions for the airline_demo."""

from dagster import InputDefinition, OutputDefinition, List, Path, PipelineDefinition

from .solids import define_spark_solid


def define_event_ingest_pipeline():

    event_ingest = define_spark_solid(
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

    return PipelineDefinition(name='event_ingest_pipeline', solids=[event_ingest], dependencies={})
