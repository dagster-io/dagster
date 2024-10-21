from random import randint

import dagster as dg


@dg.op(
    retry_policy=dg.RetryPolicy(
        max_retries=5,
        delay=0.2,  # 200ms
        backoff=dg.Backoff.EXPONENTIAL,
        jitter=dg.Jitter.PLUS_MINUS,
    )
)
def step_one() -> int:
    if randint(0, 2) >= 1:
        raise Exception("Flaky step that may fail randomly")
    return 42


@dg.op
def step_two(num: int):
    return num**2


@dg.graph_asset
def complex_asset():
    return step_two(step_one())


defs = dg.Definitions(assets=[complex_asset])
