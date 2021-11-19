import os

import pytest
from dagster import Failure, OutputDefinition, composite_solid, execute_solid
from dagster_shell import (
    create_shell_command_op,
    create_shell_command_solid,
    create_shell_script_op,
    create_shell_script_solid,
    shell_op,
    shell_solid,
)


@pytest.mark.parametrize("factory", [create_shell_command_solid, create_shell_command_op])
def test_shell_command(factory):
    solid = factory('echo "this is a test message: $MY_ENV_VAR"', name="foobar")

    result = execute_solid(
        solid,
        run_config={"solids": {"foobar": {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
    )
    assert result.output_values == {"result": "this is a test message: foobar\n"}


@pytest.mark.parametrize("shell_defn,name", [(shell_op, "shell_op"), (shell_solid, "shell_solid")])
def test_shell(shell_defn, name):

    result = execute_solid(
        shell_defn,
        input_values={"shell_command": 'echo "this is a test message: $MY_ENV_VAR"'},
        run_config={"solids": {name: {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
    )
    assert result.output_values == {"result": "this is a test message: foobar\n"}


@pytest.mark.parametrize("factory", [create_shell_command_op, create_shell_command_solid])
def test_shell_command_retcode(factory):
    with pytest.raises(Failure, match="Shell command execution failed"):
        execute_solid(factory("exit 1", name="exit_solid"))


@pytest.mark.parametrize("shell_defn", [shell_op, shell_solid])
def test_shell_solid_retcode(shell_defn):
    with pytest.raises(Failure, match="Shell command execution failed"):
        execute_solid(shell_defn, input_values={"shell_command": "exit 1"})


@pytest.mark.parametrize("factory", [create_shell_command_op, create_shell_command_solid])
def test_shell_command_stream_logs(factory):
    solid = factory('for i in 1 2 3 4 5; do echo "hello ${i}"; done', name="foobar")

    result = execute_solid(
        solid,
        run_config={
            "solids": {
                "foobar": {"config": {"output_logging": "STREAM", "env": {"MY_ENV_VAR": "foobar"}}}
            }
        },
    )
    assert result.output_values == {"result": "hello 1\nhello 2\nhello 3\nhello 4\nhello 5\n"}


@pytest.mark.parametrize("factory", [create_shell_script_op, create_shell_script_solid])
def test_shell_script_solid(factory):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = factory(os.path.join(script_dir, "test.sh"), name="foobar")
    result = execute_solid(
        solid,
        run_config={"solids": {"foobar": {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
    )
    assert result.output_values == {"result": "this is a test message: foobar\n"}


@pytest.mark.parametrize("factory", [create_shell_script_op, create_shell_script_solid])
def test_shell_script_solid_no_config(factory):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = factory(os.path.join(script_dir, "test.sh"), name="foobar")
    result = execute_solid(solid)
    assert result.output_values == {"result": "this is a test message: \n"}


@pytest.mark.parametrize("factory", [create_shell_script_op, create_shell_script_solid])
def test_shell_script_solid_no_config_composite(factory):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = factory(os.path.join(script_dir, "test.sh"), name="foobar")

    @composite_solid(
        config_schema={}, config_fn=lambda cfg: {}, output_defs=[OutputDefinition(str, "result")]
    )
    def composite():
        return solid()

    result = execute_solid(composite)
    assert result.output_values == {"result": "this is a test message: \n"}


@pytest.mark.parametrize("factory", [create_shell_command_op, create_shell_command_solid])
def test_shell_command_solid_overrides(factory):
    solid = factory(
        'echo "this is a test message: $MY_ENV_VAR"',
        name="foobar",
        description="a description override",
    )

    result = execute_solid(
        solid,
        run_config={"solids": {"foobar": {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
    )
    assert result.output_values == {"result": "this is a test message: foobar\n"}


@pytest.mark.parametrize("factory", [create_shell_script_op, create_shell_script_solid])
def test_shell_script_solid_run_time_config(factory, monkeypatch):
    monkeypatch.setattr(os, "environ", {"MY_ENV_VAR": "foobar"})
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = factory(os.path.join(script_dir, "test.sh"), name="foobar")
    result = execute_solid(solid)
    assert result.output_values == {"result": "this is a test message: foobar\n"}


@pytest.mark.parametrize("factory", [create_shell_script_op, create_shell_script_solid])
def test_shell_script_solid_run_time_config_composite(factory, monkeypatch):
    monkeypatch.setattr(os, "environ", {"MY_ENV_VAR": "foobar"})
    script_dir = os.path.dirname(os.path.abspath(__file__))
    solid = factory(os.path.join(script_dir, "test.sh"), name="foobar")

    @composite_solid(
        config_schema={}, config_fn=lambda cfg: {}, output_defs=[OutputDefinition(str, "result")]
    )
    def composite():
        return solid()

    result = execute_solid(composite)
    assert result.output_values == {"result": "this is a test message: foobar\n"}
