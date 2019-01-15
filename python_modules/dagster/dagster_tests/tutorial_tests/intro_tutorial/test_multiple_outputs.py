# pylint: disable=W0622,W0614,W0401
import pytest


from dagster import DagsterInvariantViolationError, execute_pipeline
from dagster.tutorials.intro_tutorial.multiple_outputs import (
    define_multiple_outputs_step_one_pipeline,
    define_multiple_outputs_step_two_pipeline,
    define_multiple_outputs_step_three_pipeline,
)


def test_intro_tutorial_multiple_outputs_step_one():
    result = execute_pipeline(define_multiple_outputs_step_one_pipeline())

    assert result.success
    assert result.result_for_solid('return_dict_results').transformed_value('out_one') == 23
    assert result.result_for_solid('return_dict_results').transformed_value('out_two') == 45
    assert result.result_for_solid('log_num').transformed_value() == 23
    assert result.result_for_solid('log_num_squared').transformed_value() == 45 * 45


def test_intro_tutorial_multiple_outputs_step_two():
    result = execute_pipeline(define_multiple_outputs_step_two_pipeline())

    assert result.success
    assert result.result_for_solid('yield_outputs').transformed_value('out_one') == 23
    assert result.result_for_solid('yield_outputs').transformed_value('out_two') == 45
    assert result.result_for_solid('log_num').transformed_value() == 23
    assert result.result_for_solid('log_num_squared').transformed_value() == 45 * 45


def test_intro_tutorial_multiple_outputs_step_three():
    result = execute_pipeline(
        define_multiple_outputs_step_three_pipeline(),
        {'solids': {'conditional': {'config': 'out_two'}}},
    )

    # successful things
    assert result.success
    assert result.result_for_solid('conditional').transformed_value('out_two') == 45
    assert result.result_for_solid('log_num_squared').transformed_value() == 45 * 45

    # unsuccessful things
    with pytest.raises(DagsterInvariantViolationError):
        assert result.result_for_solid('conditional').transformed_value('out_one') == 45


if __name__ == '__main__':
    execute_pipeline(
        define_multiple_outputs_step_three_pipeline(),
        {'solids': {'conditional': {'config': 'out_two'}}},
    )

    # execute_pipeline(define_multiple_outputs_step_two())
