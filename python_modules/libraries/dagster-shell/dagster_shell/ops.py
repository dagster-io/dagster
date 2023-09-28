import os
from enum import Enum
from typing import AbstractSet, Any, Dict, Mapping, Optional

from dagster import (
    Config,
    Failure,
    In,
    Nothing,
    OpExecutionContext,
    Out,
    _check as check,
    op,
)
from dagster._core.definitions.op_definition import OpDefinition
from pydantic import Field

from .utils import execute, execute_script_file


class OutputType(Enum):
    STREAM = "STREAM"
    """Stream script stdout/stderr."""

    BUFFER = "BUFFER"
    """Buffer shell script stdout/stderr, then log upon completion."""

    NONE = "NONE"
    """No logging."""


class ShellOpConfig(Config):
    env: Optional[Dict[str, str]] = Field(
        default=None,
        description="An optional dict of environment variables to pass to the subprocess.",
    )
    output_logging: OutputType = Field(
        OutputType.BUFFER.value,
    )
    cwd: Optional[str] = Field(
        default=None, description="Working directory in which to execute shell script"
    )

    def to_execute_params(self) -> Dict[str, Any]:
        return {
            "env": {**os.environ, **(self.env or {})},
            "output_logging": self.output_logging.value,
            "cwd": self.cwd,
        }


@op(
    name="shell_op",
    description=(
        "This op executes a shell command it receives as input.\n\n"
        "This op is suitable for uses where the command to execute is generated dynamically by "
        "upstream ops. If you know the command to execute at job construction time, "
        "consider `shell_command_op` instead."
    ),
    ins={"shell_command": In(str)},
    out=Out(str),
)
def shell_op(context: OpExecutionContext, shell_command: str, config: ShellOpConfig) -> str:
    """This op executes a shell command it receives as input.
    This op is suitable for uses where the command to execute is generated dynamically by
    upstream ops. If you know the command to execute at job construction time,
    consider ``shell_command_op`` instead.

    Args:
        shell_command: The shell command to be executed
        config (ShellOpConfig): A ShellOpConfig object specifying configuration options

    Examples:
        .. code-block:: python

            @op
            def create_shell_command():
                return "echo hello world!"

            @graph
            def echo_graph():
                shell_op(create_shell_command())
    """
    output, return_code = execute(
        shell_command=shell_command, log=context.log, **config.to_execute_params()
    )

    if return_code:
        raise Failure(description=f"Shell command execution failed with output: {output}")

    return output


def create_shell_command_op(
    shell_command: str,
    name: str,
    description: Optional[str] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    tags: Optional[Mapping[str, str]] = None,
) -> OpDefinition:
    """This function is a factory that constructs ops to execute a shell command.

    Note that you can only use ``shell_command_op`` if you know the command you'd like to execute
    at job construction time. If you'd like to construct shell commands dynamically during
    job execution and pass them between ops, you should use ``shell_op`` instead.

    The resulting op can take a single ``start`` argument that is a
    `Nothing dependency <https://docs.dagster.io/concepts/ops-jobs-graphs/graphs#defining-nothing-dependencies>`__
    to allow you to run ops before the shell op.

    Examples:
        .. literalinclude:: ../../../../../../python_modules/libraries/dagster-shell/dagster_shell_tests/example_shell_command_op.py
           :language: python

        .. code-block:: python

            @op
            def run_before_shell_op():
                do_some_work()

            @graph
            def my_graph():
                my_echo_op = create_shell_command_op("echo hello world!", name="echo_op")
                my_echo_op(start=run_before_shell_op())


    Args:
        shell_command (str): The shell command that the constructed op will execute.
        name (str): The name of the constructed op.
        description (Optional[str]): Human-readable description of this op.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by this op.
            Setting this ensures that resource spin up for the required resources will occur before
            the shell command is executed.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for the op. Frameworks may
            expect and require certain metadata to be attached to a op. Users should generally
            not set metadata directly. Values that are not strings will be json encoded and must meet
            the criteria that `json.loads(json.dumps(value)) == value`.

    Raises:
        Failure: Raised when the shell command returns a non-zero exit code.

    Returns:
        OpDefinition: Returns the constructed op definition.
    """

    @op(
        name=name,
        description=description,
        ins={"start": In(Nothing)},
        out=Out(str),
        required_resource_keys=required_resource_keys,
        tags=tags,
    )
    def _shell_fn(context, config: ShellOpConfig):
        output, return_code = execute(
            shell_command=shell_command, log=context.log, **config.to_execute_params()
        )

        if return_code:
            raise Failure(description=f"Shell command execution failed with output: {output}")

        return output

    return _shell_fn


def create_shell_script_op(
    shell_script_path,
    name="create_shell_script_op",
    ins: Optional[Mapping[str, In]] = None,
    **kwargs: Any,
) -> OpDefinition:
    """This function is a factory which constructs an op that will execute a shell command read
    from a script file.

    Any kwargs passed to this function will be passed along to the underlying :func:`@op
    <dagster.op>` decorator. However, note that overriding ``config`` or ``output_defs`` is not
    supported.

    You might consider using :func:`@graph <dagster.graph>` to wrap this op
    in the cases where you'd like to configure the shell op with different config fields.

    If no ``ins`` are passed then the resulting op can take a single ``start`` argument that is a
    `Nothing dependency <https://docs.dagster.io/concepts/ops-jobs-graphs/graphs#defining-nothing-dependencies>`__
    to allow you to run ops before the shell op.


    Examples:
        .. literalinclude:: ../../../../../../python_modules/libraries/dagster-shell/dagster_shell_tests/example_shell_script_op.py
           :language: python

        .. code-block:: python

            @op
            def run_before_shell_op():
                do_some_work()

            @graph
            def my_graph():
                my_echo_op = create_shell_script_op(file_relative_path(__file__, "hello_world.sh"), name="echo_op")
                my_echo_op(start=run_before_shell_op())


    Args:
        shell_script_path (str): The script file to execute.
        name (Optional[str]): The name of this op. Defaults to "create_shell_script_op".
        ins (Optional[Mapping[str, In]]): Ins for the op. Defaults to
            a single Nothing input.

    Raises:
        Failure: Raised when the shell command returns a non-zero exit code.

    Returns:
        OpDefinition: Returns the constructed op definition.
    """
    check.str_param(shell_script_path, "shell_script_path")
    name = check.str_param(name, "name")
    check.opt_mapping_param(ins, "ins", value_type=In)

    if "config" in kwargs:
        raise TypeError("Overriding config for shell op is not supported.")

    @op(
        name=name,
        description=kwargs.pop("description", "An op to invoke a shell command."),
        ins=ins or {"start": In(Nothing)},
        out=Out(str),
        **kwargs,
    )
    def _shell_script_fn(context, config: ShellOpConfig):
        output, return_code = execute_script_file(
            shell_script_path=shell_script_path, log=context.log, **config.to_execute_params()
        )

        if return_code:
            raise Failure(description=f"Shell command execution failed with output: {output}")

        return output

    return _shell_script_fn
