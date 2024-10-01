# start_asset_marker

# dagster_glue_pipes.py
from dagster import AssetExecutionContext, asset
from dagster_aws.pipes import PipesECSClient


@asset
def ecs_pipes_asset(context: AssetExecutionContext, pipes_ecs_client: PipesECSClient):
    return pipes_ecs_client.run(
        context=context,
        run_task_params={
            "taskDefinition": "my-task",
            "count": 1,
        },
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker

from dagster import Definitions  # noqa


defs = Definitions(
    assets=[ecs_pipes_asset],
    resources={"pipes_ecs_client": PipesECSClient()},
)

# end_definitions_marker
