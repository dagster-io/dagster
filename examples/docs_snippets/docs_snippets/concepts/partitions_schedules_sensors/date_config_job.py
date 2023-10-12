from dagster import Config, job, op, OpExecutionContext


class ProcessDateConfig(Config):
    date: str


@op
def process_data_for_date(context: OpExecutionContext, config: ProcessDateConfig):
    date = config.date
    context.log.info(f"processing data for {date}")


@job
def do_stuff():
    process_data_for_date()
