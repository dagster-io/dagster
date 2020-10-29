from dagster import execute_pipeline

from ..fan_in_fan_out import fan_in_fan_out_pipeline


def test_fan_in_fan_out_pipeline():
    assert execute_pipeline(fan_in_fan_out_pipeline).success
