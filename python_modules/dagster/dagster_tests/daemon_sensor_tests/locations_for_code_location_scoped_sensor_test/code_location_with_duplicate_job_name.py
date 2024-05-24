from dagster import Definitions, job, op


# this code location also contains a job named success_job. But it should not trigger the sensor in code_location_with_sensor
@op
def an_op():
    pass


@job
def success_job():
    an_op()


defs = Definitions(
    jobs=[success_job],
)
