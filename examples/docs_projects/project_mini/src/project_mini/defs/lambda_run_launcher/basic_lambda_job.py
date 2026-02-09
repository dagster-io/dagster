import dagster as dg


# start_async_lambda_job
@dg.op(config_schema={"message": str})
def async_op(context: dg.OpExecutionContext):
    message = context.op_config["message"]
    context.log.info(f"Message: {message}")
    return {"status": "processed", "message": message}


@dg.job(
    tags={
        "lambda/function_name": "dagster-example-handler",
        "lambda/invocation_type": "Event",
    }
)
def async_lambda_job():
    async_op()


# end_async_lambda_job


# start_sync_lambda_job
@dg.op(
    config_schema={
        "input_data": str,
        "processing_mode": str,
    }
)
def sync_op(context: dg.OpExecutionContext):
    input_data = context.op_config["input_data"]
    mode = context.op_config["processing_mode"]
    context.log.info(f"Processing {input_data} in {mode} mode")
    return {"result": "completed"}


@dg.job(
    tags={
        "lambda/function_name": "dagster-sync-handler",
        "lambda/invocation_type": "RequestResponse",
    }
)
def sync_lambda_job():
    sync_op()


# end_sync_lambda_job


# start_arn_lambda_job
@dg.op
def arn_based_op(context: dg.OpExecutionContext):
    context.log.info("Executing with Lambda ARN")
    return {"status": "success"}


@dg.job(
    tags={
        "lambda/function_arn": "arn:aws:lambda:us-east-1:123456789012:function:my-dagster-handler",
        "lambda/invocation_type": "Event",
    }
)
def arn_lambda_job():
    arn_based_op()


# end_arn_lambda_job


# start_etl_lambda_job
@dg.op(config_schema={"input_path": str})
def extract(context: dg.OpExecutionContext):
    input_path = context.op_config["input_path"]
    context.log.info(f"Extracting from {input_path}")
    return {"data": ["record1", "record2", "record3"]}


@dg.op
def transform(context: dg.OpExecutionContext, data: dict):
    records = data["data"]
    context.log.info(f"Transforming {len(records)} records")
    return {"transformed": [r.upper() for r in records]}


@dg.op(config_schema={"output_path": str})
def load(context: dg.OpExecutionContext, transformed: dict):
    output_path = context.op_config["output_path"]
    data = transformed["transformed"]
    context.log.info(f"Loading {len(data)} records to {output_path}")
    return {"loaded": len(data)}


@dg.job(
    tags={
        "lambda/function_name": "dagster-etl-handler",
        "lambda/invocation_type": "Event",
    }
)
def etl_lambda_job():
    extracted = extract()
    transformed = transform(extracted)
    load(transformed)


# end_etl_lambda_job
