import uuid
from typing import cast

from dagster import asset, define_asset_job, external_assets_from_specs
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    PendingRepositoryDefinition,
)
from dagster_powerbi import PowerBIWorkspace

fake_token = uuid.uuid4().hex
resource = PowerBIWorkspace(
    api_token=fake_token,
    workspace_id="a2122b8f-d7e1-42e8-be2b-a5e636ca3221",
)
all_asset_specs = resource.build_asset_specs()

assets = external_assets_from_specs(all_asset_specs)


@asset
def my_materializable_asset():
    pass


pending_repo_from_cached_asset_metadata = cast(
    PendingRepositoryDefinition,
    Definitions(
        assets=[*assets, my_materializable_asset], jobs=[define_asset_job("all_asset_job")]
    ).get_inner_repository(),
)
