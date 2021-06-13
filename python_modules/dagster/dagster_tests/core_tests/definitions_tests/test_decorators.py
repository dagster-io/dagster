import re
from datetime import datetime, time

import pendulum
import pytest
from dagster import (
    Any,
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    DependencyDefinition,
    Field,
    InputDefinition,
    Output,
    OutputDefinition,
    PipelineDefinition,
    ScheduleDefinition,
    build_schedule_context,
    composite_solid,
    execute_pipeline,
    execute_solid,
    lambda_solid,
    pipeline,
    schedule,
    solid,
)
from dagster.core.definitions.decorators import (
    daily_schedule,
    hourly_schedule,
    monthly_schedule,
    weekly_schedule,
)
from dagster.core.utility_solids import define_stub_solid
from dagster.seven.compat.pendulum import create_pendulum_time, to_timezone
from dagster.utils.partitions import (
    DEFAULT_DATE_FORMAT,
    DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
    DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
    DEFAULT_MONTHLY_FORMAT,
)
from dateutil.relativedelta import relativedelta

# This file tests a lot of parameter name stuff, so these warnings are spurious
# pylint: disable=unused-variable, unused-argument, redefined-outer-name


def test_no_parens_solid():
    called = {}

    @lambda_solid
    def hello_world():
        called["yup"] = True

    result = execute_solid(hello_world)

    assert called["yup"]


def test_empty_solid():
    called = {}

    @lambda_solid()
    def hello_world():
        called["yup"] = True

    result = execute_solid(hello_world)

    assert called["yup"]


def test_solid():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_one_output():
    @lambda_solid
    def hello_world():
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_yield():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        yield Output(value={"foo": "bar"})

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_result_return():
    @solid(output_defs=[OutputDefinition()])
    def hello_world(_context):
        return Output(value={"foo": "bar"})

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_with_explicit_empty_outputs():
    @solid(output_defs=[])
    def hello_world(_context):
        return "foo"

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_solid(hello_world)

    assert (
        "Error in solid hello_world: Unexpectedly returned output foo of type "
        "<class 'str'>. Solid is explicitly defined to return no results."
    ) in str(exc_info.value)


def test_solid_with_implicit_single_output():
    @solid()
    def hello_world(_context):
        return "foo"

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value() == "foo"


def test_solid_return_list_instead_of_multiple_results():
    @solid(output_defs=[OutputDefinition(name="foo"), OutputDefinition(name="bar")])
    def hello_world(_context):
        return ["foo", "bar"]

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        result = execute_solid(hello_world)

    assert "unexpectedly returned output ['foo', 'bar']" in str(exc_info.value)


def test_lambda_solid_with_name():
    @lambda_solid(name="foobar")
    def hello_world():
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_with_name():
    @solid(name="foobar", output_defs=[OutputDefinition()])
    def hello_world(_context):
        return {"foo": "bar"}

    result = execute_solid(hello_world)

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_solid_with_input():
    @lambda_solid(input_defs=[InputDefinition(name="foo_to_foo")])
    def hello_world(foo_to_foo):
        return foo_to_foo

    pipeline = PipelineDefinition(
        solid_defs=[define_stub_solid("test_value", {"foo": "bar"}), hello_world],
        name="test",
        dependencies={"hello_world": {"foo_to_foo": DependencyDefinition("test_value")}},
    )

    pipeline_result = execute_pipeline(pipeline)

    result = pipeline_result.result_for_solid("hello_world")

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_lambda_solid_definition_errors():
    with pytest.raises(
        DagsterInvalidDefinitionError, match=re.escape("positional vararg parameter '*args'")
    ):

        @lambda_solid(input_defs=[InputDefinition(name="foo")])
        def vargs(foo, *args):
            pass


def test_solid_definition_errors():
    with pytest.raises(
        DagsterInvalidDefinitionError, match=re.escape("positional vararg parameter '*args'")
    ):

        @solid(input_defs=[InputDefinition(name="foo")], output_defs=[OutputDefinition()])
        def vargs(context, foo, *args):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(input_defs=[InputDefinition(name="foo")], output_defs=[OutputDefinition()])
        def wrong_name(context, bar):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(
            input_defs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
            output_defs=[OutputDefinition()],
        )
        def wrong_name_2(context, foo):
            pass

    @solid(
        input_defs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
        output_defs=[OutputDefinition()],
    )
    def valid_kwargs(context, **kwargs):
        pass

    @solid(
        input_defs=[InputDefinition(name="foo"), InputDefinition(name="bar")],
        output_defs=[OutputDefinition()],
    )
    def valid(context, foo, bar):
        pass

    @solid
    def valid_because_inference(context, foo, bar):
        pass


def test_wrong_argument_to_pipeline():
    def non_solid_func():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError, match="You have passed a lambda or function non_solid_func"
    ):
        PipelineDefinition(solid_defs=[non_solid_func], name="test")

    with pytest.raises(
        DagsterInvalidDefinitionError, match="You have passed a lambda or function <lambda>"
    ):
        PipelineDefinition(solid_defs=[lambda x: x], name="test")


def test_descriptions():
    @solid(description="foo")
    def solid_desc(_context):
        pass

    assert solid_desc.description == "foo"


def test_any_config_field():
    called = {}
    conf_value = 234

    @solid(config_schema=Field(Any))
    def hello_world(context):
        assert context.solid_config == conf_value
        called["yup"] = True

    result = execute_solid(
        hello_world, run_config={"solids": {"hello_world": {"config": conf_value}}}
    )

    assert called["yup"]


def test_solid_no_arg():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="'_noop' decorated function requires positional parameter 'context',",
    ):

        @solid(required_resource_keys={"foo"})
        def _noop():
            return

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="'_noop2' decorated function requires positional parameter 'context',",
    ):

        @solid(config_schema={"foo": str})
        def _noop2():
            return


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
    def always_skip_schedule(context):
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
    def foo_schedule(context):
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
    def foo_schedule_timezone(context):
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


def test_solid_docstring():
    @solid
    def foo_solid(_):
        """FOO_DOCSTRING"""
        return

    @lambda_solid
    def bar_solid():
        """BAR_DOCSTRING"""
        return

    @solid(name="baz")
    def baz_solid(_):
        """BAZ_DOCSTRING"""
        return

    @lambda_solid(name="quux")
    def quux_solid():
        """QUUX_DOCSTRING"""
        return

    @composite_solid
    def comp_solid():
        """COMP_DOCSTRING"""
        foo_solid()

    @pipeline
    def the_pipeline():
        """THE_DOCSTRING"""
        quux_solid()

    assert foo_solid.__doc__ == "FOO_DOCSTRING"
    assert foo_solid.__name__ == "foo_solid"
    assert bar_solid.__doc__ == "BAR_DOCSTRING"
    assert bar_solid.__name__ == "bar_solid"
    assert baz_solid.__doc__ == "BAZ_DOCSTRING"
    assert baz_solid.__name__ == "baz_solid"
    assert quux_solid.__doc__ == "QUUX_DOCSTRING"
    assert quux_solid.__name__ == "quux_solid"
    assert comp_solid.__doc__ == "COMP_DOCSTRING"
    assert comp_solid.__name__ == "comp_solid"
    assert the_pipeline.__doc__ == "THE_DOCSTRING"
    assert the_pipeline.__name__ == "the_pipeline"


def test_solid_yields_single_bare_value():
    @solid
    def return_iterator(_):
        yield 1

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape("Compute function for solid return_iterator yielded a value of type <")
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by solids must be wrapped in one of these types. If your solid has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your solid compute function. If you are already using "
            "`return`, and you expected to return a value of type <"
        )
        + r"(class|type)"
        + re.escape(
            " 'int'>, you may be inadvertently returning a generator rather than the value you "
            "expected."
        ),
    ):
        result = execute_solid(return_iterator)


def test_solid_yields_multiple_bare_values():
    @solid
    def return_iterator(_):
        yield 1
        yield 2

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape("Compute function for solid return_iterator yielded a value of type <")
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by solids must be wrapped in one of these types. If your solid has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your solid compute function. If you are already using "
            "`return`, and you expected to return a value of type <"
        )
        + r"(class|type)"
        + re.escape(
            " 'int'>, you may be inadvertently returning a generator rather than the value you "
            "expected."
        ),
    ):
        result = execute_solid(return_iterator)


def test_solid_returns_iterator():
    def iterator():
        for i in range(3):
            yield i

    @solid
    def return_iterator(_):
        return iterator()

    with pytest.raises(
        DagsterInvariantViolationError,
        match=re.escape("Compute function for solid return_iterator yielded a value of type <")
        + r"(class|type)"
        + re.escape(
            " 'int'> rather than an instance of Output, AssetMaterialization, or ExpectationResult. "
            "Values yielded by solids must be wrapped in one of these types. If your solid has a "
            "single output and yields no other events, you may want to use `return` instead of "
            "`yield` in the body of your solid compute function. If you are already using "
            "`return`, and you expected to return a value of type <"
        )
        + r"(class|type)"
        + re.escape(
            " 'int'>, you may be inadvertently returning a generator rather than the value you "
            "expected."
        ),
    ):
        result = execute_solid(return_iterator)


def test_input_default():
    @lambda_solid
    def foo(bar="ok"):
        return bar

    result = execute_solid(foo)
    assert result.output_value() == "ok"
