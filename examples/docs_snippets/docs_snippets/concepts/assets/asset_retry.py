from dagster import (
    AssetExecutionContext,
    Backoff,
    Jitter,
    RetryPolicy,
    RetryRequested,
    asset,
)


@asset(
    retry_policy=RetryPolicy(
        max_retries=3,
        delay=0.2,  # 200ms
        backoff=Backoff.EXPONENTIAL,
        jitter=Jitter.PLUS_MINUS,
    )
)
def retried_asset(context: AssetExecutionContext):
    context.log.info("Retry me!")
