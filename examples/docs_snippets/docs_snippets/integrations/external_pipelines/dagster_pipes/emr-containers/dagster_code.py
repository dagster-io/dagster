from dagster_aws.pipes import PipesEMRContainersClient

import dagster as dg


@dg.asset
def emr_containers_asset(
    context: dg.AssetExecutionContext,
    pipes_emr_containers_client: PipesEMRContainersClient,
):
    image = (
        ...
    )  # it's likely the image can be taken from context.run_tags["dagster/image"]

    return pipes_emr_containers_client.run(
        context=context,
        start_job_run_params={
            "releaseLabel": "emr-7.5.0-latest",
            "virtualClusterId": ...,  # ty: ignore[invalid-argument-type]
            "clientToken": context.run_id,  # idempotency identifier for the job run
            "executionRoleArn": ...,  # ty: ignore[invalid-argument-type]
            "jobDriver": {
                "sparkSubmitJobDriver": {
                    "entryPoint": "local:///app/script.py",
                    "sparkSubmitParameters": f"--conf spark.kubernetes.container.image={image}",
                }
            },
        },  # ty: ignore[invalid-argument-type]
    ).get_materialize_result()
