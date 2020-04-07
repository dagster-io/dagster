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


def bash_command_solid(bash_command, name='bash_solid', input_defs=None, **kwargs):
    '''This function is a factory which constructs a solid that will execute a Bash command.

    Any kwargs passed to this function will be passed along to the underlying :func:`@solid
    <dagster.solid>` decorator. However, note that overriding ``config`` or ``output_defs`` is not
    supported.

    You might consider using :func:`@composite_solid <dagster.composite_solid>` to wrap this solid
    in the cases where you'd like to configure the bash solid with different config fields.


    Examples:

    .. literalinclude:: ../../../../../python_modules/libraries/dagster-bash/dagster_bash_tests/example_bash_command_solid.py
       :language: python


    Args:
        bash_command (str): The shell command to execute.
        name (str, optional): The name of this solid. Defaults to "bash_solid".
        input_defs (List[InputDefinition], optional): input definitions for the solid. Defaults to
            a single Nothing input.

    Raises:
        Failure: Raised when the shell command returns a non-zero exit code.

    Returns:
        SolidDefinition: Returns the constructed solid definition.
    '''
    check.str_param(bash_command, 'bash_command')
    name = check.str_param(name, 'name')
    check.opt_list_param(input_defs, 'input_defs', of_type=InputDefinition)

    if 'output_defs' in kwargs:
        raise TypeError('Overriding output_defs for bash solid is not supported.')

    if 'config' in kwargs:
        raise TypeError('Overriding config for bash solid is not supported.')

    @solid(
        name=name,
        description=kwargs.pop('description', 'A solid to invoke a bash command.'),
        input_defs=input_defs or [InputDefinition('start', Nothing)],
        output_defs=[OutputDefinition(str, 'result')],
        config=bash_solid_config(),
        **kwargs
    )
    def _bash_solid(context):
        output, return_code = execute(
            bash_command=bash_command, log=context.log, **context.solid_config
        )

        if return_code:
            raise Failure(
                description='Bash command execution failed with output: {output}'.format(
                    output=output
                )
            )

        return output

    return _bash_solid


def bash_script_solid(bash_script_path, name='bash_script_solid', input_defs=None, **kwargs):
    '''This function is a factory which constructs a solid that will execute a Bash command read
    from a script file.

    Any kwargs passed to this function will be passed along to the underlying :func:`@solid
    <dagster.solid>` decorator. However, note that overriding ``config`` or ``output_defs`` is not
    supported.

    You might consider using :func:`@composite_solid <dagster.composite_solid>` to wrap this solid
    in the cases where you'd like to configure the bash solid with different config fields.


    Examples:

    .. literalinclude:: ../../../../../python_modules/libraries/dagster-bash/dagster_bash_tests/example_bash_script_solid.py
       :language: python


    Args:
        bash_script_path (str): The script file to execute.
        name (str, optional): The name of this solid. Defaults to "bash_script_solid".
        input_defs (List[InputDefinition], optional): input definitions for the solid. Defaults to
            a single Nothing input.

    Raises:
        Failure: Raised when the shell command returns a non-zero exit code.

    Returns:
        SolidDefinition: Returns the constructed solid definition.
    '''
    check.str_param(bash_script_path, 'bash_script_path')
    name = check.str_param(name, 'name')
    check.opt_list_param(input_defs, 'input_defs', of_type=InputDefinition)

    if 'output_defs' in kwargs:
        raise TypeError('Overriding output_defs for bash solid is not supported.')

    if 'config' in kwargs:
        raise TypeError('Overriding config for bash solid is not supported.')

    @solid(
        name=name,
        description=kwargs.pop('description', 'A solid to invoke a bash command.'),
        input_defs=input_defs or [InputDefinition('start', Nothing)],
        output_defs=[OutputDefinition(str, 'result')],
        config=bash_solid_config(),
        **kwargs
    )
    def _bash_script_solid(context):
        output, return_code = execute_script_file(
            bash_script_path=bash_script_path, log=context.log, **context.solid_config
        )

        if return_code:
            raise Failure(
                description='Bash command execution failed with output: {output}'.format(
                    output=output
                )
            )

        return output

    return _bash_script_solid


def bash_solid_config():
    return {
        'env': Field(
            Noneable(Permissive()),
            default_value=os.environ.copy(),
            is_required=False,
            description='An optional dict of environment variables to pass to the subprocess. '
            'Defaults to using os.environ.copy().',
        ),
        'output_logging': Field(
            Enum(
                name='OutputType',
                enum_values=[
                    EnumValue('STREAM', description='Stream script stdout/stderr.'),
                    EnumValue(
                        'BUFFER',
                        description='Buffer bash script stdout/stderr, then log upon completion.',
                    ),
                    EnumValue('NONE', description='No logging'),
                ],
            ),
            is_required=False,
            default_value='BUFFER',
        ),
        'cwd': Field(
            Noneable(str),
            default_value=None,
            is_required=False,
            description='Working directory in which to execute bash script',
        ),
    }
