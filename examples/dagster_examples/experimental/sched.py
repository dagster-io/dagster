import os

from dagster_cron import SystemCronScheduler
from dagster_examples.experimental.partitions import dash_stat_date_set, log_date_set, us_states_set

from dagster import schedules


@schedules(scheduler=SystemCronScheduler)
def define_scheduler():

    dash_stats_datetime_partition = dash_stat_date_set.create_schedule_definition(
        schedule_name='dash_stats_datetime_partition',
        cron_schedule='0 0 * * *',
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
