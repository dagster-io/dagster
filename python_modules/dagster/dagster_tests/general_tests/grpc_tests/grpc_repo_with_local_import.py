import dummy_local_file as dummy_local_file  # type: ignore
from dagster import op, job, repository


@op
def my_op():
    pass


@job
def my_job():
    my_op()


@repository
def bar_repo():
    return [my_job]
