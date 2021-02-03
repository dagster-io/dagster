from dagster import execute_pipeline

from ..repo import define_dep_dsl_pipeline


def test_basic_dep_dsl():
    result = execute_pipeline(
        define_dep_dsl_pipeline(),
        run_config={"solids": {"A": {"inputs": {"num": {"value": 2}}}}},
    )

    assert result.success
    assert result.result_for_solid("subtract").output_value() == 9
