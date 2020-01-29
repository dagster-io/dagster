import datetime

from dagster import daily_schedule, hourly_schedule, schedule, schedules


@hourly_schedule(
    pipeline_name='metrics_pipeline',
    start_date=datetime.datetime(2019, 12, 1),
    execution_time=datetime.time(),
)
def daily_ingest_schedule(date):
    date_path = date.strftime('%Y/%m/%d/%H')
    return {
        'solids': {
            'save_metrics': {
                'inputs': {'data_path': {'value': 's3://bucket-name/data/{}'.format(date_path)}}
            }
        },
    }


@daily_schedule(
    pipeline_name='rollup_pipeline',
    start_date=datetime.datetime(2019, 12, 1),
    execution_time=datetime.time(hour=3, minute=0),
)
def daily_rollup_schedule(date):
    date_path = date.strftime('%Y/%m/%d')
    return {
        'solids': {
            'rollup_data': {
                'inputs': {'data_path': {'value': 's3://bucket-name/data/{}'.format(date_path)}}
            }
        },
    }


@schedule(
    name="test_schedule", cron_schedule="* * * * *", pipeline_name="metrics_pipeline",
)
def test_schedule(_):
    return {
        'solids': {
            'save_metrics': {
                'inputs': {'data_path': {'value': 's3://bucket-name/data/{}'.format("date")}}
            }
        },
    }


@schedules
def define_scheduler():
    return [daily_ingest_schedule, daily_rollup_schedule, test_schedule]
