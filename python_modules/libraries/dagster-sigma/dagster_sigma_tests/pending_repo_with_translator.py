from dagster import AssetSpec, EnvVar, define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.env import environ
from dagster_sigma import (
    DagsterSigmaTranslator,
    SigmaBaseUrl,
    SigmaOrganization,
    load_sigma_asset_specs,
)
from dagster_sigma.translator import SigmaDataset, SigmaWorkbook

fake_client_id = "fake_client_id"
fake_client_secret = "fake_client_secret"

with environ({"SIGMA_CLIENT_ID": fake_client_id, "SIGMA_CLIENT_SECRET": fake_client_secret}):
    fake_token = "fake_token"

    class MyCoolTranslator(DagsterSigmaTranslator):
        def get_dataset_spec(self, data: SigmaDataset) -> AssetSpec:
            spec = super().get_dataset_spec(data)
            return spec._replace(key=spec.key.with_prefix("my_prefix"))

        def get_workbook_spec(self, data: SigmaWorkbook) -> AssetSpec:
            spec = super().get_workbook_spec(data)
            return spec._replace(key=spec.key.with_prefix("my_prefix"))

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=EnvVar("SIGMA_CLIENT_ID"),
        client_secret=EnvVar("SIGMA_CLIENT_SECRET"),
        translator=MyCoolTranslator,
    )

    sigma_specs = load_sigma_asset_specs(resource)
    defs = Definitions(assets=[*sigma_specs], jobs=[define_asset_job("all_asset_job")])
