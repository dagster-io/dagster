import dagster as dg
from dagster._time import get_current_timestamp


def should_fail(logger):
    now = get_current_timestamp()
    logger.info(f"Current timestamp: {int(now)}")
    if int(now) % 2 == 0:
        return False
    return True


@dg.asset(retry_policy=dg.RetryPolicy(max_retries=2))
def random_1(context):
    if should_fail(context.log):
        raise Exception("random_1 failed")
    return 1


@dg.asset
def asset_1(context):
    return 1


asset_job_for_step_stats = dg.define_asset_job(
    "asset_job_for_step_stats", selection=["asset_1", "random_1"]
)


class RunIdConfig(dg.Config):
    run_id: str


@dg.op
def print_step_stats_op(context: dg.OpExecutionContext, config: RunIdConfig):
    step_stats = context.instance.get_streamline_step_stats_for_run(config.run_id)
    context.log.info("Step stats:")
    context.log.info(step_stats)


@dg.job
def print_step_stats():
    print_step_stats_op()


defs = dg.Definitions(
    jobs=[print_step_stats, asset_job_for_step_stats],
    assets=[asset_1, random_1],
)
