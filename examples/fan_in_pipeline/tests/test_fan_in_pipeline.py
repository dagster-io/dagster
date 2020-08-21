from dagster import execute_pipeline

from ..repo import fan_in_pipeline


def test_fan_in_pipeline():
    result = execute_pipeline(fan_in_pipeline)
    assert result.success

    assert result.result_for_solid("sum_fan_in").output_value() == 10
