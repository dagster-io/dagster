from docs_snippets_crag.concepts.configuration.configurable_solid import config_example_pipeline
from docs_snippets_crag.concepts.configuration.configurable_solid_with_schema import (
    configurable_pipeline_with_schema,
)


def execute_with_config():
    # start_execute_with_config
    from dagster import execute_pipeline

    execute_pipeline(
        config_example_pipeline,
        run_config={"solids": {"config_example_solid": {"config": {"iterations": 1}}}},
    )
    # end_execute_with_config


def execute_with_bad_config():
    # start_execute_with_bad_config
    from dagster import execute_pipeline

    execute_pipeline(
        configurable_pipeline_with_schema,
        run_config={
            "solids": {
                "configurable_solid_with_schema": {"config": {"nonexistent_config_value": 1}}
            }
        },
    )

    # end_execute_with_bad_config
