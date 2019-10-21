import os
from datetime import date, timedelta

from dagster_cron import SystemCronScheduler

from dagster import ScheduleDefinition, schedules


@schedules(scheduler=SystemCronScheduler)
def define_scheduler():
    def dash_stats_datetime_partition_config():

        yesterday = date.today() - timedelta(days=1)
        d = yesterday.strftime("%Y-%m-%d")

        return {
            'resources': {
                'bigquery': None,
                'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}},
            },
            'solids': {'bq_solid': {'config': {'date': d}}},
        }

    dash_stats_datetime_partition = ScheduleDefinition(
        name='dash_stats_datetime_partition',
        cron_schedule='* * * * *',
        pipeline_name='dash_stats',
        environment_dict_fn=dash_stats_datetime_partition_config,
        environment_vars={
            'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            'SLACK_TOKEN': os.getenv('SLACK_TOKEN'),
        },
    )

    return [dash_stats_datetime_partition]
