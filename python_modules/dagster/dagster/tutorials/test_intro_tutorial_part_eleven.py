# pylint: disable=W0622,W0614,W0401
import pytest

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    Field,
    InputDefinition,
    MultipleResults,
    OutputDefinition,
    PipelineDefinition,
    Result,
    execute_pipeline,
    solid,
    String,
    Int,
)


@solid(
    outputs=[
        OutputDefinition(dagster_type=Int, name='out_one'),
        OutputDefinition(dagster_type=Int, name='out_two'),
    ]
)
def yield_outputs(_info):
    yield Result(23, 'out_one')
    yield Result(45, 'out_two')


@solid(
    outputs=[
        OutputDefinition(dagster_type=Int, name='out_one'),
        OutputDefinition(dagster_type=Int, name='out_two'),
    ]
)
def return_dict_results(_info):
    return MultipleResults.from_dict({'out_one': 23, 'out_two': 45})


@solid(
    config_field=Field(
        String, description='Should be either out_one or out_two'
    ),
    outputs=[
        OutputDefinition(dagster_type=Int, name='out_one'),
        OutputDefinition(dagster_type=Int, name='out_two'),
    ],
)
def conditional(info):
    if info.config == 'out_one':
        yield Result(23, 'out_one')
    elif info.config == 'out_two':
        yield Result(45, 'out_two')
    else:
        raise Exception('invalid config')


@solid(inputs=[InputDefinition('num', dagster_type=Int)])
def log_num(info, num):
    info.context.info('num {num}'.format(num=num))
    return num


@solid(inputs=[InputDefinition('num', dagster_type=Int)])
def log_num_squared(info, num):
    info.context.info(
        'num_squared {num_squared}'.format(num_squared=num * num)
    )
    return num * num


def define_part_eleven_step_one_pipeline():
    return PipelineDefinition(
        name='part_eleven_step_one_pipeline',
        solids=[return_dict_results, log_num, log_num_squared],
        dependencies={
            'log_num': {
                'num': DependencyDefinition('return_dict_results', 'out_one')
            },
            'log_num_squared': {
                'num': DependencyDefinition('return_dict_results', 'out_two')
            },
        },
    )


def define_part_eleven_step_two_pipeline():
    return PipelineDefinition(
        name='part_eleven_step_two_pipeline',
        solids=[yield_outputs, log_num, log_num_squared],
        dependencies={
            'log_num': {
                'num': DependencyDefinition('yield_outputs', 'out_one')
            },
            'log_num_squared': {
                'num': DependencyDefinition('yield_outputs', 'out_two')
            },
        },
    )


def define_part_eleven_step_three_pipeline():
    return PipelineDefinition(
        name='part_eleven_step_three_pipeline',
        solids=[conditional, log_num, log_num_squared],
        dependencies={
            'log_num': {'num': DependencyDefinition('conditional', 'out_one')},
            'log_num_squared': {
                'num': DependencyDefinition('conditional', 'out_two')
            },
        },
    )


def test_intro_tutorial_part_eleven_step_one():
    result = execute_pipeline(define_part_eleven_step_one_pipeline())

    assert result.success
    assert (
        result.result_for_solid('return_dict_results').transformed_value(
            'out_one'
        )
        == 23
    )
    assert (
        result.result_for_solid('return_dict_results').transformed_value(
            'out_two'
        )
        == 45
    )
    assert result.result_for_solid('log_num').transformed_value() == 23
    assert (
        result.result_for_solid('log_num_squared').transformed_value()
        == 45 * 45
    )


def test_intro_tutorial_part_eleven_step_two():
    result = execute_pipeline(define_part_eleven_step_two_pipeline())

    assert result.success
    assert (
        result.result_for_solid('yield_outputs').transformed_value('out_one')
        == 23
    )
    assert (
        result.result_for_solid('yield_outputs').transformed_value('out_two')
        == 45
    )
    assert result.result_for_solid('log_num').transformed_value() == 23
    assert (
        result.result_for_solid('log_num_squared').transformed_value()
        == 45 * 45
    )


def test_intro_tutorial_part_eleven_step_three():
    result = execute_pipeline(
        define_part_eleven_step_three_pipeline(),
        {'solids': {'conditional': {'config': 'out_two'}}},
    )

    # successful things
    assert result.success
    assert (
        result.result_for_solid('conditional').transformed_value('out_two')
        == 45
    )
    assert (
        result.result_for_solid('log_num_squared').transformed_value()
        == 45 * 45
    )

    # unsuccessful things
    with pytest.raises(DagsterInvariantViolationError):
        assert (
            result.result_for_solid('conditional').transformed_value('out_one')
            == 45
        )


if __name__ == '__main__':
    execute_pipeline(
        define_part_eleven_step_three_pipeline(),
        {'solids': {'conditional': {'config': 'out_two'}}},
    )

    # execute_pipeline(define_part_eleven_step_two())
