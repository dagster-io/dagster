from dagster_aws.secretsmanager import (
    SecretsManagerResource,
    SecretsManagerSecretsResource,
)

import dagster as dg


@dg.asset
def my_asset(secretsmanager: SecretsManagerResource):
    secret_value = secretsmanager.get_client().get_secret_value(
        SecretId="arn:aws:secretsmanager:region:aws_account_id:secret:appauthexample-AbCdEf"
    )
    return secret_value


@dg.asset
def my_other_asset(secrets: SecretsManagerSecretsResource):
    secret_value = secrets.fetch_secrets().get("my-secret-name")
    return secret_value


defs = dg.Definitions(
    assets=[my_asset, my_other_asset],
    resources={
        "secretsmanager": SecretsManagerResource(region_name="us-west-1"),
        "secrets": SecretsManagerSecretsResource(
            region_name="us-west-1",
            secrets_tag="dagster",
        ),
    },
)
