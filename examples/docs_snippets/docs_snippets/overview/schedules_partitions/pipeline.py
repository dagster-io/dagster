from dagster import pipeline, solid


@solid(config_schema={"day_of_week": str})
def process_data_for_day(context):
    day_of_week = context.solid_config["day_of_week"]
    context.log.info(day_of_week)


@pipeline
def my_pipeline():
    process_data_for_day()


@solid(config_schema={"date": str})
def process_data_for_date(context):
    date = context.solid_config["date"]
    context.log.info(date)


@pipeline
def my_data_pipeline():
    process_data_for_date()
