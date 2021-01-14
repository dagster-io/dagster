from dagster import pipeline, solid


# start_pipeline_marker_1
@solid(config_schema={"date": str})
def process_data_for_date(context):
    date = context.solid_config["date"]
    context.log.info(f"processing data for {date}")


@solid
def post_slack_message(context):
    context.log.info("posting slack message")


@pipeline
def my_data_pipeline():
    process_data_for_date()
    post_slack_message()


# end_pipeline_marker_1

# start_pipeline_marker_2
@solid(config_schema={"filename": str})
def process_file(context):
    filename = context.solid_config["filename"]
    context.log.info(filename)


@pipeline
def log_file_pipeline():
    process_file()


# end_pipeline_marker_2
