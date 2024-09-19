from dagster import asset, define_asset_job
from dagster._core.definitions.decorators.definitions_decorator import definitions
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext
from dagster_sigma import SigmaBaseUrl, SigmaOrganization

fake_client_id = "fake_client_id"
fake_client_secret = "fake_client_secret"

fake_token = "fake_token"
resource = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=fake_client_id,
    client_secret=fake_client_secret,
)


@asset
def my_materializable_asset():
    pass


@definitions
def defs(context: DefinitionsLoadContext) -> Definitions:
    sigma_defs = resource.build_defs(context)
    return Definitions.merge(
        Definitions(assets=[my_materializable_asset], jobs=[define_asset_job("all_asset_job")]),
        sigma_defs,
    )
