from dagster import RetryPolicy, asset


@asset(
    retry_policy=RetryPolicy(
        max_retries=3,
    )
)
def better(context):
    context.log.info("I HAVE FAILED")
    raise Exception("I HAVE FAILED")


@asset
def works(context):
    pass
