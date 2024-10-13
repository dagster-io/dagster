# start_asset_marker

# dagster_lambda_pipes.py

import boto3
from dagster_aws.pipes import PipesLambdaClient

from dagster import AssetExecutionContext, Definitions, asset


@asset
def lambda_pipes_asset(
    context: AssetExecutionContext, lambda_pipes_client: PipesLambdaClient
):
    return lambda_pipes_client.run(
        context=context,
        function_name="dagster_pipes_function",
        event={"some_parameter_value": 1},
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker

# dagster_lambda_pipes.py

defs = Definitions(
    assets=[lambda_pipes_asset],
    resources={"lambda_pipes_client": PipesLambdaClient(client=boto3.client("lambda"))},
)
# end_definitions_marker
