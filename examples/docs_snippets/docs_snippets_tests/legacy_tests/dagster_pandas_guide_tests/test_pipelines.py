import pytest
from dagster import execute_pipeline
from docs_snippets.legacy.dagster_pandas_guide.core_trip_pipeline import trip_pipeline
from docs_snippets.legacy.dagster_pandas_guide.custom_column_constraint_pipeline import (
    custom_column_constraint_pipeline,
)
from docs_snippets.legacy.dagster_pandas_guide.shape_constrained_pipeline import (
    shape_constrained_pipeline,
)
from docs_snippets.legacy.dagster_pandas_guide.summary_stats_pipeline import summary_stats_pipeline


@pytest.mark.parametrize(
    "pipeline",
    [
        custom_column_constraint_pipeline,
        shape_constrained_pipeline,
        summary_stats_pipeline,
        trip_pipeline,
    ],
)
def test_guide_pipelines_success(pipeline):
    pipeline_result = execute_pipeline(pipeline)
    assert pipeline_result.success
