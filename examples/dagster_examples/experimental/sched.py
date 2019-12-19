import datetime
import os

from dagster_cron import SystemCronScheduler

from dagster import daily_schedule, hourly_schedule, schedules


@schedules(scheduler=SystemCronScheduler)
def define_scheduler():
    @daily_schedule(
        pipeline_name='dash_stats',
        start_date=datetime.datetime(2019, 12, 1),
        execution_time=datetime.time(hour=3, minute=41),
        environment_vars={
            'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            'SLACK_TOKEN': os.getenv('SLACK_TOKEN'),
        },
    )
    def dash_stats_schedule(date):
        return {
            'resources': {
                'bigquery': {},
                'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}},
            },
            'solids': {'bq_solid': {'config': {'date': date.strftime("%Y-%m-%d")}}},
        }

    @hourly_schedule(
        pipeline_name='log_partitions',
        start_date=datetime.datetime(2019, 12, 1),
        execution_time=datetime.time(minute=28),
    )
    def hourly_announce_schedule(date):
        return {
            'solids': {
                'announce_partition': {'config': {'partition': "Partition is: " + str(date)}}
            }
        }

    return [
        dash_stats_schedule,
        hourly_announce_schedule,
    ]
