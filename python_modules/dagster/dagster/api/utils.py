import subprocess

from dagster import check
from dagster.serdes.ipc import DagsterIPCProtocolError


def execute_command_in_subprocess(parts):
    check.list_param(parts, 'parts', of_type=str)
    try:
        subprocess.check_output(parts, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise DagsterIPCProtocolError(
            "Error when executing API command {cmd}: {output}".format(cmd=e.cmd, output=e.output)
        )
