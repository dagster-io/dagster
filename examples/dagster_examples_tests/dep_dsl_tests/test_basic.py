from dagster import execute_pipeline
from dagster_examples.dep_dsl.pipeline import define_dep_dsl_pipeline


def test_basic_dep_dsl():
    result = execute_pipeline(
        define_dep_dsl_pipeline(),
        environment_dict={'solids': {'A': {'inputs': {'num': {'value': 2}}}}},
    )

    assert result.success
    assert result.result_for_solid('add').output_value() == 9
