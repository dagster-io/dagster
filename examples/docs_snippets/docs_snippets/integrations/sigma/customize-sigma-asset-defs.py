from dagster_sigma import SigmaBaseUrl, SigmaOrganization, SigmaWorkbook

from dagster import AssetSpec, Definitions, EnvVar
from dagster._core.definitions.decorators.definitions_decorator import definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext

resource = SigmaOrganization(
    base_url=SigmaBaseUrl.AWS_US,
    client_id=EnvVar("SIGMA_CLIENT_ID"),
    client_secret=EnvVar("SIGMA_CLIENT_SECRET"),
)


defs = resource.build_defs().map_asset_specs(
    lambda spec: spec._replace(owners=["my_team"])
)
