# isort: skip_file
from dagster import job

from .date_config_job import process_data_for_date

# start_partitioned_config
from dagster import daily_partitioned_config
from datetime import datetime


@daily_partitioned_config(start_date=datetime(2020, 1, 1))
def my_partitioned_config(start: datetime, _end: datetime):
    return {
        "ops": {
            "process_data_for_date": {"config": {"date": start.strftime("%Y-%m-%d")}}
        }
    }


# end_partitioned_config

# start_partitioned_job
@job(config=my_partitioned_config)
def do_stuff_partitioned():
    process_data_for_date()


# end_partitioned_job
