import uuid

from dagster._core.definitions.definitions_class import Definitions
from dagster_powerbi import PowerBIToken, PowerBIWorkspace

fake_token = uuid.uuid4().hex
resource = PowerBIWorkspace(
    credentials=PowerBIToken(api_token=fake_token),
    workspace_id="a2122b8f-d7e1-42e8-be2b-a5e636ca3221",
)
resource_second_workspace = PowerBIWorkspace(
    credentials=PowerBIToken(api_token=fake_token),
    workspace_id="c5322b8a-d7e1-42e8-be2b-a5e636ca3221",
)


defs = Definitions.merge(
    resource.build_defs(),
    resource_second_workspace.build_defs(),
)
