import time

from dagster import job, repository, sensor


@job
def the_job():
    pass


@sensor(job=the_job)
def extremely_slow_sensor():
    time.sleep(10)


@repository
def the_repo():
    return [the_job, extremely_slow_sensor]
