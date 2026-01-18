import dagster as dg
import dummy_local_file  # noqa: F401 # type: ignore


@dg.op
def do_something_op():
    return 1


@dg.op
def do_input_op(x):
    return x


@dg.job
def qux_job():
    do_input_op(do_something_op())
