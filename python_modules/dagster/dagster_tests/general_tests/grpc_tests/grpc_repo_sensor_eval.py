import time

import dagster as dg


@dg.job
def the_job():
    pass


@dg.sensor(job=the_job)
def extremely_slow_sensor():
    time.sleep(10)


@dg.repository
def the_repo():
    return [the_job, extremely_slow_sensor]
