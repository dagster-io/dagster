import boto3
from dagster_aws.pipes import PipesLambdaClient

import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "lambda_pipes_client": PipesLambdaClient(client=boto3.client("lambda"))
        }
    )
