from dagster_tests.utils import FilesytemTestScheduler

from dagster import ScheduleDefinition, schedules


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
        environment_dict_fn=lambda: {"storage": {"filesystem": {}}},
    )

    no_config_pipeline_hourly_schedule_with_schedule_id_tag = ScheduleDefinition(
        name="no_config_pipeline_hourly_schedule_with_schedule_id_tag",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": {}}},
        tags=[{"key": "dagster/schedule_id", "value": "1234"}],
    )

    no_config_should_execute = ScheduleDefinition(
        name="no_config_should_execute",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict={"storage": {"filesystem": {}}},
        should_execute=lambda: False,
    )

    dynamic_config = ScheduleDefinition(
        name="dynamic_config",
        cron_schedule="0 0 * * *",
        pipeline_name="no_config_pipeline",
        environment_dict_fn=lambda: {"storage": {"filesystem": {}}},
    )

    return [
        no_config_pipeline_hourly_schedule,
        no_config_pipeline_hourly_schedule_with_schedule_id_tag,
        no_config_pipeline_hourly_schedule_with_config_fn,
        no_config_should_execute,
        dynamic_config,
    ]
