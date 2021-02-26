from dagster import RunRequest, sensor


@sensor(pipeline_name="my_pipeline")
def my_sensor(_context):
    """
    A sensor definition. This example sensor always requests a pipeline run at each sensor tick.

    For more hints on running pipelines with sensors in Dagster, see our documentation overview on
    Sensors:
    https://docs.dagster.io/overview/schedules-sensors/sensors
    """
    should_run = True
    if should_run:
        yield RunRequest(run_key=None, run_config={})
