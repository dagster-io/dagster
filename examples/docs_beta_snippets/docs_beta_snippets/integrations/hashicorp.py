# See the Resources docs to learn more: https://docs.dagster.io/concepts/resources

import os

from dagster_hashicorp.vault import vault_resource

import dagster as dg


@dg.asset(required_resource_keys={"vault"})
def example_asset(context):
    secret_data = context.resources.vault.read_secret(secret_path="secret/data/foo/bar")
    context.log.debug(f"Secret: {secret_data}")


defs = dg.Definitions(
    assets=[example_asset],
    resources={
        "vault": vault_resource.configured(
            {
                "url": "vault-host:8200",
                "auth_type": {"token": {"token": dg.EnvVar("VAULT_AUTH_TOKEN")}},
            }
        )
    },
)
