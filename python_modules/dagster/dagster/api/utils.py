import subprocess

from dagster import check
from dagster.serdes.ipc import DagsterIPCProtocolError, read_unary_response, write_unary_input
from dagster.utils.temp_file import get_temp_file_name


def execute_command_in_subprocess(parts):
    check.list_param(parts, 'parts', of_type=str)
    try:
        subprocess.check_output(parts, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise DagsterIPCProtocolError(
            "Error when executing API command {cmd}: {output}".format(
                cmd=e.cmd, output=e.output.decode('utf-8')
            )
        )


def execute_unary_api_cli_command(executable_path, command_name, input_obj):
    with get_temp_file_name() as input_file, get_temp_file_name() as output_file:
        parts = [
            executable_path,
            '-m',
            'dagster',
            'api',
            command_name,
            input_file,
            output_file,
        ]

        write_unary_input(input_file, input_obj)

        execute_command_in_subprocess(parts)

        return read_unary_response(output_file)
