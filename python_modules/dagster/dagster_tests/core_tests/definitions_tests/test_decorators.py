# encoding: utf-8
# py27 compat

import re
from datetime import datetime, time

import pytest
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

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
from dagster.core.definitions.schedule import ScheduleExecutionContext
from dagster.core.test_utils import instance_for_test
from dagster.core.utility_solids import define_stub_solid

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
    ) in str(exc_info.value) or (
        "Error in solid hello_world: Unexpectedly returned output foo of type "
        "<type 'str'>. Solid is explicitly defined to return no results."
    ) in str(
        exc_info.value
    )  # py2


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
        dependencies={"hello_world": {"foo_to_foo": DependencyDefinition("test_value")}},
    )

    pipeline_result = execute_pipeline(pipeline)

    result = pipeline_result.result_for_solid("hello_world")

    assert result.success
    assert result.output_value()["foo"] == "bar"


def test_lambda_solid_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError, match="positional vararg"):

        @lambda_solid(input_defs=[InputDefinition(name="foo")])
        def vargs(foo, *args):
            pass


def test_solid_definition_errors():
    with pytest.raises(DagsterInvalidDefinitionError, match="positional vararg"):

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

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(input_defs=[InputDefinition(name="foo")], output_defs=[OutputDefinition()])
        def no_context(foo):
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @solid(input_defs=[InputDefinition(name="foo")], output_defs=[OutputDefinition()])
        def extras(_context, foo, bar):
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
        PipelineDefinition(solid_defs=[non_solid_func])

    with pytest.raises(
        DagsterInvalidDefinitionError, match="You have passed a lambda or function <lambda>"
    ):
        PipelineDefinition(solid_defs=[lambda x: x])


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
        match="does not have required positional parameter 'context'.",
    ):

        @solid
        def noop():
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
                    context.scheduled_execution_time_utc.isoformat()
                    if context.scheduled_execution_time_utc
                    else ""
                )
            )
        }

    with instance_for_test() as instance:
        context_without_time = ScheduleExecutionContext(instance, None)

        execution_time = datetime(year=2019, month=2, day=27)

        context_with_time = ScheduleExecutionContext(instance, execution_time)

        assert echo_time_schedule.get_run_config(context_without_time) == {"echo_time": ""}

        assert echo_time_schedule.get_run_config(context_with_time) == {
            "echo_time": execution_time.isoformat()
        }


def test_schedule_decorators_sanity():
    @solid
    def do_nothing(_):
        pass

    @pipeline
    def foo_pipeline():
        do_nothing()

    @monthly_schedule(
        pipeline_name="foo_pipeline",
        execution_day_of_month=3,
        start_date=datetime(year=2019, month=1, day=1),
    )
    def monthly_foo_schedule():
        return {}

    @weekly_schedule(
        pipeline_name="foo_pipeline",
        execution_day_of_week=1,
        start_date=datetime(year=2019, month=1, day=1),
    )
    def weekly_foo_schedule():
        return {}

    @daily_schedule(
        pipeline_name="foo_pipeline", start_date=datetime(year=2019, month=1, day=1),
    )
    def daily_foo_schedule():
        return {}

    @hourly_schedule(
        pipeline_name="foo_pipeline", start_date=datetime(year=2019, month=1, day=1),
    )
    def hourly_foo_schedule():
        return {}


def _check_partitions(partition_schedule_def, expected_num_partitions, expected_relative_delta):
    partitions = partition_schedule_def.get_partition_set().partition_fn()
    assert len(partitions) == expected_num_partitions

    for index, partition in enumerate(partitions):
        assert partition.value == partitions[0].value + (index * expected_relative_delta)


@freeze_time("2019-02-27 00:01:01")
def test_partitions_for_hourly_schedule_decorators():
    with instance_for_test() as instance:

        context_without_time = ScheduleExecutionContext(instance, None)

        @hourly_schedule(
            pipeline_name="foo_pipeline",
            start_date=datetime(year=2019, month=1, day=1, minute=1),
            execution_time=time(hour=0, minute=25),
        )
        def hourly_foo_schedule(hourly_time):
            return {"hourly_time": hourly_time.isoformat()}

        _check_partitions(hourly_foo_schedule, 24 * (31 + 26), relativedelta(hours=1))

        assert hourly_foo_schedule.get_run_config(context_without_time) == {
            "hourly_time": datetime(year=2019, month=2, day=26, hour=23, minute=1).isoformat()
        }
        assert hourly_foo_schedule.should_execute(context_without_time)

        # time that's invalid since it corresponds to a partition that hasn't happened yet
        # should still generate run config, but should not execute
        execution_time_with_invalid_partition = datetime(
            year=2019, month=2, day=27, hour=3, minute=25
        )
        context_with_invalid_time = ScheduleExecutionContext(
            instance, execution_time_with_invalid_partition
        )

        assert hourly_foo_schedule.get_run_config(context_with_invalid_time) == {
            "hourly_time": datetime(year=2019, month=2, day=27, hour=2, minute=1).isoformat()
        }

        assert not hourly_foo_schedule.should_execute(context_with_invalid_time)

        valid_time = datetime(year=2019, month=1, day=27, hour=1, minute=25)
        context_with_valid_time = ScheduleExecutionContext(instance, valid_time)

        assert hourly_foo_schedule.get_run_config(context_with_valid_time) == {
            "hourly_time": datetime(year=2019, month=1, day=27, hour=0, minute=1).isoformat()
        }

        assert hourly_foo_schedule.should_execute(context_with_valid_time)


@freeze_time("2019-02-27 00:01:01")
def test_partitions_for_daily_schedule_decorators():
    with instance_for_test() as instance:

        context_without_time = ScheduleExecutionContext(instance, None)

        @daily_schedule(
            pipeline_name="foo_pipeline",
            start_date=datetime(year=2019, month=1, day=1),
            execution_time=time(hour=9, minute=30),
        )
        def daily_foo_schedule(daily_time):
            return {"daily_time": daily_time.isoformat()}

        _check_partitions(daily_foo_schedule, (31 + 26), relativedelta(days=1))

        valid_daily_time = datetime(year=2019, month=1, day=27, hour=9, minute=30)
        context_with_valid_time = ScheduleExecutionContext(instance, valid_daily_time)

        assert daily_foo_schedule.get_run_config(context_with_valid_time) == {
            "daily_time": datetime(year=2019, month=1, day=26).isoformat()
        }
        assert daily_foo_schedule.should_execute(context_with_valid_time)

        assert daily_foo_schedule.get_run_config(context_without_time) == {
            "daily_time": datetime(year=2019, month=2, day=26).isoformat()
        }
        assert daily_foo_schedule.should_execute(context_without_time)


@freeze_time("2019-02-27 00:01:01")
def test_partitions_for_weekly_schedule_decorators():
    with instance_for_test() as instance:
        context_without_time = ScheduleExecutionContext(instance, None)

        @weekly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_week=2,
            start_date=datetime(year=2019, month=1, day=1),
            execution_time=time(9, 30),
        )
        def weekly_foo_schedule(weekly_time):
            return {"weekly_time": weekly_time.isoformat()}

        valid_weekly_time = datetime(year=2019, month=1, day=30, hour=9, minute=30)
        context_with_valid_time = ScheduleExecutionContext(instance, valid_weekly_time)

        assert weekly_foo_schedule.get_run_config(context_with_valid_time) == {
            "weekly_time": datetime(year=2019, month=1, day=22).isoformat()
        }

        assert weekly_foo_schedule.should_execute(context_with_valid_time)

        assert weekly_foo_schedule.get_run_config(context_without_time) == {
            "weekly_time": datetime(year=2019, month=2, day=19).isoformat()
        }
        assert weekly_foo_schedule.should_execute(context_without_time)

        _check_partitions(weekly_foo_schedule, 8, relativedelta(weeks=1))


@freeze_time("2019-02-27 00:01:01")
def test_partitions_for_monthly_schedule_decorators():
    with instance_for_test() as instance:
        context_without_time = ScheduleExecutionContext(instance, None)

        @monthly_schedule(
            pipeline_name="foo_pipeline",
            execution_day_of_month=3,
            start_date=datetime(year=2019, month=1, day=1),
            execution_time=time(9, 30),
        )
        def monthly_foo_schedule(monthly_time):
            return {"monthly_time": monthly_time.isoformat()}

        valid_monthly_time = datetime(year=2019, month=2, day=3, hour=9, minute=30)
        context_with_valid_time = ScheduleExecutionContext(instance, valid_monthly_time)

        assert monthly_foo_schedule.get_run_config(
            ScheduleExecutionContext(instance, valid_monthly_time)
        ) == {"monthly_time": datetime(year=2019, month=1, day=1).isoformat()}
        assert monthly_foo_schedule.should_execute(context_with_valid_time)

        assert monthly_foo_schedule.get_run_config(context_without_time) == {
            "monthly_time": datetime(year=2019, month=1, day=1).isoformat()
        }
        assert monthly_foo_schedule.should_execute(context_without_time)

        _check_partitions(monthly_foo_schedule, 1, relativedelta(months=1))


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
