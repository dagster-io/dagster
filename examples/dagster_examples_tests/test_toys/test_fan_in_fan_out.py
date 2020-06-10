from dagster_examples.toys.fan_in_fan_out import construct_level_pipeline, fan_in_fan_out_pipeline

from dagster import execute_pipeline


def test_fan_in_fan_out_execute():
    assert execute_pipeline(fan_in_fan_out_pipeline).success


def test_low_numbers_pipeline():
    result = execute_pipeline(
        construct_level_pipeline('low_numbers', levels=2, fanout=2),
        run_config={'loggers': {'console': {'config': {'log_level': 'ERROR'}}}},
    )

    assert result.result_for_solid('sum_1').output_value() == 10


def test_high_numbers_pipeline():
    result = execute_pipeline(
        construct_level_pipeline('low_numbers', levels=10, fanout=50),
        run_config={'loggers': {'console': {'config': {'log_level': 'ERROR'}}}},
    )

    assert result.result_for_solid('sum_1').output_value() == 5050
