import pytest

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    ExecutionContext,
    Field,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    lambda_solid,
    solid,
    types,
)

from dagster.utils.test import execute_solid
from dagster.core.errors import DagsterExecutionStepExecutionError


def test_single_solid_in_isolation():
    @lambda_solid
    def solid_one():
        return 1

    pipeline_def = PipelineDefinition(solids=[solid_one])

    result = execute_solid(pipeline_def, 'solid_one')
    assert result.success
    assert result.transformed_value() == 1


def test_single_solid_with_single():
    @lambda_solid
    def solid_one():
        return 1

    @lambda_solid(inputs=[InputDefinition(name='num')])
    def add_one_solid(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        solids=[solid_one, add_one_solid],
        dependencies={'add_one_solid': {'num': DependencyDefinition('solid_one')}},
    )

    result = execute_solid(pipeline_def, 'add_one_solid', inputs={'num': 2})
    assert result.success
    assert result.transformed_value() == 3


def test_single_solid_with_multiple_inputs():
    @lambda_solid
    def solid_one():
        return 1

    @lambda_solid(inputs=[InputDefinition(name='num_one'), InputDefinition('num_two')])
    def add_solid(num_one, num_two):
        return num_one + num_two

    pipeline_def = PipelineDefinition(
        solids=[solid_one, add_solid],
        dependencies={
            'add_solid': {
                'num_one': DependencyDefinition('solid_one'),
                'num_two': DependencyDefinition('solid_one'),
            }
        },
    )

    result = execute_solid(
        pipeline_def,
        'add_solid',
        inputs={'num_one': 2, 'num_two': 3},
        environment_dict={'context': {'default': {'config': {'log_level': 'DEBUG'}}}},
    )

    assert result.success
    assert result.transformed_value() == 5


def test_single_solid_with_config():
    ran = {}

    @solid(config_field=Field(Int))
    def check_config_for_two(context):
        assert context.solid_config == 2
        ran['check_config_for_two'] = True

    pipeline_def = PipelineDefinition(solids=[check_config_for_two])
    result = execute_solid(
        pipeline_def,
        'check_config_for_two',
        environment_dict={'solids': {'check_config_for_two': {'config': 2}}},
    )

    assert result.success
    assert ran['check_config_for_two']


def test_single_solid_with_context_config():
    ran = {'check_context_config_for_two': 0}

    @solid
    def check_context_config_for_two(context):
        assert context.resources == 2
        ran['check_context_config_for_two'] += 1

    pipeline_def = PipelineDefinition(
        solids=[check_context_config_for_two],
        context_definitions={
            'test_context': PipelineContextDefinition(
                config_field=Field(Int, is_optional=True, default_value=2),
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.context_config
                ),
            )
        },
    )

    result = execute_solid(
        pipeline_def,
        'check_context_config_for_two',
        environment_dict={'context': {'test_context': {'config': 2}}},
    )

    assert result.success
    assert ran['check_context_config_for_two'] == 1

    result = execute_solid(pipeline_def, 'check_context_config_for_two')

    assert result.success
    assert ran['check_context_config_for_two'] == 2


def test_single_solid_error():
    class SomeError(Exception):
        pass

    @lambda_solid
    def throw_error():
        raise SomeError()

    pipeline_def = PipelineDefinition(solids=[throw_error])

    with pytest.raises(DagsterExecutionStepExecutionError) as e_info:
        execute_solid(pipeline_def, 'throw_error')

    assert isinstance(e_info.value.__cause__, SomeError)


def test_single_solid_type_checking_output_error():
    @lambda_solid(output=OutputDefinition(types.Int))
    def return_string():
        return 'ksjdfkjd'

    pipeline_def = PipelineDefinition(solids=[return_string])

    with pytest.raises(DagsterInvariantViolationError):
        execute_solid(pipeline_def, 'return_string')


def test_failing_solid_execute_solid():
    class ThisException(Exception):
        pass

    @lambda_solid
    def throw_an_error():
        raise ThisException('nope')

    pipeline_def = PipelineDefinition(solids=[throw_an_error])

    with pytest.raises(DagsterExecutionStepExecutionError) as e_info:
        execute_solid(pipeline_def, 'throw_an_error')

    assert isinstance(e_info.value.__cause__, ThisException)
