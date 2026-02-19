import dagster as dg


@dg.op(config_schema={"api_endpoint": str, "api_key": str})
def call_api(context: dg.OpExecutionContext):
    endpoint = context.op_config["api_endpoint"]
    context.log.info(f"Calling API: {endpoint}")
    return {"status": "called", "endpoint": endpoint}


@dg.job(
    tags={
        "lambda/function_name": "api-caller",
        "lambda/invocation_type": "Event",
    }
)
def api_trigger_job():
    call_api()


@dg.op(config_schema={"source_bucket": str, "file_pattern": str})
def trigger_etl(context: dg.OpExecutionContext):
    bucket = context.op_config["source_bucket"]
    context.log.info(f"Triggering ETL for {bucket}")
    return {"triggered": True}


@dg.job(tags={"lambda/function_name": "etl-trigger"})
def etl_trigger_job():
    trigger_etl()


@dg.op
def check_new_data(context: dg.OpExecutionContext):
    context.log.info("Checking for new data...")
    return {"has_new_data": True, "file_count": 42}


@dg.job(tags={"lambda/function_name": "data-checker"})
def check_data_job():
    check_new_data()
