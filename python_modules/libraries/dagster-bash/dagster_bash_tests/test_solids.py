import os

import pytest
from dagster_bash import bash_solid, create_bash_command_solid, create_bash_script_solid

from dagster import Failure, OutputDefinition, composite_solid, execute_solid


def test_bash_command_solid():
    solid = create_bash_command_solid('echo "this is a test message: $MY_ENV_VAR"', name='foobar')

    result = execute_solid(
        solid,
        environment_dict={'solids': {'foobar': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar\n'}


def test_bash_solid():

    result = execute_solid(
        bash_solid,
        input_values={'bash_command': 'echo "this is a test message: $MY_ENV_VAR"'},
        environment_dict={'solids': {'bash_solid': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar\n'}


def test_bash_command_retcode():
    with pytest.raises(Failure, match='Bash command execution failed'):
        execute_solid(create_bash_command_solid('exit 1', name='exit_solid'))


def test_bash_solid_retcode():
    with pytest.raises(Failure, match='Bash command execution failed'):
        execute_solid(bash_solid, input_values={'bash_command': 'exit 1'})


def test_bash_command_stream_logs():
    solid = create_bash_command_solid(
        'for i in 1 2 3 4 5; do echo "hello ${i}"; done', name='foobar'
    )

    result = execute_solid(
        solid,
        environment_dict={
            'solids': {
                'foobar': {'config': {'output_logging': 'STREAM', 'env': {'MY_ENV_VAR': 'foobar'}}}
            }
        },
    )
    assert result.output_values == {'result': 'hello 1\nhello 2\nhello 3\nhello 4\nhello 5\n'}


def test_bash_script_solid():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = create_bash_script_solid(os.path.join(script_dir, 'test.sh'), name='foobar')
    result = execute_solid(
        solid,
        environment_dict={'solids': {'foobar': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar\n'}


def test_bash_script_solid_no_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = create_bash_script_solid(os.path.join(script_dir, 'test.sh'), name='foobar')
    result = execute_solid(solid)
    assert result.output_values == {'result': 'this is a test message: \n'}


def test_bash_script_solid_no_config_composite():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = create_bash_script_solid(os.path.join(script_dir, 'test.sh'), name='foobar')

    @composite_solid(
        config={}, config_fn=lambda cfg: {}, output_defs=[OutputDefinition(str, 'result')]
    )
    def composite():
        return solid()

    result = execute_solid(composite)
    assert result.output_values == {'result': 'this is a test message: \n'}


def test_bash_command_solid_overrides():
    solid = create_bash_command_solid(
        'echo "this is a test message: $MY_ENV_VAR"',
        name='foobar',
        description='a description override',
    )

    result = execute_solid(
        solid,
        environment_dict={'solids': {'foobar': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar\n'}
