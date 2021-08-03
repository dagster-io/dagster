"""isort:skip_file"""


# start_local_mode
from dagster_dask import dask_executor
from dagster import ModeDefinition, default_executors, fs_io_manager


local_mode = ModeDefinition(
    name="local",
    resource_defs={"io_manager": fs_io_manager},
    executor_defs=default_executors + [dask_executor],
)
# end_local_mode
# start_distributed_mode

from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

distributed_mode = ModeDefinition(
    name="distributed",
    resource_defs={"io_manager": s3_pickle_io_manager, "s3": s3_resource},
    executor_defs=default_executors + [dask_executor],
)
# end_distributed_mode

# start_pipeline_marker

from dagster import pipeline, solid


@solid
def hello_world():
    return "Hello, World!"


@pipeline(mode_defs=[local_mode, distributed_mode])
def dask_pipeline():
    return hello_world()


# end_pipeline_marker
