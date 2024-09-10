import uuid
from typing import cast

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
resource_second_workspace = PowerBIWorkspace(
    api_token=fake_token,
    workspace_id="c5322b8a-d7e1-42e8-be2b-a5e636ca3221",
)


pending_repo_from_cached_asset_metadata = cast(
    PendingRepositoryDefinition,
    Definitions.merge(
        resource.build_defs(),
        resource_second_workspace.build_defs(),
    ).get_inner_repository(),
)
