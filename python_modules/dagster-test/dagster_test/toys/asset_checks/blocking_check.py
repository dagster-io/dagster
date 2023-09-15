import random
import time

from dagster import AssetCheckResult, AssetCheckSpec, Out, Output, graph_asset, op




@op
def get_data_op():
    """
    Do the actual work to materialize
    """
    return "foobar"


@op(out={"result": Out(), "blocking_graph_asset_random_fail_check": Out()})
def blocking_check_op(data):
    '''
    Check the materialized data. We pass data through this Op so that downstreams
    assets will wait for the check to complete before executing.
    '''
    yield Output(data)

    random.seed(time.time())
    success = random.choice([True, False])
    yield AssetCheckResult(success=success, metadata={"fiz": "buz"})

    if not success:
        raise Exception("The check failed, so block downstreams!")


@graph_asset(
    group_name="asset_checks",
    check_specs=[
        AssetCheckSpec(
            name="random_fail_check",
            asset="blocking_graph_asset",
            description="A check that fails half the time",
        )
    ],
)
def blocking_graph_asset():
    """
    An asset that materializes data and then runs a check on it. If the check fails, it will raise an
    exception so that downstreams don't execute.
    """
    data = get_data_op()
    return blocking_check_op(data)
