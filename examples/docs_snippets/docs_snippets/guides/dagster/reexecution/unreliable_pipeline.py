from random import random

from dagster import ModeDefinition, fs_io_manager, pipeline, solid


@solid()
def unreliable_start(_):
    return 1


@solid()
def unreliable(_, num):
    failure_rate = 0.5
    if random() < failure_rate:
        raise Exception("blah")


@solid()
def unreliable_end(_, num):
    return


@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
def unreliable_pipeline():
    unreliable_end(unreliable(unreliable_start()))
