from dagster_aws.pipes import PipesECSClient

import dagster as dg


# start_resources
@dg.definitions
def resources():
    return dg.Definitions(resources={"pipes_ecs_client": PipesECSClient()})
