from dagster_tests.utils import FilesytemTestScheduler

from dagster import Partition, PartitionSetDefinition, ScheduleDefinition, schedules
from dagster.core.definitions.partition import last_empty_partition

integer_partition_set = PartitionSetDefinition(
    name='scheduled_integer_partitions',
    pipeline_name='no_config_pipeline',
    partition_fn=lambda: [Partition(x) for x in range(1, 10)],
    environment_dict_fn_for_partition=lambda _partition: {"storage": {"filesystem": {}}},
    tags_fn_for_partition=lambda _partition: {"test": "1234"},
)


@schedules(scheduler=FilesytemTestScheduler)
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

    no_config_pipeline_hourly_schedule_with_schedule_id_tag = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule_with_schedule_id_tag",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": {}}},
        tags={"dagster/schedule_id": "1234"},
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

    return [
        no_config_pipeline_hourly_schedule,
        no_config_pipeline_hourly_schedule_with_schedule_id_tag,
        no_config_pipeline_hourly_schedule_with_config_fn,
        no_config_should_execute,
        dynamic_config,
        partition_based,
        partition_based_custom_selector,
    ]
