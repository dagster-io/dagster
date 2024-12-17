import dagster


@dagster.op
def node(_):
    pass


@dagster.job
def job():
    node()


@dagster.repository  # pyright: ignore[reportArgumentType]
def repository():
    return {"jobs": {"job": job}}
