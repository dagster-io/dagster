from dagster import ScheduleDefinition, schedules


@schedules
def gbfs_schedules():
    return [
        ScheduleDefinition(
            name='get_gbfs_feed_every_minute',
            cron_schedule='* * * * *',
            pipeline_name='download_gbfs_files',
            environment_dict={'storage': {'filesystem': {}}},
        ),
        ScheduleDefinition(
            name='get_gbfs_feed_every_five_minutes',
            cron_schedule='*/5 * * * *',
            pipeline_name='download_gbfs_files',
            environment_dict={'storage': {'filesystem': {}}},
        ),
    ]
