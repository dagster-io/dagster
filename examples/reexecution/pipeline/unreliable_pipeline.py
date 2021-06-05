import os

from random import random
from dagster import Array, Field, ModeDefinition, OutputDefinition, pipeline, solid
from dagster.core.storage.fs_io_manager import PickledObjectFilesystemIOManager
from dagster.core.storage.io_manager import io_manager


class MyDatabaseIOManager(PickledObjectFilesystemIOManager):
    def _get_path(self, context):
        keys = context.get_run_scoped_output_identifier()

        return os.path.join("/tmp", *keys)


@io_manager(output_config_schema={"partitions": Field(Array(str), is_required=False)})
def my_db_io_manager(_):
    return MyDatabaseIOManager()


@solid(
    output_defs=[
        OutputDefinition(io_manager_key="my_db_io_manager"),
    ],
)
def unreliable_start(_):
    return 1


@solid(
    output_defs=[
        OutputDefinition(io_manager_key="my_db_io_manager"),
    ],
)
def unreliable(_, num):
    failure_rate = 0.5
    if random() < failure_rate:
        raise Exception("blah")


@solid(
    output_defs=[
        OutputDefinition(io_manager_key="my_db_io_manager"),
    ],
)
def unreliable_end(_, num):
    return


@pipeline(
    mode_defs=[ModeDefinition(resource_defs={"my_db_io_manager": my_db_io_manager})],
    description="Demo pipeline of chained solids that fail with a configurable probability."
)
def unreliable_pipeline():
    unreliable_end(unreliable(unreliable_start()))
