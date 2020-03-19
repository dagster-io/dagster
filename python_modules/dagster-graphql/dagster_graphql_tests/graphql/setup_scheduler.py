import datetime

from dagster import (
    Partition,
    PartitionSetDefinition,
    ScheduleDefinition,
    daily_schedule,
    hourly_schedule,
    monthly_schedule,
    schedules,
    weekly_schedule,
)
from dagster.core.definitions.partition import last_empty_partition

integer_partition_set = PartitionSetDefinition(
    name='scheduled_integer_partitions',
    pipeline_name='no_config_pipeline',
    partition_fn=lambda: [Partition(x) for x in range(1, 10)],
    environment_dict_fn_for_partition=lambda _partition: {"storage": {"filesystem": {}}},
    tags_fn_for_partition=lambda _partition: {"test": "1234"},
)


@schedules
def define_scheduler():

    no_config_pipeline_hourly_schedule = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": {}}},
    )

    no_config_pipeline_hourly_schedule_with_config_fn = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule_with_config_fn",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict_fn=lambda _context: {"storage": {"filesystem": {}}},
    )

    no_config_should_execute = ScheduleDefinition(
        name="no_config_should_execute",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": {}}},
        should_execute=lambda _context: False,
    )

    dynamic_config = ScheduleDefinition(
        name="dynamic_config",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict_fn=lambda _context: {"storage": {"filesystem": {}}},
    )

    partition_based = integer_partition_set.create_schedule_definition(
        schedule_name="partition_based", cron_schedule="0 0 * * *",
    )

    partition_based_custom_selector = integer_partition_set.create_schedule_definition(
        schedule_name="partition_based_custom_selector",
        cron_schedule="0 0 * * *",
        partition_selector=last_empty_partition,
    )

    @daily_schedule(
        pipeline_name='no_config_pipeline',
        start_date=datetime.datetime.now() - datetime.timedelta(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
    )
    def partition_based_decorator(_date):
        return {"storage": {"filesystem": {}}}

    @daily_schedule(
        pipeline_name='multi_mode_with_loggers',
        start_date=datetime.datetime.now() - datetime.timedelta(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
        mode='foo_mode',
    )
    def partition_based_multi_mode_decorator(_date):
        return {"storage": {"filesystem": {}}}

    @hourly_schedule(
        pipeline_name='no_config_chain_pipeline',
        start_date=datetime.datetime.now() - datetime.timedelta(days=1),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=2)).time(),
        solid_subset=['return_foo'],
    )
    def solid_subset_hourly_decorator(_date):
        return {"storage": {"filesystem": {}}}

    @daily_schedule(
        pipeline_name='no_config_chain_pipeline',
        start_date=datetime.datetime.now() - datetime.timedelta(days=2),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=3)).time(),
        solid_subset=['return_foo'],
    )
    def solid_subset_daily_decorator(_date):
        return {"storage": {"filesystem": {}}}

    @monthly_schedule(
        pipeline_name='no_config_chain_pipeline',
        start_date=datetime.datetime.now() - datetime.timedelta(days=100),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=4)).time(),
        solid_subset=['return_foo'],
    )
    def solid_subset_monthly_decorator(_date):
        return {"storage": {"filesystem": {}}}

    @weekly_schedule(
        pipeline_name='no_config_chain_pipeline',
        start_date=datetime.datetime.now() - datetime.timedelta(days=50),
        execution_time=(datetime.datetime.now() + datetime.timedelta(hours=5)).time(),
        solid_subset=['return_foo'],
    )
    def solid_subset_weekly_decorator(_date):
        return {"storage": {"filesystem": {}}}

    # Schedules for testing the user error boundary
    @daily_schedule(
        pipeline_name='no_config_pipeline',
        start_date=datetime.datetime.now() - datetime.timedelta(days=1),
        should_execute=lambda _: asdf,  # pylint: disable=undefined-variable
    )
    def should_execute_error_schedule(_date):
        return {"storage": {"filesystem": {}}}

    @daily_schedule(
        pipeline_name='no_config_pipeline',
        start_date=datetime.datetime.now() - datetime.timedelta(days=1),
        tags_fn_for_date=lambda _: asdf,  # pylint: disable=undefined-variable
    )
    def tags_error_schedule(_date):
        return {"storage": {"filesystem": {}}}

    @daily_schedule(
        pipeline_name='no_config_pipeline',
        start_date=datetime.datetime.now() - datetime.timedelta(days=1),
    )
    def environment_dict_error_schedule(_date):
        return asdf  # pylint: disable=undefined-variable

    tagged_pipeline_schedule = ScheduleDefinition(
        name="tagged_pipeline_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="tagged_pipeline",
        environment_dict={"storage": {"filesystem": {}}},
    )

    tagged_pipeline_override_schedule = ScheduleDefinition(
        name="tagged_pipeline_override_schedule",
        cron_schedule="0 0 * * *",
        pipeline_name="tagged_pipeline",
        environment_dict={"storage": {"filesystem": {}}},
        tags={'foo': 'notbar'},
    )

    return [
        environment_dict_error_schedule,
        no_config_pipeline_hourly_schedule,
        no_config_pipeline_hourly_schedule_with_config_fn,
        no_config_should_execute,
        dynamic_config,
        partition_based,
        partition_based_custom_selector,
        partition_based_decorator,
        partition_based_multi_mode_decorator,
        solid_subset_hourly_decorator,
        solid_subset_daily_decorator,
        solid_subset_monthly_decorator,
        solid_subset_weekly_decorator,
        should_execute_error_schedule,
        tagged_pipeline_schedule,
        tagged_pipeline_override_schedule,
        tags_error_schedule,
    ]
