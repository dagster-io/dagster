import os

from dagster import EnvVar, asset, define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.env import environ
from dagster_sigma import SigmaBaseUrl, SigmaOrganization, load_sigma_asset_specs

fake_client_id = "fake_client_id"
fake_client_secret = "fake_client_secret"
snapshot_path = os.getenv("SIGMA_SNAPSHOT_PATH") or None

with environ({"SIGMA_CLIENT_ID": fake_client_id, "SIGMA_CLIENT_SECRET": fake_client_secret}):
    fake_token = "fake_token"
    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=EnvVar("SIGMA_CLIENT_ID"),
        client_secret=EnvVar("SIGMA_CLIENT_SECRET"),
    )

    @asset
    def my_materializable_asset():
        pass

    sigma_specs = load_sigma_asset_specs(resource, snapshot_path=snapshot_path)
    defs = Definitions(
        assets=[my_materializable_asset, *sigma_specs], jobs=[define_asset_job("all_asset_job")]
    )
