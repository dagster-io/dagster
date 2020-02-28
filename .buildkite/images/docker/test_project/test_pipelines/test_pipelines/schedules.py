import datetime

from dagster import schedules
from dagster.core.definitions.decorators import daily_schedule

from .repo import optional_outputs


@daily_schedule(
    pipeline_name=optional_outputs.name, start_date=datetime.datetime(2020, 1, 1),
)
def daily_optional_outputs(_date):
    return {}


@schedules
def define_schedules():
    return [daily_optional_outputs]
