from dagster import job, op, repository


@op
def do_something():
    return 1


@job
def extra_job():
    do_something()


@repository  # pyright: ignore[reportArgumentType]
def extra():
    return {"jobs": {"extra_job": extra_job}}
