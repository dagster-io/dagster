import inspect
import json
import re
from datetime import datetime

import pendulum
import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    RunRequest,
    ScheduleDefinition,
    build_schedule_context,
    job,
    op,
    schedule,
    validate_run_config,
)
from dagster._utils import merge_dicts

# This file tests a lot of parameter name stuff, so these warnings are spurious
# pylint: disable=unused-variable, unused-argument, redefined-outer-name


def test_scheduler():
    def define_schedules():
        return [
            ScheduleDefinition(
                name="my_schedule",
                cron_schedule="* * * * *",
                job_name="test_job",
                run_config={},
            )
        ]

    @schedule(cron_schedule="* * * * *", job_name="foo_job")
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
        cron_schedule="* * * * *",
        job_name="foo_job",
        should_execute=lambda x: False,
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
    @op
    def do_nothing(_):
        pass

    @job
    def foo_job():
        do_nothing()

    @schedule(cron_schedule="* * * * *", job_name="foo_job")
    def foo_schedule():
        """Fake doc block"""
        return {}

    # Ensure that schedule definition inherits properties from wrapped fxn
    assert foo_schedule.__doc__ == """Fake doc block"""

    assert not foo_schedule.execution_timezone

    @schedule(
        cron_schedule="* * * * *",
        job_name="foo_job",
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

        @schedule(
            cron_schedule="* * * * *",
            job_name="foo_job",
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


def test_schedule_decorators_bad():
    @op
    def do_nothing(_):
        pass

    @job
    def foo_job():
        do_nothing()

    with pytest.raises(DagsterInvalidDefinitionError, match="invalid cron schedule"):

        @schedule(cron_schedule="", job_name="foo_job")
        def bad_cron_string(context):
            return {}

    with pytest.raises(DagsterInvalidDefinitionError, match="invalid cron schedule"):

        @schedule(cron_schedule="bad_schedule_two", job_name="foo_job")
        def bad_cron_string_two(context):
            return {}

    with pytest.raises(DagsterInvalidDefinitionError, match="invalid cron schedule"):

        @schedule(cron_schedule="* * * * * *", job_name="foo_job")
        def bad_cron_string_three(context):
            return {}


def test_schedule_with_nested_tags():

    nested_tags = {"foo": {"bar": "baz"}}

    @schedule(cron_schedule="* * * * *", job_name="foo_job", tags=nested_tags)
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
