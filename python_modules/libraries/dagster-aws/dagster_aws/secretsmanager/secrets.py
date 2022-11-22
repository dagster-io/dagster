from typing import Mapping, Optional, Sequence

import boto3

import dagster._check as check

from ..utils import construct_boto_client_retry_config


def construct_secretsmanager_client(
    max_attempts: int, region_name: Optional[str] = None, profile_name: Optional[str] = None
):
    check.int_param(max_attempts, "max_attempts")
    check.opt_str_param(region_name, "region_name")
    check.opt_str_param(profile_name, "profile_name")

    client_session = boto3.session.Session(profile_name=profile_name)
    secrets_manager = client_session.client(
        "secretsmanager",
        region_name=region_name,
        config=construct_boto_client_retry_config(max_attempts),
    )

    return secrets_manager


def get_tagged_secrets(secrets_manager, secrets_tags: Sequence[str]) -> Mapping[str, str]:
    """
    Return a dictionary of AWS Secrets Manager names to arns
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


def get_secrets_from_arns(secrets_manager, secret_arns: Sequence[str]) -> Mapping[str, str]:
    """
    Return a dictionary of AWS Secrets Manager names to arns.
    """

    secrets = {}
    for arn in secret_arns:
        name = secrets_manager.describe_secret(SecretId=arn)["Name"]
        secrets[name] = arn

    return secrets
