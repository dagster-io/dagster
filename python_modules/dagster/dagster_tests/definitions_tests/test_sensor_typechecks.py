import dagster as dg


@dg.op
def foo_op(_):
    return


@dg.job
def foo_job():
    foo_op()


@dg.sensor(job=foo_job)
def foo_sensor(_context):
    return


def test_sensor_typechecks_when_defined_on_job_decorated_function():
    assert foo_sensor is not None
