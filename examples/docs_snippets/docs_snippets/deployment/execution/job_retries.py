import dagster as dg


@dg.job(tags={"dagster/max_retries": 3})
def sample_job():
    pass


@dg.job(tags={"dagster/max_retries": 3, "dagster/retry_strategy": "ALL_STEPS"})
def other_sample_sample_job():
    pass
