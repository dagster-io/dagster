import random

from dagster import AssetKey, Output, RunRequest, asset, asset_sensor, job, op


@asset(output_required=False)
def may_not_materialize(context):
    random.seed()
    rand_num = random.randint(1, 10)
    context.log.info(
        f"Random number is {rand_num}. Asset will {'not' if rand_num >=5 else ''} materialize."
    )
    if rand_num < 5:
        yield Output([1, 2, 3])


@asset
def downstream_conditional(may_not_materialize):
    return may_not_materialize + [4]


@op
def success_op(context):
    context.log.info("success!")


@job
def success_job():
    success_op()


@asset_sensor(asset_key=AssetKey("may_not_materialize"), job=success_job)
def may_not_materialize_sensor(context, asset_event):  # pylint: disable=unused-argument
    return RunRequest(run_key=None)


def get_conditional_assets_repo():
    return [may_not_materialize, downstream_conditional, may_not_materialize_sensor, success_job]
