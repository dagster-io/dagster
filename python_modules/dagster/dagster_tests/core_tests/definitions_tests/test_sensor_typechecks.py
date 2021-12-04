from dagster import job, op, sensor


@op
def foo_op(_):
    return


@job
def foo_job():
    foo_op()


@sensor(job=foo_job)
def foo_sensor(_context):
    return


def test_sensor_typechecks_when_defined_on_job_decorated_function():
    assert foo_sensor is not None
