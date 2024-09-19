from dagster import Definitions, job, op


@op
def an_op():
    pass


@job
def success_job():
    an_op()


@job
def another_success_job():
    an_op()


@op
def failure_op():
    raise Exception("womp womp")


@job
def another_failure_job():
    failure_op()


defs = Definitions(jobs=[success_job, another_success_job, another_failure_job])
