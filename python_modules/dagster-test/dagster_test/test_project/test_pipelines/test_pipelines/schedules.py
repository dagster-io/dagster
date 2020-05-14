import datetime

from dagster.core.definitions.decorators import daily_schedule, schedule

from .repo import optional_outputs


@daily_schedule(
    pipeline_name=optional_outputs.name, start_date=datetime.datetime(2020, 1, 1),
)
def daily_optional_outputs(_date):
    return {}


@schedule(pipeline_name='large_pipeline_celery', cron_schedule='*/2 * * * *')
def frequent_large_pipe(_):
    from dagster_k8s import get_celery_engine_config

    return get_celery_engine_config()


def define_schedules():
    return [daily_optional_outputs, frequent_large_pipe]
