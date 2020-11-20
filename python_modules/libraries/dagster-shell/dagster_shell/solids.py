import os

from dagster import (
    Enum,
    EnumValue,
    Failure,
    Field,
    InputDefinition,
    Noneable,
    Nothing,
    OutputDefinition,
    Permissive,
    check,
    solid,
)

from .utils import execute, execute_script_file


def shell_solid_config():
    return {
        "env": Field(
            Noneable(Permissive()),
            default_value=os.environ.copy(),
            is_required=False,
            description="An optional dict of environment variables to pass to the subprocess. "
            "Defaults to using os.environ.copy().",
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


@solid(
    name="shell_solid",
    description=(
        "This solid executes a shell command it receives as input.\n\n"
        "This solid is suitable for uses where the command to execute is generated dynamically by "
        "upstream solids. If you know the command to execute at pipeline construction time, "
        "consider `shell_command_solid` instead."
    ),
    input_defs=[InputDefinition("shell_command", str)],
    output_defs=[OutputDefinition(str, "result")],
    config_schema=shell_solid_config(),
)
def shell_solid(context, shell_command):
    """This solid executes a shell command it receives as input.

    This solid is suitable for uses where the command to execute is generated dynamically by
    upstream solids. If you know the command to execute at pipeline construction time, consider
    `shell_command_solid` instead.
    """
    output, return_code = execute(
        shell_command=shell_command, log=context.log, **context.solid_config
    )

    if return_code:
        raise Failure(
            description="Shell command execution failed with output: {output}".format(output=output)
        )

    return output


def create_shell_command_solid(
    shell_command, name, description=None, required_resource_keys=None, tags=None,
):
    """This function is a factory that constructs solids to execute a shell command.

    Note that you can only use `shell_command_solid` if you know the command you'd like to execute
    at pipeline construction time. If you'd like to construct shell commands dynamically during
    pipeline execution and pass them between solids, you should use `shell_solid` instead.

    Examples:

    .. literalinclude:: ../../../../../python_modules/libraries/dagster-shell/dagster_shell_tests/example_shell_command_solid.py
       :language: python


    Args:
        shell_command (str): The shell command that the constructed solid will execute.
        name (str): The name of the constructed solid.
        description (Optional[str]): Human-readable description of this solid.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by this solid.
            Setting this ensures that resource spin up for the required resources will occur before
            the shell command is executed.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for the solid. Frameworks may
            expect and require certain metadata to be attached to a solid. Users should generally
            not set metadata directly. Values that are not strings will be json encoded and must meet
            the criteria that `json.loads(json.dumps(value)) == value`.

    Raises:
        Failure: Raised when the shell command returns a non-zero exit code.

    Returns:
        SolidDefinition: Returns the constructed solid definition.
    """
    check.str_param(shell_command, "shell_command")
    name = check.str_param(name, "name")

    @solid(
        name=name,
        description=description,
        input_defs=[InputDefinition("start", Nothing)],
        output_defs=[OutputDefinition(str, "result")],
        config_schema=shell_solid_config(),
        required_resource_keys=required_resource_keys,
        tags=tags,
    )
    def _shell_solid(context):
        output, return_code = execute(
            shell_command=shell_command, log=context.log, **context.solid_config
        )

        if return_code:
            raise Failure(
                description="Shell command execution failed with output: {output}".format(
                    output=output
                )
            )

        return output

    return _shell_solid


def create_shell_script_solid(
    shell_script_path, name="create_shell_script_solid", input_defs=None, **kwargs
):
    """This function is a factory which constructs a solid that will execute a shell command read
    from a script file.

    Any kwargs passed to this function will be passed along to the underlying :func:`@solid
    <dagster.solid>` decorator. However, note that overriding ``config`` or ``output_defs`` is not
    supported.

    You might consider using :func:`@composite_solid <dagster.composite_solid>` to wrap this solid
    in the cases where you'd like to configure the shell solid with different config fields.


    Examples:

    .. literalinclude:: ../../../../../python_modules/libraries/dagster-shell/dagster_shell_tests/example_shell_script_solid.py
       :language: python


    Args:
        shell_script_path (str): The script file to execute.
        name (str, optional): The name of this solid. Defaults to "create_shell_script_solid".
        input_defs (List[InputDefinition], optional): input definitions for the solid. Defaults to
            a single Nothing input.

    Raises:
        Failure: Raised when the shell command returns a non-zero exit code.

    Returns:
        SolidDefinition: Returns the constructed solid definition.
    """
    check.str_param(shell_script_path, "shell_script_path")
    name = check.str_param(name, "name")
    check.opt_list_param(input_defs, "input_defs", of_type=InputDefinition)

    if "output_defs" in kwargs:
        raise TypeError("Overriding output_defs for shell solid is not supported.")

    if "config" in kwargs:
        raise TypeError("Overriding config for shell solid is not supported.")

    @solid(
        name=name,
        description=kwargs.pop("description", "A solid to invoke a shell command."),
        input_defs=input_defs or [InputDefinition("start", Nothing)],
        output_defs=[OutputDefinition(str, "result")],
        config_schema=shell_solid_config(),
        **kwargs,
    )
    def _shell_script_solid(context):
        output, return_code = execute_script_file(
            shell_script_path=shell_script_path, log=context.log, **context.solid_config
        )

        if return_code:
            raise Failure(
                description="Shell command execution failed with output: {output}".format(
                    output=output
                )
            )

        return output

    return _shell_script_solid
