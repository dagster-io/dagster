import datetime
import warnings

import pendulum
from dagster import check
from dagster.core.definitions.partition import PartitionSetDefinition
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils.partitions import (
    DEFAULT_DATE_FORMAT,
    DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE,
    DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE,
    DEFAULT_MONTHLY_FORMAT,
    create_offset_partition_selector,
    schedule_partition_range,
)

from ..mode import DEFAULT_MODE_NAME
from ..schedule import ScheduleDefinition

# Error messages are long
# pylint: disable=C0301


def schedule(
    cron_schedule,
    pipeline_name,
    name=None,
    tags=None,
    tags_fn=None,
    solid_selection=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
    execution_timezone=None,
):
    """Create a schedule.

    The decorated function will be called as the ``run_config_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        cron_schedule (str): A valid cron string specifying when the schedule will run, e.g.,
            ``'45 23 * * 6'`` for a schedule that runs at 11:45 PM every Saturday.
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        name (Optional[str]): The name of the schedule to create.
        tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the scheduled runs.
        tags_fn (Optional[Callable[[ScheduleExecutionContext], Optional[Dict[str, str]]]]): A function
            that generates tags to attach to the schedules runs. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a dictionary of tags (string
            key-value pairs). You may set only one of ``tags`` and ``tags_fn``.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the schedule runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[[ScheduleExecutionContext], bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
        execution_timezone (Optional[str]): Timezone in which the schedule should run. Only works
            with DagsterDaemonScheduler, and must be set when using that scheduler.
    """

    def inner(fn):
        check.callable_param(fn, "fn")

        schedule_name = name or fn.__name__

        return ScheduleDefinition(
            name=schedule_name,
            cron_schedule=cron_schedule,
            pipeline_name=pipeline_name,
            run_config_fn=fn,
            tags=tags,
            tags_fn=tags_fn,
            solid_selection=solid_selection,
            mode=mode,
            should_execute=should_execute,
            environment_vars=environment_vars,
            execution_timezone=execution_timezone,
        )

    return inner


def monthly_schedule(
    pipeline_name,
    start_date,
    name=None,
    execution_day_of_month=1,
    execution_time=datetime.time(0, 0),
    tags_fn_for_date=None,
    solid_selection=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
    end_date=None,
    execution_timezone=None,
):
    """Create a schedule that runs monthly.

    The decorated function will be called as the ``run_config_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        start_date (datetime.datetime): The date from which to run the schedule.
        name (Optional[str]): The name of the schedule to create.
        execution_day_of_month (int): The day of the month on which to run the schedule (must be
            between 0 and 31).
        execution_time (datetime.time): The time at which to execute the schedule.
        tags_fn_for_date (Optional[Callable[[datetime.datetime], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes the date of the
            schedule run and returns a dictionary of tags (string key-value pairs).
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the schedule runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
        end_date (Optional[datetime.datetime]): The last time to run the schedule to, defaults to
            current time.
        execution_timezone (Optional[str]): Timezone in which the schedule should run. Only works
            with DagsterDaemonScheduler, and must be set when using that scheduler.
    """
    check.opt_str_param(name, "name")
    check.inst_param(start_date, "start_date", datetime.datetime)
    check.opt_inst_param(end_date, "end_date", datetime.datetime)
    check.opt_callable_param(tags_fn_for_date, "tags_fn_for_date")
    check.opt_nullable_list_param(solid_selection, "solid_selection", of_type=str)
    mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)
    check.opt_callable_param(should_execute, "should_execute")
    check.opt_dict_param(environment_vars, "environment_vars", key_type=str, value_type=str)
    check.str_param(pipeline_name, "pipeline_name")
    check.int_param(execution_day_of_month, "execution_day")
    check.inst_param(execution_time, "execution_time", datetime.time)
    check.opt_str_param(execution_timezone, "execution_timezone")

    if (
        start_date.day != 1
        or start_date.hour != 0
        or start_date.minute != 0
        or start_date.second != 0
    ):
        warnings.warn(
            "`start_date` must be at the beginning of the first day of the month for a monthly "
            "schedule. Use `execution_day_of_month` and `execution_time` to execute the schedule "
            "at a specific time within the month. For example, to run the schedule at 3AM on the "
            "23rd of each month starting in October, your schedule definition would look like:"
            """
@monthly_schedule(
    start_date=datetime.datetime(2020, 10, 1),
    execution_day_of_month=23,
    execution_time=datetime.time(3, 0)
):
def my_schedule_definition(_):
    ...
"""
        )

    if execution_day_of_month <= 0 or execution_day_of_month > 31:
        raise DagsterInvalidDefinitionError(
            "`execution_day_of_month={}` is not valid for monthly schedule. Execution day must be "
            "between 1 and 31".format(execution_day_of_month)
        )

    cron_schedule = "{minute} {hour} {day} * *".format(
        minute=execution_time.minute, hour=execution_time.hour, day=execution_day_of_month
    )

    fmt = DEFAULT_MONTHLY_FORMAT

    execution_time_to_partition_fn = (
        lambda d: pendulum.instance(d)
        .replace(hour=0, minute=0)
        .subtract(months=1, days=execution_day_of_month - 1)
    )

    partition_fn = schedule_partition_range(
        start_date,
        end=end_date,
        cron_schedule=cron_schedule,
        fmt=fmt,
        timezone=execution_timezone,
        execution_time_to_partition_fn=execution_time_to_partition_fn,
    )

    def inner(fn):
        check.callable_param(fn, "fn")

        schedule_name = name or fn.__name__

        tags_fn_for_partition_value = lambda partition: {}
        if tags_fn_for_date:
            tags_fn_for_partition_value = lambda partition: tags_fn_for_date(partition.value)

        partition_set = PartitionSetDefinition(
            name="{}_partitions".format(schedule_name),
            pipeline_name=pipeline_name,
            partition_fn=partition_fn,
            run_config_fn_for_partition=lambda partition: fn(partition.value),
            solid_selection=solid_selection,
            tags_fn_for_partition=tags_fn_for_partition_value,
            mode=mode,
        )

        return partition_set.create_schedule_definition(
            schedule_name,
            cron_schedule,
            should_execute=should_execute,
            environment_vars=environment_vars,
            partition_selector=create_offset_partition_selector(
                execution_time_to_partition_fn=execution_time_to_partition_fn
            ),
            execution_timezone=execution_timezone,
        )

    return inner


def weekly_schedule(
    pipeline_name,
    start_date,
    name=None,
    execution_day_of_week=0,
    execution_time=datetime.time(0, 0),
    tags_fn_for_date=None,
    solid_selection=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
    end_date=None,
    execution_timezone=None,
):
    """Create a schedule that runs weekly.

    The decorated function will be called as the ``run_config_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        start_date (datetime.datetime): The date from which to run the schedule.
        name (Optional[str]): The name of the schedule to create.
        execution_day_of_week (int): The day of the week on which to run the schedule. Must be
            between 0 (Sunday) and 6 (Saturday).
        execution_time (datetime.time): The time at which to execute the schedule.
        tags_fn_for_date (Optional[Callable[[datetime.datetime], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes the date of the
            schedule run and returns a dictionary of tags (string key-value pairs).
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the schedule runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
        end_date (Optional[datetime.datetime]): The last time to run the schedule to, defaults to
            current time.
        execution_timezone (Optional[str]): Timezone in which the schedule should run. Only works
            with DagsterDaemonScheduler, and must be set when using that scheduler.
    """
    check.opt_str_param(name, "name")
    check.inst_param(start_date, "start_date", datetime.datetime)
    check.opt_inst_param(end_date, "end_date", datetime.datetime)
    check.opt_callable_param(tags_fn_for_date, "tags_fn_for_date")
    check.opt_nullable_list_param(solid_selection, "solid_selection", of_type=str)
    mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)
    check.opt_callable_param(should_execute, "should_execute")
    check.opt_dict_param(environment_vars, "environment_vars", key_type=str, value_type=str)
    check.str_param(pipeline_name, "pipeline_name")
    check.int_param(execution_day_of_week, "execution_day_of_week")
    check.inst_param(execution_time, "execution_time", datetime.time)
    check.opt_str_param(execution_timezone, "execution_timezone")

    if start_date.hour != 0 or start_date.minute != 0 or start_date.second != 0:
        warnings.warn(
            "`start_date` must be at the beginning of a day for a weekly schedule. "
            "Use `execution_time` to execute the schedule at a specific time of day. For example, "
            "to run the schedule at 3AM each Tuesday starting on 10/20/2020, your schedule "
            "definition would look like:"
            """
@weekly_schedule(
    start_date=datetime.datetime(2020, 10, 20),
    execution_day_of_week=1,
    execution_time=datetime.time(3, 0)
):
def my_schedule_definition(_):
    ...
"""
        )

    if execution_day_of_week < 0 or execution_day_of_week >= 7:
        raise DagsterInvalidDefinitionError(
            "`execution_day_of_week={}` is not valid for weekly schedule. Execution day must be "
            "between 0 [Sunday] and 6 [Saturday]".format(execution_day_of_week)
        )

    cron_schedule = "{minute} {hour} * * {day}".format(
        minute=execution_time.minute, hour=execution_time.hour, day=execution_day_of_week
    )

    fmt = DEFAULT_DATE_FORMAT

    day_difference = (execution_day_of_week - (start_date.weekday() + 1)) % 7

    execution_time_to_partition_fn = (
        lambda d: pendulum.instance(d)
        .replace(hour=0, minute=0)
        .subtract(weeks=1, days=day_difference)
    )

    partition_fn = schedule_partition_range(
        start_date,
        end=end_date,
        cron_schedule=cron_schedule,
        fmt=fmt,
        timezone=execution_timezone,
        execution_time_to_partition_fn=execution_time_to_partition_fn,
    )

    def inner(fn):
        check.callable_param(fn, "fn")

        schedule_name = name or fn.__name__

        tags_fn_for_partition_value = lambda partition: {}
        if tags_fn_for_date:
            tags_fn_for_partition_value = lambda partition: tags_fn_for_date(partition.value)

        partition_set = PartitionSetDefinition(
            name="{}_partitions".format(schedule_name),
            pipeline_name=pipeline_name,
            partition_fn=partition_fn,
            run_config_fn_for_partition=lambda partition: fn(partition.value),
            solid_selection=solid_selection,
            tags_fn_for_partition=tags_fn_for_partition_value,
            mode=mode,
        )

        return partition_set.create_schedule_definition(
            schedule_name,
            cron_schedule,
            should_execute=should_execute,
            environment_vars=environment_vars,
            partition_selector=create_offset_partition_selector(
                execution_time_to_partition_fn=execution_time_to_partition_fn,
            ),
            execution_timezone=execution_timezone,
        )

    return inner


def daily_schedule(
    pipeline_name,
    start_date,
    name=None,
    execution_time=datetime.time(0, 0),
    tags_fn_for_date=None,
    solid_selection=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
    end_date=None,
    execution_timezone=None,
):
    """Create a schedule that runs daily.

    The decorated function will be called as the ``run_config_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        start_date (datetime.datetime): The date from which to run the schedule.
        name (Optional[str]): The name of the schedule to create.
        execution_time (datetime.time): The time at which to execute the schedule.
        tags_fn_for_date (Optional[Callable[[datetime.datetime], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes the date of the
            schedule run and returns a dictionary of tags (string key-value pairs).
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the schedule runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
        end_date (Optional[datetime.datetime]): The last time to run the schedule to, defaults to
            current time.
        execution_timezone (Optional[str]): Timezone in which the schedule should run. Only works
            with DagsterDaemonScheduler, and must be set when using that scheduler.
    """
    check.str_param(pipeline_name, "pipeline_name")
    check.inst_param(start_date, "start_date", datetime.datetime)
    check.opt_str_param(name, "name")
    check.inst_param(execution_time, "execution_time", datetime.time)
    check.opt_inst_param(end_date, "end_date", datetime.datetime)
    check.opt_callable_param(tags_fn_for_date, "tags_fn_for_date")
    check.opt_nullable_list_param(solid_selection, "solid_selection", of_type=str)
    mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)
    check.opt_callable_param(should_execute, "should_execute")
    check.opt_dict_param(environment_vars, "environment_vars", key_type=str, value_type=str)
    check.opt_str_param(execution_timezone, "execution_timezone")

    if start_date.hour != 0 or start_date.minute != 0 or start_date.second != 0:
        warnings.warn(
            "`start_date` must be at the beginning of a day for a daily schedule. "
            "Use `execution_time` to execute the schedule at a specific time of day. For example, "
            "to run the schedule at 3AM each day starting on 10/20/2020, your schedule "
            "definition would look like:"
            """
@daily_schedule(
    start_date=datetime.datetime(2020, 10, 20),
    execution_time=datetime.time(3, 0)
):
def my_schedule_definition(_):
    ...
"""
        )

    cron_schedule = "{minute} {hour} * * *".format(
        minute=execution_time.minute, hour=execution_time.hour
    )

    fmt = DEFAULT_DATE_FORMAT

    execution_time_to_partition_fn = (
        lambda d: pendulum.instance(d)
        .replace(hour=0, minute=0)
        .subtract(
            days=1,
        )
    )

    partition_fn = schedule_partition_range(
        start_date,
        end=end_date,
        cron_schedule=cron_schedule,
        fmt=fmt,
        timezone=execution_timezone,
        execution_time_to_partition_fn=execution_time_to_partition_fn,
    )

    def inner(fn):
        check.callable_param(fn, "fn")

        schedule_name = name or fn.__name__

        tags_fn_for_partition_value = lambda partition: {}
        if tags_fn_for_date:
            tags_fn_for_partition_value = lambda partition: tags_fn_for_date(partition.value)

        partition_set = PartitionSetDefinition(
            name="{}_partitions".format(schedule_name),
            pipeline_name=pipeline_name,
            partition_fn=partition_fn,
            run_config_fn_for_partition=lambda partition: fn(partition.value),
            solid_selection=solid_selection,
            tags_fn_for_partition=tags_fn_for_partition_value,
            mode=mode,
        )

        return partition_set.create_schedule_definition(
            schedule_name,
            cron_schedule,
            should_execute=should_execute,
            environment_vars=environment_vars,
            partition_selector=create_offset_partition_selector(
                execution_time_to_partition_fn=execution_time_to_partition_fn,
            ),
            execution_timezone=execution_timezone,
        )

    return inner


def hourly_schedule(
    pipeline_name,
    start_date,
    name=None,
    execution_time=datetime.time(0, 0),
    tags_fn_for_date=None,
    solid_selection=None,
    mode="default",
    should_execute=None,
    environment_vars=None,
    end_date=None,
    execution_timezone=None,
):
    """Create a schedule that runs hourly.

    The decorated function will be called as the ``run_config_fn`` of the underlying
    :py:class:`~dagster.ScheduleDefinition` and should take a
    :py:class:`~dagster.ScheduleExecutionContext` as its only argument, returning the environment
    dict for the scheduled execution.

    Args:
        pipeline_name (str): The name of the pipeline to execute when the schedule runs.
        start_date (datetime.datetime): The date from which to run the schedule.
        name (Optional[str]): The name of the schedule to create. By default, this will be the name
            of the decorated function.
        execution_time (datetime.time): The time at which to execute the schedule. Only the minutes
            component will be respected -- the hour should be 0, and will be ignored if it is not 0.
        tags_fn_for_date (Optional[Callable[[datetime.datetime], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes the date of the
            schedule run and returns a dictionary of tags (string key-value pairs).
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the schedule runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The pipeline mode in which to execute this schedule.
            (Default: 'default')
        should_execute (Optional[Callable[ScheduleExecutionContext, bool]]): A function that runs at
            schedule execution tie to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleExecutionContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[Dict[str, str]]): Any environment variables to set when executing
            the schedule.
        end_date (Optional[datetime.datetime]): The last time to run the schedule to, defaults to
            current time.
        execution_timezone (Optional[str]): Timezone in which the schedule should run. Only works
            with DagsterDaemonScheduler, and must be set when using that scheduler.
    """
    check.opt_str_param(name, "name")
    check.inst_param(start_date, "start_date", datetime.datetime)
    check.opt_inst_param(end_date, "end_date", datetime.datetime)
    check.opt_callable_param(tags_fn_for_date, "tags_fn_for_date")
    check.opt_nullable_list_param(solid_selection, "solid_selection", of_type=str)
    mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)
    check.opt_callable_param(should_execute, "should_execute")
    check.opt_dict_param(environment_vars, "environment_vars", key_type=str, value_type=str)
    check.str_param(pipeline_name, "pipeline_name")
    check.inst_param(execution_time, "execution_time", datetime.time)
    check.opt_str_param(execution_timezone, "execution_timezone")

    if start_date.minute != 0 or start_date.second != 0:
        warnings.warn(
            "`start_date` must be at the beginning of the hour for an hourly schedule. "
            "Use `execution_time` to execute the schedule at a specific time within the hour. For "
            "example, to run the schedule each hour at 15 minutes past the hour starting at 3AM "
            "on 10/20/2020, your schedule definition would look like:"
            """
@hourly_schedule(
    start_date=datetime.datetime(2020, 10, 20, 3),
    execution_time=datetime.time(0, 15)
):
def my_schedule_definition(_):
    ...
"""
        )

    if execution_time.hour != 0:
        warnings.warn(
            "Hourly schedule {schedule_name} created with:\n"
            "\tschedule_time=datetime.time(hour={hour}, minute={minute}, ...)."
            "Since this is an hourly schedule, the hour parameter will be ignored and the schedule "
            "will run on the {minute} mark for the previous hour interval. Replace "
            "datetime.time(hour={hour}, minute={minute}, ...) with "
            "datetime.time(minute={minute}, ...) to fix this warning."
        )

    cron_schedule = "{minute} * * * *".format(minute=execution_time.minute)

    fmt = (
        DEFAULT_HOURLY_FORMAT_WITH_TIMEZONE
        if execution_timezone
        else DEFAULT_HOURLY_FORMAT_WITHOUT_TIMEZONE
    )

    execution_time_to_partition_fn = lambda d: pendulum.instance(d).subtract(
        hours=1, minutes=(execution_time.minute - start_date.minute) % 60
    )

    partition_fn = schedule_partition_range(
        start_date,
        end=end_date,
        cron_schedule=cron_schedule,
        fmt=fmt,
        timezone=execution_timezone,
        execution_time_to_partition_fn=execution_time_to_partition_fn,
    )

    def inner(fn):
        check.callable_param(fn, "fn")

        schedule_name = name or fn.__name__

        tags_fn_for_partition_value = lambda partition: {}
        if tags_fn_for_date:
            tags_fn_for_partition_value = lambda partition: tags_fn_for_date(partition.value)

        partition_set = PartitionSetDefinition(
            name="{}_partitions".format(schedule_name),
            pipeline_name=pipeline_name,
            partition_fn=partition_fn,
            run_config_fn_for_partition=lambda partition: fn(partition.value),
            solid_selection=solid_selection,
            tags_fn_for_partition=tags_fn_for_partition_value,
            mode=mode,
        )

        return partition_set.create_schedule_definition(
            schedule_name,
            cron_schedule,
            should_execute=should_execute,
            environment_vars=environment_vars,
            partition_selector=create_offset_partition_selector(
                execution_time_to_partition_fn=execution_time_to_partition_fn,
            ),
            execution_timezone=execution_timezone,
        )

    return inner
