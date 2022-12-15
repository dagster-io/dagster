from dagster import job, repository


@job
def do_it_all():
    ...


@repository
def my_repo():
    return [do_it_all]
