from dagster import execute_pipeline
from docs_snippets.guides.dagster.reexecution.pipeline.unreliable_pipeline import unreliable_pipeline


def test_pipeline_compiles_and_executes():
    result = execute_pipeline(unreliable_pipeline)
    assert result
