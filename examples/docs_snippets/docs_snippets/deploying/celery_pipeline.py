from dagster import ModeDefinition, default_executors, fs_io_manager, pipeline, solid
from dagster_celery import celery_executor

celery_mode_defs = [
    ModeDefinition(
        resource_defs={"io_manager": fs_io_manager},
        executor_defs=default_executors + [celery_executor],
    )
]


@solid
def not_much():
    return


@pipeline(mode_defs=celery_mode_defs)
def parallel_pipeline():
    for i in range(50):
        not_much.alias("not_much_" + str(i))()
