from collections.abc import Mapping, Sequence
from typing import Optional

import boto3.session
import dagster._check as check
from dagster._annotations import beta

from dagster_aws.utils import construct_boto_client_retry_config


def construct_secretsmanager_client(
    max_attempts: int,
    region_name: Optional[str] = None,
    profile_name: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    use_ssl: bool = True,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    verify: Optional[bool] = None,
):
    check.int_param(max_attempts, "max_attempts")
    check.opt_str_param(region_name, "region_name")
    check.opt_str_param(profile_name, "profile_name")
    check.opt_str_param(endpoint_url, "endpoint_url")
    check.bool_param(use_ssl, "use_ssl")
    check.opt_bool_param(verify, "verify")
    check.opt_str_param(aws_access_key_id, "aws_access_key_id")
    check.opt_str_param(aws_secret_access_key, "aws_secret_access_key")
    check.opt_str_param(aws_session_token, "aws_session_token")

    client_session = boto3.session.Session(profile_name=profile_name)
    secrets_manager = client_session.client(
        "secretsmanager",
        region_name=region_name,
        use_ssl=use_ssl,
        verify=verify,
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        config=construct_boto_client_retry_config(max_attempts),
    )

    return secrets_manager


@beta
def get_tagged_secrets(secrets_manager, secrets_tags: Sequence[str]) -> Mapping[str, str]:
    """Return a dictionary of AWS Secrets Manager names to arns
    for any secret tagged with `secrets_tag`.
    """
    secrets = {}
    paginator = secrets_manager.get_paginator("list_secrets")
    for secrets_tag in secrets_tags:
        for page in paginator.paginate(
            Filters=[
                {
                    "Key": "tag-key",
                    "Values": [secrets_tag],
                },
            ],
        ):
            for secret in page["SecretList"]:
                secrets[secret["Name"]] = secret["ARN"]

    return secrets


@beta
def get_secrets_from_arns(secrets_manager, secret_arns: Sequence[str]) -> Mapping[str, str]:
    """Return a dictionary of AWS Secrets Manager names to arns."""
    secrets = {}
    for arn in secret_arns:
        name = secrets_manager.describe_secret(SecretId=arn)["Name"]
        secrets[name] = arn

    return secrets
