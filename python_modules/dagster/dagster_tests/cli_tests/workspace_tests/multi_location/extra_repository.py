from dagster import job, op, repository


@op
def extra_op(_):
    pass


@job
def extra_job():
    extra_op()


@repository
def extra_repository():
    return [extra_job]
