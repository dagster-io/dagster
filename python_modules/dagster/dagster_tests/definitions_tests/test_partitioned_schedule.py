from datetime import datetime

import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    asset,
    build_schedule_context,
    define_asset_job,
    graph,
    instance_for_test,
    op,
    repository,
)
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.partition import (
    DynamicPartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partitioned_schedule import build_schedule_from_partitioned_job
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    TimeWindow,
    daily_partitioned_config,
    hourly_partitioned_config,
    monthly_partitioned_config,
    weekly_partitioned_config,
)
from dagster._core.test_utils import freeze_time
from dagster._time import create_datetime, parse_time_string

DATE_FORMAT = "%Y-%m-%d"


def time_window(start: str, end: str) -> TimeWindow:
    return TimeWindow(parse_time_string(start), parse_time_string(end))


def schedule_for_partitioned_config(
    partitioned_config, minute_of_hour=None, hour_of_day=None, day_of_week=None, day_of_month=None
):
    @op
    def my_op():
        pass

    @graph
    def my_graph():
        my_op()

    return build_schedule_from_partitioned_job(
        my_graph.to_job(config=partitioned_config),
        minute_of_hour=minute_of_hour,
        hour_of_day=hour_of_day,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        tags={"test_tag_key": "test_tag_value"},
    )


def test_daily_schedule():
    @daily_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()

    assert keys[0] == "2021-05-05"
    assert keys[1] == "2021-05-06"

    partitions_def = my_partitioned_config.partitions_def
    partition_keys = partitions_def.get_partition_keys()
    assert partitions_def.time_window_for_partition_key(partition_keys[0]) == time_window(
        "2021-05-05", "2021-05-06"
    )

    assert my_partitioned_config.get_run_config_for_partition_key(keys[0]) == {
        "start": "2021-05-05T00:00:00+00:00",
        "end": "2021-05-06T00:00:00+00:00",
    }

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30
    )
    assert my_schedule.cron_schedule == "30 9 * * *"  # pyright: ignore[reportAttributeAccessIssue]

    run_request = my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-05-08", DATE_FORMAT)
        )
    ).run_requests[0]
    assert run_request.run_config == {
        "start": "2021-05-07T00:00:00+00:00",
        "end": "2021-05-08T00:00:00+00:00",
    }
    assert run_request.tags["test_tag_key"] == "test_tag_value"

    @repository
    def _repo():
        return [my_schedule]


def test_daily_schedule_with_offsets():
    @daily_partitioned_config(start_date="2021-05-05", minute_offset=15, hour_offset=2)
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()
    assert keys[0] == "2021-05-05"
    assert keys[1] == "2021-05-06"

    assert my_partitioned_config.partitions_def.time_window_for_partition_key(
        keys[0]
    ) == time_window("2021-05-05T02:15:00", "2021-05-06T02:15:00")

    assert my_partitioned_config.get_run_config_for_partition_key(keys[0]) == {
        "start": "2021-05-05T02:15:00+00:00",
        "end": "2021-05-06T02:15:00+00:00",
    }

    my_schedule_default = schedule_for_partitioned_config(my_partitioned_config)
    assert my_schedule_default.cron_schedule == "15 2 * * *"  # pyright: ignore[reportAttributeAccessIssue]

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30
    )
    assert my_schedule.cron_schedule == "30 9 * * *"  # pyright: ignore[reportAttributeAccessIssue]

    assert my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
        build_schedule_context(scheduled_execution_time=datetime(2021, 5, 8, 9, 30))
    ).run_requests[0].run_config == {
        "start": "2021-05-07T02:15:00+00:00",
        "end": "2021-05-08T02:15:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_hourly_schedule():
    @hourly_partitioned_config(start_date=datetime(2021, 5, 5))
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()
    assert keys[0] == "2021-05-05-00:00"
    assert keys[1] == "2021-05-05-01:00"

    assert my_partitioned_config.partitions_def.time_window_for_partition_key(
        keys[0]
    ) == time_window("2021-05-05T00:00:00", "2021-05-05T01:00:00")

    assert my_partitioned_config.get_run_config_for_partition_key(keys[0]) == {
        "start": "2021-05-05T00:00:00+00:00",
        "end": "2021-05-05T01:00:00+00:00",
    }

    my_schedule_default = schedule_for_partitioned_config(my_partitioned_config)
    assert my_schedule_default.cron_schedule == "0 * * * *"  # pyright: ignore[reportAttributeAccessIssue]

    my_schedule = schedule_for_partitioned_config(my_partitioned_config, minute_of_hour=30)
    assert my_schedule.cron_schedule == "30 * * * *"  # pyright: ignore[reportAttributeAccessIssue]

    assert my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
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


def test_hourly_schedule_with_offsets():
    @hourly_partitioned_config(start_date=datetime(2021, 5, 5), minute_offset=20)
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()
    assert keys[0] == "2021-05-05-00:20"
    assert keys[1] == "2021-05-05-01:20"
    assert my_partitioned_config.partitions_def.time_window_for_partition_key(
        keys[0]
    ) == time_window("2021-05-05T00:20:00", "2021-05-05T01:20:00")

    assert my_partitioned_config.get_run_config_for_partition_key(keys[0]) == {
        "start": "2021-05-05T00:20:00+00:00",
        "end": "2021-05-05T01:20:00+00:00",
    }

    my_schedule = schedule_for_partitioned_config(my_partitioned_config, minute_of_hour=30)
    assert my_schedule.cron_schedule == "30 * * * *"  # pyright: ignore[reportAttributeAccessIssue]

    assert my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-05-08", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-05-07T22:20:00+00:00",
        "end": "2021-05-07T23:20:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_weekly_schedule():
    @weekly_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()
    assert keys[0] == "2021-05-09"
    assert keys[1] == "2021-05-16"
    assert my_partitioned_config.partitions_def.time_window_for_partition_key(
        keys[0]
    ) == time_window("2021-05-09", "2021-05-16")

    assert my_partitioned_config.get_run_config_for_partition_key(keys[0]) == {
        "start": "2021-05-09T00:00:00+00:00",
        "end": "2021-05-16T00:00:00+00:00",
    }

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30, day_of_week=2
    )
    assert my_schedule.cron_schedule == "30 9 * * 2"  # pyright: ignore[reportAttributeAccessIssue]

    assert my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
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


def test_weekly_schedule_with_offsets():
    @weekly_partitioned_config(
        start_date="2021-05-05", minute_offset=10, hour_offset=13, day_offset=3
    )
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()
    assert keys[0] == "2021-05-05"
    assert keys[1] == "2021-05-12"
    assert my_partitioned_config.partitions_def.time_window_for_partition_key(
        keys[0]
    ) == time_window("2021-05-05T13:10:00", "2021-05-12T13:10:00")

    assert my_partitioned_config.get_run_config_for_partition_key(keys[0]) == {
        "start": "2021-05-05T13:10:00+00:00",
        "end": "2021-05-12T13:10:00+00:00",
    }

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30, day_of_week=2
    )
    assert my_schedule.cron_schedule == "30 9 * * 2"  # pyright: ignore[reportAttributeAccessIssue]

    assert my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-05-21", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-05-12T13:10:00+00:00",
        "end": "2021-05-19T13:10:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_monthly_schedule():
    @monthly_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()
    assert keys[0] == "2021-06-01"
    assert keys[1] == "2021-07-01"
    assert my_partitioned_config.partitions_def.time_window_for_partition_key(
        keys[0]
    ) == time_window("2021-06-01", "2021-07-01")

    assert my_partitioned_config.get_run_config_for_partition_key(keys[0]) == {
        "start": "2021-06-01T00:00:00+00:00",
        "end": "2021-07-01T00:00:00+00:00",
    }

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30, day_of_month=2
    )
    assert my_schedule.cron_schedule == "30 9 2 * *"  # pyright: ignore[reportAttributeAccessIssue]

    assert my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
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


def test_monthly_schedule_late_in_month():
    @monthly_partitioned_config(
        start_date="2021-05-05", minute_offset=15, hour_offset=16, day_offset=31
    )
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()
    assert keys[0] == "2021-05-31"
    assert keys[1] == "2021-07-31"


def test_monthly_schedule_with_offsets():
    @monthly_partitioned_config(
        start_date="2021-05-05", minute_offset=15, hour_offset=16, day_offset=12
    )
    def my_partitioned_config(start, end):
        return {"start": start.isoformat(), "end": end.isoformat()}

    keys = my_partitioned_config.get_partition_keys()
    assert keys[0] == "2021-05-12"
    assert keys[1] == "2021-06-12"
    assert my_partitioned_config.partitions_def.time_window_for_partition_key(
        keys[0]
    ) == time_window("2021-05-12T16:15:00", "2021-06-12T16:15:00")

    assert my_partitioned_config.get_run_config_for_partition_key(keys[0]) == {
        "start": "2021-05-12T16:15:00+00:00",
        "end": "2021-06-12T16:15:00+00:00",
    }

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30, day_of_month=2
    )
    assert my_schedule.cron_schedule == "30 9 2 * *"  # pyright: ignore[reportAttributeAccessIssue]

    assert my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-06-21", DATE_FORMAT)
        )
    ).run_requests[0].run_config == {
        "start": "2021-05-12T16:15:00+00:00",
        "end": "2021-06-12T16:15:00+00:00",
    }

    @repository
    def _repo():
        return [my_schedule]


def test_empty_partitions():
    @daily_partitioned_config(start_date="2021-05-05")
    def my_partitioned_config(start, end):
        del start
        del end
        assert False

    my_schedule = schedule_for_partitioned_config(
        my_partitioned_config, hour_of_day=9, minute_of_hour=30
    )

    result = my_schedule.evaluate_tick(  # pyright: ignore[reportAttributeAccessIssue]
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2021-05-05", DATE_FORMAT)
        )
    )

    assert len(result.run_requests) == 0  # pyright: ignore[reportArgumentType]
    assert result.skip_message is not None


def test_future_tick():
    with freeze_time(create_datetime(2022, 2, 28)):

        @daily_partitioned_config(start_date="2021-05-05")
        def my_partitioned_config(start, end):
            return {"start": start.isoformat(), "end": end.isoformat()}

        my_schedule = schedule_for_partitioned_config(my_partitioned_config)

        run_request = my_schedule.evaluate_tick(  # pyright: ignore[reportOptionalSubscript,reportAttributeAccessIssue]
            build_schedule_context(
                scheduled_execution_time=datetime.strptime("2022-03-05", DATE_FORMAT)
            )
        ).run_requests[0]
        assert run_request.run_config == {
            "start": "2022-03-04T00:00:00+00:00",
            "end": "2022-03-05T00:00:00+00:00",
        }
        assert run_request.tags["test_tag_key"] == "test_tag_value"


def test_multipartitioned_job_schedule():
    time_window_partitions = DailyPartitionsDefinition(start_date="2020-01-01")
    static_partitions = StaticPartitionsDefinition(["a", "b", "c", "d"])
    multipartitions_def = MultiPartitionsDefinition(
        {
            "static": static_partitions,
            "date": time_window_partitions,
        }
    )

    @asset(partitions_def=multipartitions_def)
    def my_asset():
        return 1

    my_job = define_asset_job("multipartitions_job", [my_asset], partitions_def=multipartitions_def)
    my_schedule = build_schedule_from_partitioned_job(my_job)

    @repository
    def my_repo():
        return [my_asset, my_schedule, my_job]

    run_requests = my_schedule.evaluate_tick(  # pyright: ignore[reportAttributeAccessIssue]
        build_schedule_context(
            scheduled_execution_time=datetime.strptime("2020-01-02", DATE_FORMAT),
            repository_def=my_repo,
        )
    ).run_requests
    assert len(run_requests) == 4  # pyright: ignore[reportArgumentType]
    assert set([req.partition_key for req in run_requests]) == set(  # pyright: ignore[reportOptionalIterable]
        [
            "2020-01-01|a",
            "2020-01-01|b",
            "2020-01-01|c",
            "2020-01-01|d",
        ]
    )


def test_invalid_multipartitioned_job_schedule():
    static_partitions = StaticPartitionsDefinition(["a", "b", "c", "d"])
    multipartitions_def = MultiPartitionsDefinition(
        {
            "1": static_partitions,
            "2": static_partitions,
        }
    )

    @asset(partitions_def=multipartitions_def)
    def my_asset():
        return 1

    with pytest.raises(DagsterInvalidDefinitionError):
        build_schedule_from_partitioned_job(
            define_asset_job("multipartitions_job", [my_asset], partitions_def=multipartitions_def)
        )


def test_unresolved_partitioned_schedule():
    partitions_def = DailyPartitionsDefinition(start_date="2020-01-01")

    @asset(partitions_def=partitions_def)
    def asset1():
        return 1

    job1 = define_asset_job("job1")
    schedule1 = build_schedule_from_partitioned_job(job1)

    @repository
    def my_repo():
        return [asset1, job1, schedule1]

    run_requests = (
        my_repo.get_schedule_def("job1_schedule")
        .evaluate_tick(
            build_schedule_context(
                scheduled_execution_time=datetime.strptime("2020-01-02", DATE_FORMAT)
            )
        )
        .run_requests
    )
    assert len(run_requests) == 1  # pyright: ignore[reportArgumentType]
    assert run_requests[0].partition_key == "2020-01-01"  # pyright: ignore[reportOptionalSubscript]


def test_unresolved_multi_partitioned_schedule():
    time_window_partitions = DailyPartitionsDefinition(start_date="2020-01-01")
    static_partitions = StaticPartitionsDefinition(["a", "b", "c", "d"])
    partitions_def = MultiPartitionsDefinition(
        {"static": static_partitions, "date": time_window_partitions}
    )

    @asset(partitions_def=partitions_def)
    def asset1():
        return 1

    job1 = define_asset_job("job1")
    schedule1 = build_schedule_from_partitioned_job(job1)

    @repository
    def my_repo():
        return [asset1, job1, schedule1]

    run_requests = (
        my_repo.get_schedule_def("job1_schedule")
        .evaluate_tick(
            build_schedule_context(
                scheduled_execution_time=datetime.strptime("2020-01-02", DATE_FORMAT)
            )
        )
        .run_requests
    )
    assert len(run_requests) == 4  # pyright: ignore[reportArgumentType]
    assert set([req.partition_key for req in run_requests]) == set(  # pyright: ignore[reportOptionalIterable]
        [
            "2020-01-01|a",
            "2020-01-01|b",
            "2020-01-01|c",
            "2020-01-01|d",
        ]
    )


def test_dynamic_multipartitioned_job_schedule():
    time_window_partitions = DailyPartitionsDefinition(start_date="2020-01-01")
    dynamic_partitions = DynamicPartitionsDefinition(name="dummy")
    multipartitions_def = MultiPartitionsDefinition(
        {
            "dynamic": dynamic_partitions,
            "date": time_window_partitions,
        }
    )

    @asset(partitions_def=multipartitions_def)
    def my_asset():
        return 1

    my_job = define_asset_job("multipartitions_job", [my_asset], partitions_def=multipartitions_def)
    my_schedule = build_schedule_from_partitioned_job(my_job)

    @repository
    def my_repo():
        return [my_asset, my_schedule, my_job]

    with instance_for_test() as instance:
        instance.add_dynamic_partitions(dynamic_partitions.name, ["a", "b", "c", "d"])  # pyright: ignore[reportArgumentType]

        run_requests = my_schedule.evaluate_tick(  # pyright: ignore[reportAttributeAccessIssue]
            build_schedule_context(
                scheduled_execution_time=datetime.strptime("2020-01-02", DATE_FORMAT),
                repository_def=my_repo,
                instance=instance,
            )
        ).run_requests

        assert len(run_requests) == 4  # pyright: ignore[reportArgumentType]
        assert set([req.partition_key for req in run_requests]) == {  # pyright: ignore[reportOptionalIterable]
            "2020-01-01|a",
            "2020-01-01|b",
            "2020-01-01|c",
            "2020-01-01|d",
        }
