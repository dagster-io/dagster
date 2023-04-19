# isort: skip_file
from dagster import job, op, Config


class ProcessDataForDateConfig(Config):
    date: str


@op
def process_data_for_date(context, config: ProcessDataForDateConfig):
    date = config.date
    context.log.info(f"processing data for {date}")


# start_partitioned_config
from dagster import daily_partitioned_config, RunConfig
from datetime import datetime


@daily_partitioned_config(start_date=datetime(2020, 1, 1))
def my_partitioned_config(start: datetime, _end: datetime):
    return RunConfig(
        ops={
            "process_data_for_date": ProcessDataForDateConfig(
                date=start.strftime("%Y-%m-%d")
            )
        }
    )


# end_partitioned_config


# start_partitioned_job
@job(config=my_partitioned_config)
def do_stuff_partitioned():
    process_data_for_date()


# end_partitioned_job
