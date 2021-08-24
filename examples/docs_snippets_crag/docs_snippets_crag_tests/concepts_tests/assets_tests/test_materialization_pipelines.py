from dagster import execute_pipeline
from docs_snippets_crag.concepts.assets.materialization_pipelines import my_user_model_pipeline


def test_pipelines_compile_and_execute():
    pipelines = [my_user_model_pipeline]
    for pipeline in pipelines:
        result = execute_pipeline(pipeline)
        assert result
        assert result.success
