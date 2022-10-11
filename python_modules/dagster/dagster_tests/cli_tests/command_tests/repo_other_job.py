from dagster import job, op, repository


@op
def my_op():
    pass


@job
def my_job():
    my_op()


@repository
def my_other_repo():
    return [my_job]
