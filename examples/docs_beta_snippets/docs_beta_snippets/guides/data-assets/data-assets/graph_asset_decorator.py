import dagster as dg


@dg.op(
    retry_policy=dg.RetryPolicy(
        max_retries=3,
        delay=0.2,  # 200ms
        backoff=dg.Backoff.EXPONENTIAL,
        jitter=dg.Jitter.PLUS_MINUS,
    )
)
def step_one():
    return 42


@dg.op
def step_two(num):
    return num**2


@dg.graph_asset
def complex_asset():
    return step_two(step_one())


defs = dg.Definitions(assets=[complex_asset])
