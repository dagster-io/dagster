from datetime import datetime
from typing import cast

import pendulum

from dagster import build_schedule_context, graph, repository, solid
from dagster.core.definitions.partitioned_schedule import build_schedule_from_partitioned_job
from dagster.core.definitions.time_window_partitions import (
    TimeWindow,
    daily_partitioned_config,
    hourly_partitioned_config,
    monthly_partitioned_config,
    weekly_partitioned_config,
)

DATE_FORMAT = "%Y-%m-%d"


def time_window(start: str, end: str) -> TimeWindow:
    return TimeWindow(cast(datetime, pendulum.parse(start)), cast(datetime, pendulum.parse(end)))


def schedule_for_partitioned_config(
    partitioned_config, minute_of_hour=None, hour_of_day=None, day_of_week=None, day_of_month=None
):
    @solid
    def my_solid():
        pass

    @graph
    def my_graph():
        my_solid()

    return build_schedule_from_partitioned_job(
        my_graph.to_job(config=partitioned_config),
        minute_of_hour=minute_of_hour,
        hour_of_day=hour_of_day,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
    )


def test_daily_schedule():
    @daily_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(start, end):
        return {"start": str(start), "end": str(end)}

    assert my_partitioned_config.get_partition_keys()[0] == "2021-05-05"
    assert my_partitioned_config.get_partition_keys()[1] == "2021-05-06"

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30
    )
    assert my_schedule.cron_schedule == "30 9 * * *"

    assert my_schedule.evaluate_tick(
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-05-08", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-05-07T00:00:00+00:00",
        "end": "2021-05-08T00:00:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_hourly_schedule():
    @hourly_partitioned_config(start_date=datetime(2021, 5, 5))
    def my_partitioned_config(start, end):
        return {"start": str(start), "end": str(end)}

    assert my_partitioned_config.get_partition_keys()[0] == "2021-05-05-00:00"
    assert my_partitioned_config.get_partition_keys()[1] == "2021-05-05-01:00"

    my_schedule = schedule_for_partitioned_config(my_partitioned_config, minute_of_hour=30)
    assert my_schedule.cron_schedule == "30 * * * *"

    assert my_schedule.evaluate_tick(
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-05-08", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-05-07T23:00:00+00:00",
        "end": "2021-05-08T00:00:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_weekly_schedule():
    @weekly_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(start, end):
        return {"start": str(start), "end": str(end)}

    assert my_partitioned_config.get_partition_keys()[0] == "2021-05-09"
    assert my_partitioned_config.get_partition_keys()[1] == "2021-05-16"

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30, day_of_week=2
    )
    assert my_schedule.cron_schedule == "30 9 * * 2"

    assert my_schedule.evaluate_tick(
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-05-21", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-05-09T00:00:00+00:00",
        "end": "2021-05-16T00:00:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_weekly_schedule_on_custom_day():
    @weekly_partitioned_config(start_date="2021-05-05", start_day_of_week=3)
    def my_partitioned_config(start, end):
        return {"start": str(start), "end": str(end)}

    assert my_partitioned_config.get_partition_keys()[0] == "2021-05-05"
    assert my_partitioned_config.get_partition_keys()[1] == "2021-05-12"

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30, day_of_week=2
    )
    assert my_schedule.cron_schedule == "30 9 * * 2"

    assert my_schedule.evaluate_tick(
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-05-17", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-05-05T00:00:00+00:00",
        "end": "2021-05-12T00:00:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_monthly_schedule():
    @monthly_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(start, end):
        return {"start": str(start), "end": str(end)}

    assert my_partitioned_config.get_partition_keys()[0] == "2021-06-01"
    assert my_partitioned_config.get_partition_keys()[1] == "2021-07-01"

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30, day_of_month=2
    )
    assert my_schedule.cron_schedule == "30 9 2 * *"

    assert my_schedule.evaluate_tick(
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-07-21", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-06-01T00:00:00+00:00",
        "end": "2021-07-01T00:00:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_monthly_schedule_on_custom_day():
    @monthly_partitioned_config(start_date="2021-05-05", start_day_of_month=5)
    def my_partitioned_config(start, end):
        return {"start": str(start), "end": str(end)}

    assert my_partitioned_config.get_partition_keys()[0] == "2021-05-05"
    assert my_partitioned_config.get_partition_keys()[1] == "2021-06-05"

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30, day_of_month=2
    )
    assert my_schedule.cron_schedule == "30 9 2 * *"

    assert my_schedule.evaluate_tick(
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-06-21", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-05-05T00:00:00+00:00",
        "end": "2021-06-05T00:00:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]
