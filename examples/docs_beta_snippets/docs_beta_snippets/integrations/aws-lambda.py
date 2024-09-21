import boto3
from dagster_aws.pipes import PipesLambdaClient

import dagster as dg

lambda_client = boto3.client("lambda", region_name="us-west-1")

lambda_pipes_client = PipesLambdaClient(client=lambda_client)


@dg.asset
def lambda_pipes_asset(
    context: dg.AssetExecutionContext, lambda_pipes_client: PipesLambdaClient
):
    return lambda_pipes_client.run(
        context=context,
        function_name="your_lambda_function_name",
        event={"key": "value"},
    ).get_materialize_result()


defs = dg.Definitions(
    assets=[lambda_pipes_asset],
    resources={"lambda_pipes_client": lambda_pipes_client},
)
