"""isort:skip_file"""

from dagster import repository


# start_sensor_pipeline_marker
from dagster import solid, pipeline


@solid(config_schema={"filename": str})
def process_file(context):
    filename = context.solid_config["filename"]
    context.log.info(filename)


@pipeline
def log_file_pipeline():
    process_file()


# end_sensor_pipeline_marker

MY_DIRECTORY = "./"

# start_directory_sensor_marker
import os
from dagster import sensor, RunRequest


@sensor(pipeline_name="log_file_pipeline")
def my_directory_sensor(_context):
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            yield RunRequest(
                run_key=filename,
                run_config={"solids": {"process_file": {"config": {"filename": filename}}}},
            )


# end_directory_sensor_marker


def isolated_run_request():
    filename = "placeholder"

    # start_run_request_marker

    yield RunRequest(
        run_key=filename,
        run_config={"solids": {"process_file": {"config": {"filename": filename}}}},
    )

    # end_run_request_marker


# start_interval_sensors_maker


@sensor(pipeline_name="my_pipeline", minimum_interval_seconds=30)
def sensor_A(_context):
    yield RunRequest(run_key=None, run_config={})


@sensor(pipeline_name="my_pipeline", minimum_interval_seconds=45)
def sensor_B(_context):
    yield RunRequest(run_key=None, run_config={})


# end_interval_sensors_maker


@pipeline
def my_pipeline():
    pass


@repository
def my_repository():
    return [my_pipeline, log_file_pipeline, my_directory_sensor, sensor_A, sensor_B]
