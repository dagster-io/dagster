import os
import signal
from subprocess import PIPE, STDOUT, Popen
from tempfile import NamedTemporaryFile

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
    seven,
    solid,
)


def bash_command_solid(
    bash_command, name='bash_solid', input_defs=None, output_encoding='utf-8', **kwargs
):
    '''This function is a factory which constructs a solid that will execute a Bash command.

    Any kwargs passed to this function will be passed along to the underlying @solid decorator.
    However, note that overriding config or output_defs is not supported. You might consider using
    @composite_solid to wrap this solid in the cases where you'd like to configure the bash solid
    with different config fields.

    Args:
        bash_command (str): The shell command to execute.
        name (str, optional): The name of this solid. Defaults to "bash_solid".
        input_defs (List[InputDefinition], optional): input definitions for the solid. Defaults to
            a single Nothing input.
        output_encoding (str, optional): The output encoding of the shell, used when reading back
            logs produced by shell script execution. Defaults to "utf-8".

    Raises:
        Failure: Raised when the shell command returns a non-zero exit code.

    Returns:
        SolidDefinition: Returns the constructed solid definition.
    '''
    check.str_param(bash_command, 'bash_command')
    name = check.str_param(name, 'name')
    check.str_param(output_encoding, 'output_encoding')
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
        config={
            'env': Field(
                Noneable(Permissive()),
                default_value=None,
                is_required=False,
                description='An optional dict of environment variables to pass to the subprocess.',
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
        },
        **kwargs
    )
    def _bash_solid(context):
        '''This logic is ported from the Airflow BashOperator implementation.

        https://github.com/apache/airflow/blob/master/airflow/operators/bash_operator.py
        '''

        tmp_path = seven.get_system_temp_directory()
        context.log.info('using temporary directory: %s' % tmp_path)

        env = (
            context.solid_config['env']
            if context.solid_config['env'] is not None
            else os.environ.copy()
        )

        # Solid will return the string result of reading stdout of the shell command
        res = ''

        with NamedTemporaryFile(dir=tmp_path, prefix=name) as tmp_file:
            tmp_file.write(bytes(bash_command.encode('utf-8')))
            tmp_file.flush()
            script_location = os.path.abspath(tmp_file.name)
            context.log.info(
                'Temporary script location: {location}'.format(location=script_location)
            )

            def pre_exec():
                # Restore default signal disposition and invoke setsid
                for sig in ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ'):
                    if hasattr(signal, sig):
                        signal.signal(getattr(signal, sig), signal.SIG_DFL)
                os.setsid()

            context.log.info('Running command: {command}'.format(command=bash_command))

            # pylint: disable=subprocess-popen-preexec-fn
            sub_process = Popen(
                ['bash', tmp_file.name],
                stdout=PIPE,
                stderr=STDOUT,
                cwd=tmp_path,
                env=env,
                preexec_fn=pre_exec,
            )

            # Stream back logs as they are emitted
            if context.solid_config['output_logging'] == 'STREAM':
                for raw_line in iter(sub_process.stdout.readline, b''):
                    line = raw_line.decode(output_encoding).rstrip()
                    context.log.info(line)
                    res += line

            sub_process.wait()

            # Collect and buffer all logs, then emit
            if context.solid_config['output_logging'] == 'BUFFER':
                res = ''.join(
                    [
                        raw_line.decode(output_encoding)
                        for raw_line in iter(sub_process.stdout.readline, b'')
                    ]
                )
                context.log.info(res)

            # no logging in this case
            elif context.solid_config['output_logging'] == 'NONE':
                pass

            context.log.info(
                'Command exited with return code {retcode}'.format(retcode=sub_process.returncode)
            )

            if sub_process.returncode:
                raise Failure(
                    description='Bash command failed {command}'.format(command=bash_command)
                )
        return res

    return _bash_solid


def bash_script_solid(
    bash_script_path, name='bash_solid', input_defs=None, output_encoding='utf-8', **kwargs
):
    '''This function is a factory which constructs a solid that will execute a Bash command read
    from a script file. See :py:func:`bash_command_solid` for more information on usage.
    '''
    check.str_param(bash_script_path, 'bash_script_path')
    # name checked in bash_solid_for_command
    # output_encoding checked in bash_solid_for_command

    with open(bash_script_path, 'rb') as f:
        return bash_command_solid(
            bash_command=f.read().decode('utf-8'),
            name=name,
            input_defs=input_defs,
            output_encoding=output_encoding,
            **kwargs
        )
