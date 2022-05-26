from dagster_shell import shell_op

from dagster import job, op


@op
def get_shell_cmd_op():
    return "echo $MY_ENV_VAR"


@job
def shell_job():
    shell_op(get_shell_cmd_op())
