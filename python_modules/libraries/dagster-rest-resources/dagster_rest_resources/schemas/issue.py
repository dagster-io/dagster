from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiIssueStatus
from dagster_rest_resources.schemas.util import DgApiPaginatedList


class DgApiIssueLinkedRun(BaseModel):
    run_id: str


class DgApiIssueLinkedAsset(BaseModel):
    asset_key: str  # Slash-separated asset key (e.g., "my/asset/key")


class DgApiIssue(BaseModel):
    id: str
    title: str
    description: str
    status: DgApiIssueStatus
    created_by_name: str
    linked_objects: list[DgApiIssueLinkedRun | DgApiIssueLinkedAsset]
    context: str | None = None


class DgApiIssueList(DgApiPaginatedList["DgApiIssue"]):
    pass
