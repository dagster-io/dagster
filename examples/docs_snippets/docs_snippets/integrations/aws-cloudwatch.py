from dagster_aws.cloudwatch import cloudwatch_logger

import dagster as dg


@dg.asset
def my_asset(context: dg.AssetExecutionContext):
    context.log.info("Hello, CloudWatch!")
    context.log.error("This is an error")
    context.log.debug("This is a debug message")


defs = dg.Definitions(
    assets=[my_asset],
    loggers={
        "cloudwatch_logger": cloudwatch_logger,
    },
)
