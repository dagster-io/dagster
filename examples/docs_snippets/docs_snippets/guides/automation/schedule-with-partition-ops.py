from datetime import datetime

import dagster as dg


class ProcessDateConfig(dg.Config):
    date: str


@dg.daily_partitioned_config(start_date=datetime(2024, 1, 1))
def partitioned_config(start: datetime, _end: datetime): ...


@dg.op
def process_data_for_date(context: dg.OpExecutionContext, config: ProcessDateConfig):
    date = config.date
    context.log.info(f"processing data for {date}")


# Define the job
@dg.job(config=partitioned_config)
def partitioned_op_job(): ...


# highlight-start
# Create the schedule from the partition
partitioned_op_schedule = dg.build_schedule_from_partitioned_job(
    partitioned_op_job,
)
# highlight-end
