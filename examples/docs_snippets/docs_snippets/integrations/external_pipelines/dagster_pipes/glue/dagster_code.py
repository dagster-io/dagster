from dagster_aws.pipes import PipesGlueClient

import dagster as dg


@dg.asset
def glue_pipes_asset(
    context: dg.AssetExecutionContext, pipes_glue_client: PipesGlueClient
):
    return pipes_glue_client.run(
        context=context,
        start_job_run_params={
            "JobName": "Example Job",
            "Arguments": {"some_parameter": "some_value"},
        },
    ).get_materialize_result()
