import dagster as dg


@dg.op
def an_op():
    pass


@dg.job
def success_job():
    an_op()


@dg.job
def another_success_job():
    an_op()


@dg.op
def failure_op():
    raise Exception("womp womp")


@dg.job
def another_failure_job():
    failure_op()


defs = dg.Definitions(jobs=[success_job, another_success_job, another_failure_job])
