import dagster as dg


@dg.job
def job_one():
    pass


@dg.job
def job_two():
    pass


@dg.repository
def multi_job():
    return [job_one, job_two]
