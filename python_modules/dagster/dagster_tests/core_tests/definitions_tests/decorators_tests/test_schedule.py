import inspect
import json
import re
from datetime import datetime, time

import pendulum
import pytest
from dateutil.relativedelta import relativedelta

from dagster import (
    DagsterInvalidDefinitionError,
    RunRequest,
    ScheduleDefinition,
    build_schedule_context,
    daily_schedule,
    hourly_schedule,
    job,
    monthly_schedule,
    op,
    pipeline,
    schedule,
    validate_run_config,
    weekly_schedule,
)
from dagster.legacy import solid
from dagster.seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster.utils import merge_dicts
from dagster.utils.partitions import (
    DEFAULT_DATE_FORMAT,
    DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
    DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
    DEFAULT_MONTHLY_FORMAT,
)

# This file tests a lot of parameter name stuff, so these warnings are spurious
# pylint: disable=unused-variable, unused-argument, redefined-outer-name


def test_scheduler():
    def define_schedules():
        return [
            ScheduleDefinition(
                name="my_schedule",
                cron_schedule="* * * * *",
                pipeline_name="test_pipeline",
                run_config={},
            )
        ]

    @schedule(cron_schedule="* * * * *", pipeline_name="foo_pipeline")
    def echo_time_schedule(context):
        return {
            "echo_time": (
                (
                    context.scheduled_execution_time.isoformat()
                    if context.scheduled_execution_time
                    else ""
                )
            )
        }

    @schedule(
        cron_schedule="* * * * *", pipeline_name="foo_pipeline", should_execute=lambda x: False
    )
    def always_skip_schedule():
        return {}

    context_without_time = build_schedule_context()

    execution_time = datetime(year=2019, month=2, day=27)

    context_with_time = build_schedule_context(scheduled_execution_time=execution_time)

    execution_data = echo_time_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].run_config == {"echo_time": ""}

    execution_data = echo_time_schedule.evaluate_tick(context_with_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].run_config == {"echo_time": execution_time.isoformat()}

    execution_data = always_skip_schedule.evaluate_tick(context_with_time)
    assert execution_data.skip_message
    assert (
        execution_data.skip_message
        == "should_execute function for always_skip_schedule returned false."
    )


def test_schedule_decorators_sanity():
    @solid
    def do_nothing(_):
        pass

    @pipeline
    def foo_pipeline():
        do_nothing()

    @schedule(cron_schedule="* * * * *", pipeline_name="foo_pipeline")
    def foo_schedule():
        """Fake doc block"""
        return {}

    @monthly_schedule(
        pipeline_name="foo_pipeline",
        execution_day_of_month=3,
        start_date=datetime(year=2019, month=1, day=1),
    )
    def monthly_foo_schedule():
        """Fake doc block"""
        return {}

    @weekly_schedule(
        pipeline_name="foo_pipeline",
        execution_day_of_week=1,
        start_date=datetime(year=2019, month=1, day=1),
    )
    def weekly_foo_schedule():
        """Fake doc block"""
        return {}

    @daily_schedule(
        pipeline_name="foo_pipeline",
        start_date=datetime(year=2019, month=1, day=1),
    )
    def daily_foo_schedule():
        """Fake doc block"""
        return {}

    @hourly_schedule(
        pipeline_name="foo_pipeline",
        start_date=datetime(year=2019, month=1, day=1),
    )
    def hourly_foo_schedule():
        """Fake doc block"""
        return {}

    # Ensure that schedule definition inherits properties from wrapped fxn
    assert foo_schedule.__doc__ == """Fake doc block"""
    assert monthly_foo_schedule.__doc__ == """Fake doc block"""
    assert weekly_foo_schedule.__doc__ == """Fake doc block"""
    assert hourly_foo_schedule.__doc__ == """Fake doc block"""
    assert daily_foo_schedule.__doc__ == """Fake doc block"""

    assert not foo_schedule.execution_timezone
    assert not monthly_foo_schedule.execution_timezone
    assert not weekly_foo_schedule.execution_timezone
    assert not hourly_foo_schedule.execution_timezone
    assert not daily_foo_schedule.execution_timezone

    @schedule(
        cron_schedule="* * * * *",
        pipeline_name="foo_pipeline",
        execution_timezone="US/Central",
    )
    def foo_schedule_timezone():
        return {}

    assert foo_schedule_timezone.execution_timezone == "US/Central"

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=re.escape(
            "Invalid execution timezone MadeUpTimeZone for invalid_timezone_foo_schedule"
        ),
    ):

        @daily_schedule(
            pipeline_name="foo_pipeline",
            start_date=datetime(year=2019, month=1, day=1),
            execution_timezone="MadeUpTimeZone",
        )
        def invalid_timezone_foo_schedule():
            return {}


def _check_partitions(
    partition_schedule_def,
    expected_num_partitions,
    expected_start_date,
    expected_format,
    expected_relative_delta,
):
    partitions = partition_schedule_def.get_partition_set().get_partitions()

    assert len(partitions) == expected_num_partitions

    assert partitions[0].value == expected_start_date
    assert partitions[0].name == expected_start_date.strftime(expected_format)

    for index, partition in enumerate(partitions):
        partition_value = partitions[0].value + (index * expected_relative_delta)
        assert partition.value == partitions[0].value + (index * expected_relative_delta)
        assert partition.name == partition_value.strftime(expected_format)


HOURS_UNTIL_FEBRUARY_27 = 24 * (31 + 26)


@pytest.mark.parametrize("partition_hours_offset", [0, 1, 2])
def test_partitions_for_hourly_schedule_decorators_without_timezone(partition_hours_offset: int):
    with pendulum.test(
        to_timezone(create_pendulum_time(2019, 2, 27, 0, 1, 1, tz="UTC"), "US/Eastern")
    ):

        context_without_time = build_schedule_context()

        start_date = datetime(year=2019, month=1, day=1)

        @hourly_schedule(
            pipeline_name="foo_pipeline",
            start_date=start_date,
            execution_time=time(hour=0, minute=25),
            partition_hours_offset=partition_hours_offset,
        )
        def hourly_foo_schedule(hourly_time):
            return {"hourly_time": hourly_time.isoformat()}

        _check_partitions(
            hourly_foo_schedule,
            HOURS_UNTIL_FEBRUARY_27 + 1 - partition_hours_offset,
            pendulum.instance(start_date, tz="UTC"),
            DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
            relativedelta(hours=1),
        )

        execution_data = hourly_foo_schedule.evaluate_tick(context_without_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "hourly_time": create_pendulum_time(year=2019, month=2, day=27, tz="UTC")
            .subtract(hours=partition_hours_offset)
            .isoformat()
        }

        valid_time = create_pendulum_time(year=2019, month=1, day=27, hour=1, minute=25, tz="UTC")
        context_with_valid_time = build_schedule_context(scheduled_execution_time=valid_time)

        execution_data = hourly_foo_schedule.evaluate_tick(context_with_valid_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "hourly_time": create_pendulum_time(year=2019, month=1, day=27, hour=1, tz="UTC")
            .subtract(hours=partition_hours_offset)
            .isoformat()
        }


@pytest.mark.parametrize("partition_hours_offset", [0, 1, 2])
def test_partitions_for_hourly_schedule_decorators_with_timezone(partition_hours_offset: int):
    with pendulum.test(create_pendulum_time(2019, 2, 27, 0, 1, 1, tz="US/Central")):
        start_date = datetime(year=2019, month=1, day=1)

        # You can specify a start date with no timezone and it will be assumed to be
        # in the execution timezone

        @hourly_schedule(
            pipeline_name="foo_pipeline",
            start_date=start_date,
            execution_time=time(hour=0, minute=25),
            execution_timezone="US/Central",
            partition_hours_offset=partition_hours_offset,
        )
        def hourly_central_schedule(hourly_time):
            return {"hourly_time": hourly_time.isoformat()}

        assert hourly_central_schedule.execution_timezone == "US/Central"

        _check_partitions(
            hourly_central_schedule,
            HOURS_UNTIL_FEBRUARY_27 + 1 - partition_hours_offset,
            pendulum.instance(start_date, tz="US/Central"),
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            relativedelta(hours=1),
        )

        valid_time = create_pendulum_time(
            year=2019, month=1, day=27, hour=1, minute=25, tz="US/Central"
        )
        context_with_valid_time = build_schedule_context(scheduled_execution_time=valid_time)

        execution_data = hourly_central_schedule.evaluate_tick(context_with_valid_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "hourly_time": create_pendulum_time(year=2019, month=1, day=27, hour=1, tz="US/Central")
            .subtract(hours=partition_hours_offset)
            .isoformat()
        }

        # You can specify a start date in a different timezone and it will be transformed into the
        # execution timezone
        start_date_with_different_timezone = create_pendulum_time(2019, 1, 1, 0, tz="US/Pacific")

        @hourly_schedule(
            pipeline_name="foo_pipeline",
            start_date=start_date_with_different_timezone,
            execution_time=time(hour=0, minute=25),
            execution_timezone="US/Central",
            partition_hours_offset=partition_hours_offset,
        )
        def hourly_central_schedule_with_timezone_start_time(hourly_time):
            return {"hourly_time": hourly_time.isoformat()}

        _check_partitions(
            hourly_central_schedule_with_timezone_start_time,
            HOURS_UNTIL_FEBRUARY_27
            - 2  # start date is two hours later since it's in PT
            + 1
            - partition_hours_offset,
            to_timezone(start_date_with_different_timezone, "US/Central"),
            DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
            relativedelta(hours=1),
        )


@pytest.mark.parametrize("partition_days_offset", [0, 1, 2])
def test_partitions_for_daily_schedule_decorators_without_timezone(partition_days_offset: int):
    with pendulum.test(
        to_timezone(create_pendulum_time(2019, 2, 27, 0, 1, 1, tz="UTC"), "US/Eastern")
    ):
        context_without_time = build_schedule_context()

        start_date = datetime(year=2019, month=1, day=1)

        @daily_schedule(
            pipeline_name="foo_pipeline",
            start_date=start_date,
            execution_time=time(hour=9, minute=30),
            partition_days_offset=partition_days_offset,
        )
        def daily_foo_schedule(daily_time):
            return {"daily_time": daily_time.isoformat()}

        _check_partitions(
            daily_foo_schedule,
            (31 + 27) - partition_days_offset,
            pendulum.instance(start_date, tz="UTC"),
            DEFAULT_DATE_FORMAT,
            relativedelta(days=1),
        )

        valid_daily_time = create_pendulum_time(
            year=2019, month=1, day=27, hour=9, minute=30, tz="UTC"
        )
        context_with_valid_time = build_schedule_context(scheduled_execution_time=valid_daily_time)

        execution_data = daily_foo_schedule.evaluate_tick(context_with_valid_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "daily_time": create_pendulum_time(year=2019, month=1, day=27, tz="UTC")
            .subtract(days=partition_days_offset)
            .isoformat()
        }

        execution_data = daily_foo_schedule.evaluate_tick(context_without_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "daily_time": create_pendulum_time(year=2019, month=2, day=27, tz="UTC")
            .subtract(days=partition_days_offset)
            .isoformat()
        }


@pytest.mark.parametrize("partition_days_offset", [0, 1, 2])
def test_partitions_for_daily_schedule_decorators_with_timezone(partition_days_offset: int):
    with pendulum.test(create_pendulum_time(2019, 2, 27, 0, 1, 1, tz="US/Central")):
        start_date = datetime(year=2019, month=1, day=1)

        @daily_schedule(
            pipeline_name="foo_pipeline",
            start_date=start_date,
            execution_time=time(hour=9, minute=30),
            execution_timezone="US/Central",
            partition_days_offset=partition_days_offset,
        )
        def daily_central_schedule(daily_time):
            return {"daily_time": daily_time.isoformat()}

        assert daily_central_schedule.execution_timezone == "US/Central"

        _check_partitions(
            daily_central_schedule,
            (31 + 27) - partition_days_offset,
            pendulum.instance(start_date, tz="US/Central"),
            DEFAULT_DATE_FORMAT,
            relativedelta(days=1),
        )

        valid_daily_time = create_pendulum_time(
            year=2019, month=1, day=27, hour=9, minute=30, tz="US/Central"
        )
        context_with_valid_time = build_schedule_context(scheduled_execution_time=valid_daily_time)

        execution_data = daily_central_schedule.evaluate_tick(context_with_valid_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "daily_time": create_pendulum_time(year=2019, month=1, day=27, tz="US/Central")
            .subtract(days=partition_days_offset)
            .isoformat()
        }


@pytest.mark.parametrize("partition_weeks_offset", [0, 1, 2])
def test_partitions_for_weekly_schedule_decorators_without_timezone(partition_weeks_offset: int):
    with pendulum.test(
        to_timezone(create_pendulum_time(2019, 2, 27, 0, 1, 1, tz="UTC"), "US/Eastern")
    ):
        context_without_time = build_schedule_context()

        start_date = datetime(year=2019, month=1, day=1)

        @weekly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_week=3,
            start_date=start_date,
            execution_time=time(9, 30),
            partition_weeks_offset=partition_weeks_offset,
        )
        def weekly_foo_schedule(weekly_time):
            return {"weekly_time": weekly_time.isoformat()}

        valid_weekly_time = create_pendulum_time(
            year=2019, month=1, day=30, hour=9, minute=30, tz="UTC"
        )
        context_with_valid_time = build_schedule_context(scheduled_execution_time=valid_weekly_time)

        execution_data = weekly_foo_schedule.evaluate_tick(context_with_valid_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "weekly_time": create_pendulum_time(year=2019, month=1, day=29, tz="UTC")
            .subtract(weeks=partition_weeks_offset)
            .isoformat()
        }

        execution_data = weekly_foo_schedule.evaluate_tick(context_without_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "weekly_time": create_pendulum_time(year=2019, month=2, day=26, tz="UTC")
            .subtract(weeks=partition_weeks_offset)
            .isoformat()
        }

        _check_partitions(
            weekly_foo_schedule,
            9 - partition_weeks_offset,
            pendulum.instance(start_date, tz="UTC"),
            DEFAULT_DATE_FORMAT,
            relativedelta(weeks=1),
        )


@pytest.mark.parametrize("partition_weeks_offset", [0, 1, 2])
def test_partitions_for_weekly_schedule_decorators_with_timezone(partition_weeks_offset: int):
    with pendulum.test(create_pendulum_time(2019, 2, 27, 0, 1, 1, tz="US/Central")):

        start_date = datetime(year=2019, month=1, day=1)

        @weekly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_week=3,
            start_date=start_date,
            execution_time=time(9, 30),
            execution_timezone="US/Central",
            partition_weeks_offset=partition_weeks_offset,
        )
        def weekly_foo_schedule(weekly_time):
            return {"weekly_time": weekly_time.isoformat()}

        assert weekly_foo_schedule.execution_timezone == "US/Central"

        valid_weekly_time = create_pendulum_time(
            year=2019, month=1, day=30, hour=9, minute=30, tz="US/Central"
        )
        context_with_valid_time = build_schedule_context(scheduled_execution_time=valid_weekly_time)

        execution_data = weekly_foo_schedule.evaluate_tick(context_with_valid_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "weekly_time": create_pendulum_time(year=2019, month=1, day=29, tz="US/Central")
            .subtract(weeks=partition_weeks_offset)
            .isoformat()
        }

        _check_partitions(
            weekly_foo_schedule,
            9 - partition_weeks_offset,
            pendulum.instance(start_date, tz="US/Central"),
            DEFAULT_DATE_FORMAT,
            relativedelta(weeks=1),
        )


@pytest.mark.parametrize("partition_months_offset", [0, 1, 2])
def test_partitions_for_monthly_schedule_decorators_without_timezone(partition_months_offset: int):
    with pendulum.test(
        to_timezone(create_pendulum_time(2019, 3, 27, 0, 1, 1, tz="UTC"), "US/Eastern")
    ):
        context_without_time = build_schedule_context()

        start_date = datetime(year=2019, month=1, day=1)

        @monthly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_month=3,
            start_date=start_date,
            execution_time=time(9, 30),
            partition_months_offset=partition_months_offset,
        )
        def monthly_foo_schedule(monthly_time):
            return {"monthly_time": monthly_time.isoformat()}

        valid_monthly_time = create_pendulum_time(
            year=2019, month=3, day=3, hour=9, minute=30, tz="UTC"
        )
        context_with_valid_time = build_schedule_context(
            scheduled_execution_time=valid_monthly_time
        )

        execution_data = monthly_foo_schedule.evaluate_tick(context_with_valid_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "monthly_time": create_pendulum_time(year=2019, month=3, day=1, tz="UTC")
            .subtract(months=partition_months_offset)
            .isoformat()
        }

        execution_data = monthly_foo_schedule.evaluate_tick(context_without_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "monthly_time": create_pendulum_time(year=2019, month=3, day=1, tz="UTC")
            .subtract(months=partition_months_offset)
            .isoformat()
        }

        _check_partitions(
            monthly_foo_schedule,
            3 - partition_months_offset,
            pendulum.instance(start_date, tz="UTC"),
            DEFAULT_MONTHLY_FORMAT,
            relativedelta(months=1),
        )


@pytest.mark.parametrize("partition_months_offset", [0, 1, 2])
def test_partitions_for_monthly_schedule_decorators_with_timezone(partition_months_offset: int):
    with pendulum.test(create_pendulum_time(2019, 3, 27, 0, 1, 1, tz="US/Central")):
        start_date = datetime(year=2019, month=1, day=1)

        @monthly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_month=3,
            start_date=start_date,
            execution_time=time(9, 30),
            execution_timezone="US/Central",
            partition_months_offset=partition_months_offset,
        )
        def monthly_foo_schedule(monthly_time):
            return {"monthly_time": monthly_time.isoformat()}

        assert monthly_foo_schedule.execution_timezone == "US/Central"

        valid_monthly_time = create_pendulum_time(
            year=2019, month=3, day=3, hour=9, minute=30, tz="US/Central"
        )
        context_with_valid_time = build_schedule_context(
            scheduled_execution_time=valid_monthly_time
        )

        execution_data = monthly_foo_schedule.evaluate_tick(context_with_valid_time)
        assert execution_data.run_requests
        assert len(execution_data.run_requests) == 1
        assert execution_data.run_requests[0].run_config == {
            "monthly_time": create_pendulum_time(year=2019, month=3, day=1, tz="US/Central")
            .subtract(months=partition_months_offset)
            .isoformat()
        }

        _check_partitions(
            monthly_foo_schedule,
            3 - partition_months_offset,
            pendulum.instance(start_date, tz="US/Central"),
            DEFAULT_MONTHLY_FORMAT,
            relativedelta(months=1),
        )


def test_partitions_outside_schedule_range():
    execution_time = create_pendulum_time(year=2021, month=1, day=1, tz="UTC")
    context = build_schedule_context(scheduled_execution_time=execution_time)

    @monthly_schedule(
        pipeline_name="too early",
        start_date=create_pendulum_time(year=2021, month=1, day=1, tz="UTC"),
    )
    def too_early(monthly_time):
        return {"monthly_time": monthly_time.isoformat()}

    execution_data = too_early.evaluate_tick(context)
    assert execution_data.skip_message == (
        "Your partition (2020-12-01T00:00:00+00:00) is before the beginning of "
        "the partition set (2021-01-01T00:00:00+00:00). "
        "Verify your schedule's start_date is correct."
    )

    @monthly_schedule(
        pipeline_name="too late",
        start_date=create_pendulum_time(year=2020, month=1, day=1, tz="UTC"),
        end_date=create_pendulum_time(year=2020, month=12, day=1, tz="UTC"),
        partition_months_offset=0,
    )
    def too_late(monthly_time):
        return {"monthly_time": monthly_time.isoformat()}

    execution_data = too_late.evaluate_tick(context)
    assert execution_data.skip_message == (
        "Your partition (2021-01-01T00:00:00+00:00) is after the end of "
        "the partition set (2020-12-01T00:00:00+00:00). "
        "Verify your schedule's end_date is correct."
    )


def test_schedule_decorators_bad():
    @solid
    def do_nothing(_):
        pass

    @pipeline
    def foo_pipeline():
        do_nothing()

    with pytest.raises(DagsterInvalidDefinitionError):

        @monthly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_month=32,
            start_date=datetime(year=2019, month=1, day=1),
        )
        def monthly_foo_schedule_over():
            return {}

    with pytest.warns(
        UserWarning,
        match=re.escape(
            "`start_date` must be at the beginning of the first day of the month for a monthly schedule."
        ),
    ):

        @monthly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_month=7,
            start_date=datetime(year=2019, month=1, day=5),
        )
        def monthly_foo_schedule_later_in_month():
            return {}

    with pytest.raises(DagsterInvalidDefinitionError):

        @monthly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_month=0,
            start_date=datetime(year=2019, month=1, day=1),
        )
        def monthly_foo_schedule_under():
            return {}

    with pytest.raises(DagsterInvalidDefinitionError):

        @weekly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_week=7,
            start_date=datetime(year=2019, month=1, day=1),
        )
        def weekly_foo_schedule_over():
            return {}

    with pytest.warns(
        UserWarning,
        match=re.escape("`start_date` must be at the beginning of a day for a weekly schedule."),
    ):

        @weekly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_week=3,
            start_date=datetime(year=2019, month=1, day=1, hour=2),
        )
        def weekly_foo_schedule_start_later_in_day():
            return {}

    with pytest.warns(
        UserWarning,
        match=re.escape("`start_date` must be at the beginning of a day for a daily schedule."),
    ):

        @daily_schedule(
            pipeline_name="foo_pipeline",
            start_date=datetime(year=2019, month=1, day=1, hour=2),
        )
        def daily_foo_schedule_start_later_in_day():
            return {}

    with pytest.warns(
        UserWarning,
        match=re.escape(
            "`start_date` must be at the beginning of the hour for an hourly schedule."
        ),
    ):

        @hourly_schedule(
            pipeline_name="foo_pipeline",
            start_date=datetime(year=2019, month=1, day=1, hour=2, minute=30),
        )
        def hourly_foo_schedule_start_later_in_hour():
            return {}

    with pytest.raises(DagsterInvalidDefinitionError, match="invalid cron schedule"):

        @schedule(cron_schedule="", pipeline_name="foo_pipeline")
        def bad_cron_string(context):
            return {}

    with pytest.raises(DagsterInvalidDefinitionError, match="invalid cron schedule"):

        @schedule(cron_schedule="bad_schedule_two", pipeline_name="foo_pipeline")
        def bad_cron_string_two(context):
            return {}

    with pytest.raises(DagsterInvalidDefinitionError, match="invalid cron schedule"):

        @schedule(cron_schedule="* * * * * *", pipeline_name="foo_pipeline")
        def bad_cron_string_three(context):
            return {}


def test_schedule_with_nested_tags():

    nested_tags = {"foo": {"bar": "baz"}}

    @schedule(cron_schedule="* * * * *", pipeline_name="foo_pipeline", tags=nested_tags)
    def my_tag_schedule():
        return {}

    assert my_tag_schedule.evaluate_tick(
        build_schedule_context(scheduled_execution_time=pendulum.now())
    )[0][0].tags == merge_dicts(
        {key: json.dumps(val) for key, val in nested_tags.items()},
        {"dagster/schedule_name": "my_tag_schedule"},
    )


def test_scheduled_jobs():
    from dagster import Field, String

    @op(config_schema={"foo": Field(String)})
    def foo_op(context):
        pass

    DEFAULT_FOO_CONFIG = {"ops": {"foo_op": {"config": {"foo": "bar"}}}}

    @job(config=DEFAULT_FOO_CONFIG)
    def foo_job():
        foo_op()

    my_schedule = ScheduleDefinition(name="my_schedule", cron_schedule="* * * * *", job=foo_job)

    context_without_time = build_schedule_context()
    execution_time = datetime(year=2019, month=2, day=27)
    context_with_time = build_schedule_context(scheduled_execution_time=execution_time)
    execution_data = my_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1

    validate_run_config(foo_job, execution_data.run_requests[0].run_config)


def test_request_based_schedule():
    from dagster import Field, String

    context_without_time = build_schedule_context()

    start_date = datetime(year=2019, month=1, day=1)

    @op(config_schema={"foo": Field(String)})
    def foo_op(context):
        pass

    @job
    def foo_job():
        foo_op()

    FOO_CONFIG = {"ops": {"foo_op": {"config": {"foo": "bar"}}}}

    @schedule(
        cron_schedule="* * * * *",
        job=foo_job,
    )
    def foo_schedule(context):
        return RunRequest(run_key=None, run_config=FOO_CONFIG, tags={"foo": "FOO"})

    # evaluate tick
    execution_data = foo_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    run_request = execution_data.run_requests[0]
    assert run_request.run_config == FOO_CONFIG
    assert run_request.tags.get("foo") == "FOO"

    # test direct invocation
    run_request = foo_schedule(context_without_time)
    assert run_request.run_config == FOO_CONFIG
    assert run_request.tags.get("foo") == "FOO"


def test_request_based_schedule_no_context():
    from dagster import Field, String

    context_without_time = build_schedule_context()

    start_date = datetime(year=2019, month=1, day=1)

    @op(config_schema={"foo": Field(String)})
    def foo_op(context):
        pass

    @job
    def foo_job():
        foo_op()

    FOO_CONFIG = {"ops": {"foo_op": {"config": {"foo": "bar"}}}}

    @schedule(
        cron_schedule="* * * * *",
        job=foo_job,
    )
    def foo_schedule():
        return RunRequest(run_key=None, run_config=FOO_CONFIG, tags={"foo": "FOO"})

    # evaluate tick
    execution_data = foo_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    run_request = execution_data.run_requests[0]
    assert run_request.run_config == FOO_CONFIG
    assert run_request.tags.get("foo") == "FOO"

    # test direct invocation
    run_request = foo_schedule()
    assert run_request.run_config == FOO_CONFIG
    assert run_request.tags.get("foo") == "FOO"


def test_config_based_schedule():
    from dagster import Field, String

    context_without_time = build_schedule_context()

    start_date = datetime(year=2019, month=1, day=1)

    @op(config_schema={"foo": Field(String)})
    def foo_op(context):
        pass

    @job
    def foo_job():
        foo_op()

    FOO_CONFIG = {"ops": {"foo_op": {"config": {"foo": "bar"}}}}

    @schedule(
        cron_schedule="* * * * *",
        job=foo_job,
        tags={"foo": "FOO"},
    )
    def foo_schedule(context):
        return FOO_CONFIG

    # evaluate tick
    execution_data = foo_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    run_request = execution_data.run_requests[0]
    assert run_request.run_config == FOO_CONFIG
    assert run_request.tags.get("foo") == "FOO"

    # direct invocation
    run_config = foo_schedule(context_without_time)
    assert run_config == FOO_CONFIG


def test_config_based_schedule_no_context():
    from dagster import Field, String

    context_without_time = build_schedule_context()

    start_date = datetime(year=2019, month=1, day=1)

    @op(config_schema={"foo": Field(String)})
    def foo_op(context):
        pass

    @job
    def foo_job():
        foo_op()

    FOO_CONFIG = {"ops": {"foo_op": {"config": {"foo": "bar"}}}}

    @schedule(
        cron_schedule="* * * * *",
        job=foo_job,
        tags={"foo": "FOO"},
    )
    def foo_schedule():
        return FOO_CONFIG

    # evaluate tick
    execution_data = foo_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    run_request = execution_data.run_requests[0]
    assert run_request.run_config == FOO_CONFIG
    assert run_request.tags.get("foo") == "FOO"

    # direct invocation
    run_config = foo_schedule()
    assert run_config == FOO_CONFIG


def test_request_based_schedule_generator():
    from dagster import Field, String

    context_without_time = build_schedule_context()

    start_date = datetime(year=2019, month=1, day=1)

    @op(config_schema={"foo": Field(String)})
    def foo_op(context):
        pass

    @job
    def foo_job():
        foo_op()

    FOO_CONFIG = {"ops": {"foo_op": {"config": {"foo": "bar"}}}}

    @schedule(
        cron_schedule="* * * * *",
        job=foo_job,
    )
    def foo_schedule(_context):
        yield RunRequest(run_key=None, run_config=FOO_CONFIG, tags={"foo": "FOO"})

    # evaluate tick
    execution_data = foo_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].run_config == FOO_CONFIG
    assert execution_data.run_requests[0].tags.get("foo") == "FOO"

    # test direct invocation
    request_generator = foo_schedule(context_without_time)
    assert inspect.isgenerator(request_generator)
    requests = list(request_generator)
    assert len(requests) == 1
    assert requests[0].run_config == FOO_CONFIG
    assert requests[0].tags.get("foo") == "FOO"


def test_request_based_schedule_generator_no_context():
    from dagster import Field, String

    context_without_time = build_schedule_context()

    start_date = datetime(year=2019, month=1, day=1)

    @op(config_schema={"foo": Field(String)})
    def foo_op(context):
        pass

    @job
    def foo_job():
        foo_op()

    FOO_CONFIG = {"ops": {"foo_op": {"config": {"foo": "bar"}}}}

    @schedule(
        cron_schedule="* * * * *",
        job=foo_job,
    )
    def foo_schedule():
        yield RunRequest(run_key=None, run_config=FOO_CONFIG, tags={"foo": "FOO"})

    # evaluate tick
    execution_data = foo_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].run_config == FOO_CONFIG
    assert execution_data.run_requests[0].tags.get("foo") == "FOO"

    # test direct invocation
    request_generator = foo_schedule()
    assert inspect.isgenerator(request_generator)
    requests = list(request_generator)
    assert len(requests) == 1
    assert requests[0].run_config == FOO_CONFIG
    assert requests[0].tags.get("foo") == "FOO"


def test_vixie_cronstring_schedule():
    context_without_time = build_schedule_context()
    start_date = datetime(year=2019, month=1, day=1)

    @op
    def foo_op(context):
        pass

    @job
    def foo_job():
        foo_op()

    @schedule(cron_schedule="@daily", job=foo_job)
    def foo_schedule():
        yield RunRequest(run_key=None, run_config={}, tags={"foo": "FOO"})

    # evaluate tick
    execution_data = foo_schedule.evaluate_tick(context_without_time)
    assert execution_data.run_requests
    assert len(execution_data.run_requests) == 1
    assert execution_data.run_requests[0].tags.get("foo") == "FOO"
