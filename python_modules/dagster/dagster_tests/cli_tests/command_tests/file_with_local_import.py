# type: ignore
import dummy_local_file
from dagster import job, op


@op
def do_something_op():
    return 1


@op
def do_input_op(x):
    return x


@job
def qux_job():
    do_input_op(do_something_op())
