import dagster as dg


@dg.op(name="oknow")
def invalid_op():
    pass


@dg.job
def invalid_job():
    invalid_op()
