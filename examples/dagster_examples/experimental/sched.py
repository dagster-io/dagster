import os
from datetime import date, timedelta

from dagster_cron import SystemCronScheduler
from dagster_examples.experimental.partitions import log_date_set, us_states_set

from dagster import ScheduleDefinition, schedules


@schedules(scheduler=SystemCronScheduler)
def define_scheduler():
    def dash_stats_datetime_partition_config():

        yesterday = date.today() - timedelta(days=1)
        date_string = yesterday.strftime("%Y-%m-%d")

        return {
            'resources': {
                'bigquery': None,
                'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}},
            },
            'solids': {'bq_solid': {'config': {'date': date_string}}},
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

    log_state_partition = us_states_set.create_schedule_definition(
        schedule_name='log_states', cron_schedule='* * * * *'
    )

    log_date_partition = log_date_set.create_schedule_definition(
        schedule_name='log_dates', cron_schedule='* * * * *'
    )

    return [dash_stats_datetime_partition, log_date_partition, log_state_partition]
