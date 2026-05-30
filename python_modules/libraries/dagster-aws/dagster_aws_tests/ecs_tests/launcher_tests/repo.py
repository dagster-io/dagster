import dagster


@dagster.op
def node(_):
    pass


@dagster.job
def job():
    node()


@dagster.repository
def repository():
    return {"jobs": {"job": job}}
