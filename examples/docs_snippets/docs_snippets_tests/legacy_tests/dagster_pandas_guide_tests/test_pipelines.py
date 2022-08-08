import pytest

from docs_snippets.legacy.dagster_pandas_guide.core_trip import core_trip
from docs_snippets.legacy.dagster_pandas_guide.custom_column_constraint import (
    custom_column_constraint_trip,
)
from docs_snippets.legacy.dagster_pandas_guide.shape_constrained_trip import (
    shape_constrained_trip,
)
from docs_snippets.legacy.dagster_pandas_guide.summary_stats import summary_stats_trip
from dagster import In, Out, op


@pytest.mark.parametrize(
    "job",
    [
        custom_column_constraint_trip,
        shape_constrained_trip,
        summary_stats_trip,
        core_trip,
    ],
)
def test_guide_pipelines_success(job):
    result = job.execute_in_process()
    assert result.success
