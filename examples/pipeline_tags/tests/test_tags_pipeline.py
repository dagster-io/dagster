from dagster import execute_pipeline

from ..repo import tags_pipeline


def test_fan_in_pipeline():
    result = execute_pipeline(tags_pipeline)
    assert result.success

    assert result.result_for_solid("get_tag").output_value() == "ml_team"
