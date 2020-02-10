import os

import pytest
from dagster_bash import bash_command_solid, bash_script_solid

from dagster import Failure, Field, OutputDefinition, composite_solid, execute_solid


def test_bash_command_solid():
    solid = bash_command_solid('echo "this is a test message: $MY_ENV_VAR"', name='foobar')

    result = execute_solid(
        solid,
        environment_dict={'solids': {'foobar': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar\n'}


def test_bash_command_retcode():
    with pytest.raises(Failure) as exc_info:
        execute_solid(bash_command_solid('exit 1'))
    assert 'Bash command failed' in str(exc_info.value)


def test_bash_command_stream_logs():
    solid = bash_command_solid('for i in 1 2 3 4 5; do echo "hello ${i}"; done', name='foobar')

    result = execute_solid(
        solid,
        environment_dict={
            'solids': {
                'foobar': {'config': {'output_logging': 'STREAM', 'env': {'MY_ENV_VAR': 'foobar'}}}
            }
        },
    )
    assert result.output_values == {'result': 'hello 1hello 2hello 3hello 4hello 5'}


def test_bash_script_solid():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = bash_script_solid(os.path.join(script_dir, 'test.sh'), name='foobar')
    result = execute_solid(
        solid,
        environment_dict={'solids': {'foobar': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar\n'}


def test_bash_script_solid_no_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = bash_script_solid(os.path.join(script_dir, 'test.sh'), name='foobar')
    result = execute_solid(solid)
    assert result.output_values == {'result': 'this is a test message: \n'}


def test_bash_script_solid_no_config_composite():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = bash_script_solid(os.path.join(script_dir, 'test.sh'), name='foobar')

    @composite_solid(
        config={}, config_fn=lambda cfg: {}, output_defs=[OutputDefinition(str, 'result')]
    )
    def composite():
        return solid()

    result = execute_solid(composite)
    assert result.output_values == {'result': 'this is a test message: \n'}


def test_bash_command_solid_overrides():
    solid = bash_command_solid(
        'echo "this is a test message: $MY_ENV_VAR"',
        name='foobar',
        description='a description override',
    )

    result = execute_solid(
        solid,
        environment_dict={'solids': {'foobar': {'config': {'env': {'MY_ENV_VAR': 'foobar'}}}}},
    )
    assert result.output_values == {'result': 'this is a test message: foobar\n'}

    with pytest.raises(TypeError) as exc_info:
        bash_command_solid(
            'echo "this is a test message: $MY_ENV_VAR"',
            name='foobar',
            description='a description override',
            output_defs=[OutputDefinition(str, 'bad_output_def')],
        )
    assert 'Overriding output_defs for bash solid is not supported' in str(exc_info.value)

    with pytest.raises(TypeError) as exc_info:
        bash_command_solid(
            'echo "this is a test message: $MY_ENV_VAR"',
            name='foobar',
            description='a description override',
            config={'bad_config': Field(str)},
        )
    assert 'Overriding config for bash solid is not supported' in str(exc_info.value)
