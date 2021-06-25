from dagster import execute_pipeline
from docs_snippets.concepts.solids_pipelines.pipeline_execution import execute_subset, my_pipeline


def test_execute_my_pipeline():
    result = execute_pipeline(my_pipeline)
    assert result.success


def test_solid_selection():
    execute_subset()
