import os

from dagster import Enum, EnumValue, Failure, Field, In, Noneable, Nothing, Out, Permissive
from dagster import _check as check
from dagster import op

from .utils import execute, execute_script_file


def shell_op_config():
    return {
        "env": Field(
            Noneable(Permissive()),
            is_required=False,
            description="An optional dict of environment variables to pass to the subprocess.",
        ),
        "output_logging": Field(
            Enum(
                name="OutputType",
                enum_values=[
                    EnumValue("STREAM", description="Stream script stdout/stderr."),
                    EnumValue(
                        "BUFFER",
                        description="Buffer shell script stdout/stderr, then log upon completion.",
                    ),
                    EnumValue("NONE", description="No logging"),
                ],
            ),
            is_required=False,
            default_value="BUFFER",
        ),
        "cwd": Field(
            Noneable(str),
            default_value=None,
            is_required=False,
            description="Working directory in which to execute shell script",
        ),
    }


@op(
    name="shell_op",
    description=(
        "This op executes a shell command it receives as input.\n\n"
        "This op is suitable for uses where the command to execute is generated dynamically by "
        "upstream ops. If you know the command to execute at pipeline construction time, "
        "consider `shell_command_op` instead."
    ),
    ins={"shell_command": In(str)},
    out=Out(str),
    config_schema=shell_op_config(),
)
def shell_op(context, shell_command):
    op_config = context.op_config.copy()
    op_config["env"] = {**os.environ, **op_config.get("env", {})}
    output, return_code = execute(shell_command=shell_command, log=context.log, **op_config)

    if return_code:
        raise Failure(
            description="Shell command execution failed with output: {output}".format(output=output)
        )

    return output


def create_shell_command_op(
    shell_command,
    name,
    description=None,
    required_resource_keys=None,
    tags=None,
):
    """This function is a factory that constructs ops to execute a shell command.

    Note that you can only use ``shell_command_op`` if you know the command you'd like to execute
    at pipeline construction time. If you'd like to construct shell commands dynamically during
    pipeline execution and pass them between ops, you should use ``shell_op`` instead.

    Examples:

    .. literalinclude:: ../../../../../../python_modules/libraries/dagster-shell/dagster_shell_tests/example_shell_command_op.py
       :language: python


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
        config_schema=shell_op_config(),
        required_resource_keys=required_resource_keys,
        tags=tags,
    )
    def _shell_fn(context):
        op_config = context.op_config.copy()
        op_config["env"] = {**os.environ, **op_config.get("env", {})}
        output, return_code = execute(shell_command=shell_command, log=context.log, **op_config)

        if return_code:
            raise Failure(
                description="Shell command execution failed with output: {output}".format(
                    output=output
                )
            )

        return output

    return _shell_fn


def create_shell_script_op(shell_script_path, name="create_shell_script_op", ins=None, **kwargs):
    """This function is a factory which constructs an op that will execute a shell command read
    from a script file.

    Any kwargs passed to this function will be passed along to the underlying :func:`@op
    <dagster.op>` decorator. However, note that overriding ``config`` or ``output_defs`` is not
    supported.

    You might consider using :func:`@graph <dagster.graph>` to wrap this op
    in the cases where you'd like to configure the shell op with different config fields.


    Examples:

    .. literalinclude:: ../../../../../../python_modules/libraries/dagster-shell/dagster_shell_tests/example_shell_script_op.py
       :language: python


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
        config_schema=shell_op_config(),
        **kwargs,
    )
    def _shell_script_fn(context):
        op_config = context.op_config.copy()
        op_config["env"] = {**os.environ, **op_config.get("env", {})}
        output, return_code = execute_script_file(
            shell_script_path=shell_script_path, log=context.log, **op_config
        )

        if return_code:
            raise Failure(
                description="Shell command execution failed with output: {output}".format(
                    output=output
                )
            )

        return output

    return _shell_script_fn
