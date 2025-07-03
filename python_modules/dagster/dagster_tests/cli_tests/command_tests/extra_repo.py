import dagster as dg


@dg.op
def do_something():
    return 1


@dg.job
def extra_job():
    do_something()


@dg.repository  # pyright: ignore[reportArgumentType]
def extra():
    return {"jobs": {"extra_job": extra_job}}
