import uuid

from dagster import asset, define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster_powerbi import PowerBIToken, PowerBIWorkspace
from dagster_powerbi.resource import load_powerbi_asset_specs

fake_token = uuid.uuid4().hex
resource = PowerBIWorkspace(
    credentials=PowerBIToken(api_token=fake_token),
    workspace_id="a2122b8f-d7e1-42e8-be2b-a5e636ca3221",
)
pbi_specs = load_powerbi_asset_specs(resource)


@asset
def my_materializable_asset():
    pass


defs = Definitions(
    assets=[my_materializable_asset, *pbi_specs], jobs=[define_asset_job("all_asset_job")]
)
