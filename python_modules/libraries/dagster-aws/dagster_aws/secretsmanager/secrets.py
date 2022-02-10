from typing import Dict, List


def get_tagged_secrets(secrets_manager, secrets_tag: str) -> Dict[str, str]:
    """
    Return a dictionary of AWS Secrets Manager names to arns
    for any secret tagged with `secrets_tag`.
    """

    secrets = {}
    paginator = secrets_manager.get_paginator("list_secrets")
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


def get_secrets_from_arns(secrets_manager, secret_arns: List[str]) -> Dict[str, str]:
    """
    Return a dictionary of AWS Secrets Manager names to arns.
    """

    secrets = {}
    for arn in secret_arns:
        name = secrets_manager.describe_secret(SecretId=arn)["Name"]
        secrets[name] = arn

    return secrets
