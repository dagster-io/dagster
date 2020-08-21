import pytest

from dagster import execute_pipeline, seven

from ..step_two import compute_top_quartile_pipeline_step_two


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_step_two():
    pipeline_result = execute_pipeline(compute_top_quartile_pipeline_step_two)
    assert pipeline_result.success


# k
# snapshot.assert_match(pipeline_result.output_for_solid('sugariest_cereals').to_dict())
