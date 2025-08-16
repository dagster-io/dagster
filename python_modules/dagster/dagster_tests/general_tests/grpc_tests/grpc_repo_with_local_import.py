import dummy_local_file as dummy_local_file  # type: ignore

import dagster as dg


@dg.op
def my_op():
    pass


@dg.job
def my_job():
    my_op()


@dg.repository
def bar_repo():
    return [my_job]
