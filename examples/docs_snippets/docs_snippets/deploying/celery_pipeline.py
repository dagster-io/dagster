from dagster_celery import celery_executor

from dagster import ModeDefinition, default_executors, pipeline, solid

celery_mode_defs = [ModeDefinition(executor_defs=default_executors + [celery_executor])]


@solid
def not_much(_):
    return


@pipeline(mode_defs=celery_mode_defs)
def parallel_pipeline():
    for i in range(50):
        not_much.alias("not_much_" + str(i))()
