import dagster as dg


# this code location also contains a job named success_job. But it should not trigger the sensor in code_location_with_sensor
@dg.op
def an_op():
    pass


@dg.job
def success_job():
    an_op()


defs = dg.Definitions(
    jobs=[success_job],
)
