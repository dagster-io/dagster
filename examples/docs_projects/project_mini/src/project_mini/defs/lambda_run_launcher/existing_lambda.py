import dagster as dg


# start_ops_only_example
@dg.op(
    config_schema={
        "source_bucket": str,
        "destination_bucket": str,
        "file_pattern": str,
    }
)
def copy_files_op(context: dg.OpExecutionContext):
    config = context.op_config
    context.log.info(f"Copying files from {config['source_bucket']}")
    return {"status": "initiated"}


@dg.job(
    tags={
        "lambda/function_name": "existing-s3-copy-function",
        "lambda/payload_mode": "ops_only",
    }
)
def copy_files_job():
    copy_files_op()


# end_ops_only_example


# start_custom_example
@dg.op(
    config_schema={
        "api_key": str,
        "endpoint": str,
        "data": list,
    }
)
def api_call_op(context: dg.OpExecutionContext):
    config = context.op_config
    context.log.info(f"Calling API at {config['endpoint']}")
    return {"status": "called"}


@dg.job(
    tags={
        "lambda/function_name": "existing-api-caller",
        "lambda/payload_mode": "custom",
        "lambda/payload_config_path": "ops.api_call_op.config",
    }
)
def api_call_job():
    api_call_op()


# end_custom_example


# start_config_only_example
@dg.op(config_schema={"input_file": str, "output_file": str})
def transform_op(context: dg.OpExecutionContext):
    context.log.info("Transforming data")
    return {"transformed": True}


@dg.op(config_schema={"destination": str})
def load_op(context: dg.OpExecutionContext):
    context.log.info("Loading data")
    return {"loaded": True}


@dg.job(
    tags={
        "lambda/function_name": "existing-etl-function",
        "lambda/payload_mode": "config_only",
    }
)
def etl_job():
    transform_op()
    load_op()


# end_config_only_example
