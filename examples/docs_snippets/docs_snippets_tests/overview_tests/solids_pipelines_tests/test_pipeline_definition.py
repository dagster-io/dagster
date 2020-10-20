from dagster import execute_pipeline
from docs_snippets.overview.solids_pipelines.pipeline_definition import one_plus_one_pipeline


def test_one_plus_one_pipeline():
    result = execute_pipeline(one_plus_one_pipeline)
    assert result
