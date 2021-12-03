from dagster import op, job, VersionStrategy


def my_helper_fn():
    ...


@op
def the_op():
    value = my_helper_fn()
    ...


@job
def the_job():
    the_op()
