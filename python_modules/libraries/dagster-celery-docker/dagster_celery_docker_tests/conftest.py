import json
import os

import boto3
import pytest


@pytest.fixture
def aws_creds():
    sm_client = boto3.client("secretsmanager", region_name="us-west-1")

    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return {
            "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
        }

    try:
        creds = json.loads(
            sm_client.get_secret_value(
                SecretId=os.getenv("AWS_SSM_REFERENCE", "development/DOCKER_AWS_CREDENTIAL")
            ).get("SecretString")
        )
        return creds
    except Exception as e:
        raise Exception(
            "Must have AWS credentials set to be able to run celery docker tests locally. Run "
            f"'aws sso login' to authenticate. Original error: {e}"
        )
