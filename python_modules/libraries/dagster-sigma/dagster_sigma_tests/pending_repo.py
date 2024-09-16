import uuid
from typing import cast

from dagster import asset, define_asset_job
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    PendingRepositoryDefinition,
)
from dagster_sigma import SigmaBaseUrl, SigmaOrganization

fake_client_id = uuid.uuid4().hex
fake_client_secret = uuid.uuid4().hex

fake_token = uuid.uuid4().hex
resource = SigmaOrganization(
    cloud_type=SigmaBaseUrl.AWS_US,
    client_id=fake_client_id,
    client_secret=fake_client_secret,
)
sigma_defs = resource.build_defs()


@asset
def my_materializable_asset():
    pass


pending_repo_from_cached_asset_metadata = cast(
    PendingRepositoryDefinition,
    Definitions.merge(
        Definitions(assets=[my_materializable_asset], jobs=[define_asset_job("all_asset_job")]),
        sigma_defs,
    ).get_inner_repository(),
)
