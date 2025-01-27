from dagster import EnvVar, define_asset_job
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.env import environ
from dagster_sigma import (
    DagsterSigmaTranslator,
    SigmaBaseUrl,
    SigmaOrganization,
    load_sigma_asset_specs,
)

fake_client_id = "fake_client_id"
fake_client_secret = "fake_client_secret"

with environ({"SIGMA_CLIENT_ID": fake_client_id, "SIGMA_CLIENT_SECRET": fake_client_secret}):
    fake_token = "fake_token"

    class MyCoolTranslator(DagsterSigmaTranslator):
        def get_asset_spec(self, data) -> AssetSpec:
            spec = super().get_asset_spec(data)
            return spec.replace_attributes(
                key=spec.key.with_prefix("my_prefix"),
            )

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=EnvVar("SIGMA_CLIENT_ID"),
        client_secret=EnvVar("SIGMA_CLIENT_SECRET"),
    )

    sigma_specs = load_sigma_asset_specs(resource, dagster_sigma_translator=MyCoolTranslator())
    defs = Definitions(assets=[*sigma_specs], jobs=[define_asset_job("all_asset_job")])
