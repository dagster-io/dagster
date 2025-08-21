from dagster_aws.pipes import PipesEMRServerlessClient

import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        resources={"pipes_emr_serverless_client": PipesEMRServerlessClient()}
    )
