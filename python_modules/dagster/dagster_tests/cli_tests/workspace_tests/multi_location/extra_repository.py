import dagster as dg


@dg.op
def extra_op(_):
    pass


@dg.job
def extra_job():
    extra_op()


@dg.repository
def extra_repository():
    return [extra_job]
