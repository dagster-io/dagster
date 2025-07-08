import dagster as dg


@dg.op
def my_op():
    pass


@dg.job
def my_job():
    my_op()


@dg.repository
def my_repo():
    return [my_job, my_job]
