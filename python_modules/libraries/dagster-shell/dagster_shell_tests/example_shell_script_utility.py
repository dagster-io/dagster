# pylint: disable=no-value-for-parameter
from dagster_shell import execute_shell_script

from dagster import OpExecutionContext, op


@op
def my_shell_op(context: OpExecutionContext, data: str):
    temp_file = "/tmp/echo_data.sh"
    with open(temp_file, "w") as temp_file_writer:
        temp_file_writer.write(f"echo {data}")
        execute_shell_script(temp_file, output_logging="STREAM", log=context.log)
