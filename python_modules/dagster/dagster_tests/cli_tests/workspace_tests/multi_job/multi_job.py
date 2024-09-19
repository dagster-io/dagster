from dagster import job, repository


@job
def job_one():
    pass


@job
def job_two():
    pass


@repository
def multi_job():
    return [job_one, job_two]
