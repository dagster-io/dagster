import os

import pytest
from dagster import Failure, job, op
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.output import GraphOut
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_shell import create_shell_command_op, create_shell_script_op, shell_op


@pytest.mark.parametrize("factory", [create_shell_command_op])
def test_shell_command(factory):
    solid = factory('echo "this is a test message: $MY_ENV_VAR"', name="foobar")

    result = wrap_op_in_graph_and_execute(
        solid,
        run_config={"ops": {"foobar": {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
    )
    assert result.output_value() == "this is a test message: foobar\n"


@pytest.mark.parametrize("factory", [create_shell_command_op])
def test_shell_command_inherits_environment(monkeypatch, factory):
    # OUTSIDE_ENV_VAR represents an environment variable that should be available
    # to jobs. eg. 12-factor app secrets, defined in your Docker container, etc.
    monkeypatch.setenv("OUTSIDE_ENV_VAR", "foo")

    op_def = factory('echo "$OUTSIDE_ENV_VAR:$MY_ENV_VAR"', name="foobar")

    # inherit outside environment variables if none specified for op
    result = wrap_op_in_graph_and_execute(op_def)
    assert result.output_value() == "foo:\n"

    # also inherit outside environment variables if env vars specified for op
    result = wrap_op_in_graph_and_execute(
        op_def,
        run_config={"ops": {"foobar": {"config": {"env": {"MY_ENV_VAR": "bar"}}}}},
    )
    assert result.output_value() == "foo:bar\n"


@pytest.mark.parametrize("shell_defn,name", [(shell_op, "shell_op")])
def test_shell(shell_defn, name):
    result = wrap_op_in_graph_and_execute(
        shell_defn,
        input_values={"shell_command": 'echo "this is a test message: $MY_ENV_VAR"'},
        run_config={"ops": {name: {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
    )
    assert result.output_value() == "this is a test message: foobar\n"


def test_shell_op_inside_job():
    # NOTE: this would be best as a docs example
    @op
    def get_shell_cmd_op():
        return "echo $MY_ENV_VAR"

    @job
    def shell_job():
        shell_op(get_shell_cmd_op())

    result = shell_job.execute_in_process(
        run_config={"ops": {"shell_op": {"config": {"env": {"MY_ENV_VAR": "hello world!"}}}}}
    )
    assert result.output_for_node("shell_op") == "hello world!\n"


@pytest.mark.parametrize("factory", [create_shell_command_op])
def test_shell_command_retcode(factory):
    with pytest.raises(Failure, match="Shell command execution failed"):
        wrap_op_in_graph_and_execute(factory("exit 1", name="exit_op"))


@pytest.mark.parametrize("shell_defn", [shell_op])
def test_shell_op_retcode(shell_defn):
    with pytest.raises(Failure, match="Shell command execution failed"):
        wrap_op_in_graph_and_execute(shell_defn, input_values={"shell_command": "exit 1"})


@pytest.mark.parametrize("factory", [create_shell_command_op])
def test_shell_command_stream_logs(factory):
    op_def = factory('for i in 1 2 3 4 5; do echo "hello ${i}"; done', name="foobar")

    result = wrap_op_in_graph_and_execute(
        op_def,
        run_config={
            "ops": {
                "foobar": {
                    "config": {
                        "output_logging": "STREAM",
                        "env": {"MY_ENV_VAR": "foobar"},
                    }
                }
            }
        },
    )
    assert result.output_value() == "hello 1\nhello 2\nhello 3\nhello 4\nhello 5\n"


@pytest.mark.parametrize("factory", [create_shell_script_op])
def test_shell_script_op(factory):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    op_def = factory(os.path.join(script_dir, "test.sh"), name="foobar")
    result = wrap_op_in_graph_and_execute(
        op_def,
        run_config={"ops": {"foobar": {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
    )
    assert result.output_value() == "this is a test message: foobar\n"


@pytest.mark.parametrize("factory", [create_shell_script_op])
def test_shell_script_op_no_config(factory):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    op_def = factory(os.path.join(script_dir, "test.sh"), name="foobar")
    result = wrap_op_in_graph_and_execute(op_def)
    assert result.output_value() == "this is a test message: \n"


@pytest.mark.parametrize("factory", [create_shell_script_op])
def test_shell_script_op_no_config_composite(factory):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    op_def = factory(os.path.join(script_dir, "test.sh"), name="foobar")

    @graph(
        config=ConfigMapping(
            config_schema={},
            config_fn=lambda cfg: {},
        ),
        out={"result": GraphOut()},
    )
    def graph_def():
        return op_def()

    result = graph_def.execute_in_process()
    assert result.output_value() == "this is a test message: \n"


@pytest.mark.parametrize("factory", [create_shell_command_op])
def test_shell_command_op_overrides(factory):
    op_def = factory(
        'echo "this is a test message: $MY_ENV_VAR"',
        name="foobar",
        description="a description override",
    )

    result = wrap_op_in_graph_and_execute(
        op_def,
        run_config={"ops": {"foobar": {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
    )
    assert result.output_value() == "this is a test message: foobar\n"


@pytest.mark.parametrize("factory", [create_shell_script_op])
def test_shell_script_op_run_time_config(factory, monkeypatch):
    monkeypatch.setattr(os, "environ", {"MY_ENV_VAR": "foobar"})
    script_dir = os.path.dirname(os.path.abspath(__file__))
    op_def = factory(os.path.join(script_dir, "test.sh"), name="foobar")
    result = wrap_op_in_graph_and_execute(op_def)
    assert result.output_value() == "this is a test message: foobar\n"


@pytest.mark.parametrize("factory", [create_shell_script_op])
def test_shell_script_op_run_time_config_composite(factory, monkeypatch):
    monkeypatch.setattr(os, "environ", {"MY_ENV_VAR": "foobar"})
    script_dir = os.path.dirname(os.path.abspath(__file__))
    op_def = factory(os.path.join(script_dir, "test.sh"), name="foobar")

    @graph(
        config=ConfigMapping(
            config_schema={},
            config_fn=lambda cfg: {},
        ),
        out={"result": GraphOut()},
    )
    def my_graph():
        return op_def()

    result = my_graph.execute_in_process()
    assert result.output_value() == "this is a test message: foobar\n"
