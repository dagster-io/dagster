# start_asset_marker
from dagster_aws.pipes import PipesECSClient

import dagster as dg


@dg.asset
def ecs_pipes_asset(
    context: dg.AssetExecutionContext, pipes_ecs_client: PipesECSClient
):
    return pipes_ecs_client.run(
        context=context,
        run_task_params={
            "taskDefinition": "my-task",
            "count": 1,
        },
    ).get_materialize_result()
