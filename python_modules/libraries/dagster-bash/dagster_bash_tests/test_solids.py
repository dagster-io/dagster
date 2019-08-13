import os

import pytest

from dagster import DagsterExecutionStepExecutionError, execute_solid

from dagster_bash import bash_command_solid, bash_script_solid


def test_bash_command_solid():
    solid = bash_command_solid('echo "this is a test message: $MY_ENV_VAR"', name='foobar')

    result = execute_solid(
        solid,
        environment_dict={'solids': {'foobar': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar'}


def test_bash_command_retcode():
    with pytest.raises(DagsterExecutionStepExecutionError) as exc_info:
        execute_solid(bash_command_solid('exit 1'))

    assert 'step key: "bash_solid.compute"' in str(exc_info.value)
    assert 'solid invocation: "bash_solid"' in str(exc_info.value)
    assert 'solid definition: "bash_solid"' in str(exc_info.value)


def test_bash_command_buffer_logs():
    solid = bash_command_solid('for i in 1 2 3 4 5; do echo "hello ${i}"; done', name='foobar')

    result = execute_solid(
        solid,
        environment_dict={
            'solids': {
                'foobar': {'config': {'output_logging': 'BUFFER', 'env': {'MY_ENV_VAR': 'foobar'}}}
            }
        },
    )
    assert result.output_values == {'result': 'hello 1\nhello 2\nhello 3\nhello 4\nhello 5\n'}


def test_bash_script_solid():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = bash_script_solid(os.path.join(script_dir, 'test.sh'), name='foobar')
    result = execute_solid(
        solid,
        environment_dict={'solids': {'foobar': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar'}
