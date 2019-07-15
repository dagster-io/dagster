import pytest

from dagster import (
    DagsterTypeCheckError,
    Field,
    InputDefinition,
    Int,
    OutputDefinition,
    ModeDefinition,
    lambda_solid,
    resource,
    solid,
)

from dagster.utils.test import execute_solid
from dagster.core.errors import DagsterExecutionStepExecutionError


def test_single_solid_in_isolation():
    @lambda_solid
    def solid_one():
        return 1

    result = execute_solid(solid_one)
    assert result.success
    assert result.output_value() == 1


def test_single_solid_with_single():
    @lambda_solid(input_defs=[InputDefinition(name='num')])
    def add_one_solid(num):
        return num + 1

    result = execute_solid(add_one_solid, input_values={'num': 2})

    assert result.success
    assert result.output_value() == 3


def test_single_solid_with_multiple_inputs():
    @lambda_solid(input_defs=[InputDefinition(name='num_one'), InputDefinition('num_two')])
    def add_solid(num_one, num_two):
        return num_one + num_two

    result = execute_solid(
        add_solid,
        input_values={'num_one': 2, 'num_two': 3},
        environment_dict={'loggers': {'console': {'config': {'log_level': 'DEBUG'}}}},
    )

    assert result.success
    assert result.output_value() == 5


def test_single_solid_with_config():
    ran = {}

    @solid(config_field=Field(Int))
    def check_config_for_two(context):
        assert context.solid_config == 2
        ran['check_config_for_two'] = True

    result = execute_solid(
        check_config_for_two, environment_dict={'solids': {'check_config_for_two': {'config': 2}}}
    )

    assert result.success
    assert ran['check_config_for_two']


def test_single_solid_with_context_config():
    @resource(config_field=Field(Int, is_optional=True, default_value=2))
    def num_resource(init_context):
        return init_context.resource_config

    ran = {'count': 0}

    @solid
    def check_context_config_for_two(context):
        assert context.resources.num == 2
        ran['count'] += 1

    result = execute_solid(
        check_context_config_for_two,
        environment_dict={'resources': {'num': {'config': 2}}},
        mode_def=ModeDefinition(resource_defs={'num': num_resource}),
    )

    assert result.success
    assert ran['count'] == 1

    result = execute_solid(
        check_context_config_for_two, mode_def=ModeDefinition(resource_defs={'num': num_resource})
    )

    assert result.success
    assert ran['count'] == 2


def test_single_solid_error():
    class SomeError(Exception):
        pass

    @lambda_solid
    def throw_error():
        raise SomeError()

    with pytest.raises(DagsterExecutionStepExecutionError) as e_info:
        execute_solid(throw_error)

    assert isinstance(e_info.value.__cause__, SomeError)


def test_single_solid_type_checking_output_error():
    @lambda_solid(output_def=OutputDefinition(Int))
    def return_string():
        return 'ksjdfkjd'

    with pytest.raises(DagsterTypeCheckError):
        execute_solid(return_string)


def test_failing_solid_in_isolation():
    class ThisException(Exception):
        pass

    @lambda_solid
    def throw_an_error():
        raise ThisException('nope')

    with pytest.raises(DagsterExecutionStepExecutionError) as e_info:
        execute_solid(throw_an_error)

    assert isinstance(e_info.value.__cause__, ThisException)
