import os
import signal
from subprocess import PIPE, STDOUT, Popen
from tempfile import NamedTemporaryFile

from dagster import Enum, EnumValue, Failure, Field, PermissiveDict, check, seven, solid


def bash_command_solid(bash_command, name=None, output_encoding=None):
    '''Execute a Bash command.
    '''
    check.str_param(bash_command, 'bash_command')
    name = check.opt_str_param(name, 'name', default='bash_solid')
    output_encoding = check.opt_str_param(output_encoding, 'output_encoding', default='utf-8')

    @solid(
        name=name,
        config={
            'output_logging': Field(
                Enum(
                    'OutputType',
                    [
                        EnumValue('STREAM', description='Stream script stdout/stderr.'),
                        EnumValue(
                            'BUFFER',
                            description='Buffer bash script stdout/stderr, then log upon completion.',
                        ),
                        EnumValue('NONE', description='No logging'),
                    ],
                ),
                is_optional=True,
                default_value='STREAM',
            ),
            'env': Field(
                PermissiveDict(),
                description='Environment variables to pass to the child process; if not provided, '
                'the current process environment will be passed.',
                is_optional=True,
                default_value=None,
            ),
        },
    )
    def _bash_solid(context):
        '''This logic is ported from the Airflow BashOperator implementation.

        https://github.com/apache/airflow/blob/master/airflow/operators/bash_operator.py
        '''

        def log_info_msg(log_str):
            context.log.info('[bash][{name}] '.format(name=name) + log_str)

        tmp_path = seven.get_system_temp_directory()
        log_info_msg('using temporary directory: %s' % tmp_path)

        env = (
            context.solid_config['env']
            if context.solid_config['env'] is not None
            else os.environ.copy()
        )

        with NamedTemporaryFile(dir=tmp_path, prefix=name) as tmp_file:
            tmp_file.write(bytes(bash_command.encode('utf-8')))
            tmp_file.flush()
            script_location = os.path.abspath(tmp_file.name)
            log_info_msg('Temporary script location: {location}'.format(location=script_location))

            def pre_exec():
                # Restore default signal disposition and invoke setsid
                for sig in ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ'):
                    if hasattr(signal, sig):
                        signal.signal(getattr(signal, sig), signal.SIG_DFL)
                os.setsid()

            log_info_msg('Running command: {command}'.format(command=bash_command))

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
                line = ''
                for raw_line in iter(sub_process.stdout.readline, b''):
                    line = raw_line.decode(output_encoding).rstrip()
                    log_info_msg(line)

            sub_process.wait()

            # Collect and buffer all logs, then emit
            if context.solid_config['output_logging'] == 'BUFFER':
                line = ''
                for raw_line in iter(sub_process.stdout.readline, b''):
                    line += raw_line.decode(output_encoding)
                log_info_msg(line)

            # no logging in this case
            elif context.solid_config['output_logging'] == 'NONE':
                pass

            log_info_msg(
                'Command exited with return code {retcode}'.format(retcode=sub_process.returncode)
            )

            if sub_process.returncode:
                raise Failure(description='[bash][{name}] Bash command failed'.format(name=name))

        return line

    return _bash_solid


def bash_script_solid(bash_script_path, name=None, output_encoding=None):
    '''run a bash command for a script file.
    '''
    check.str_param(bash_script_path, 'bash_script_path')
    # name checked in bash_solid_for_command
    # output_encoding checked in bash_solid_for_command

    with open(bash_script_path, 'rb') as f:
        return bash_command_solid(f.read().decode('utf-8'), name, output_encoding)
