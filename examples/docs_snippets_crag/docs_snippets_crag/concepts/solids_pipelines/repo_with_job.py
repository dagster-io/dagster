from dagster import repository

from .jobs import do_it_all_job


@repository
def my_repo():
    return [do_it_all_job]
