from dagster import job, op


@op(config_schema={"date": str})
def process_data_for_date(context):
    date = context.op_config["date"]
    context.log.info(f"processing data for {date}")


@job
def do_stuff():
    process_data_for_date()
