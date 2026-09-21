from pydantic import BaseModel

from dagster_rest_resources.schemas.enums import DgApiAgentStatus
from dagster_rest_resources.schemas.util import DgApiTruncatedList


class DgApiAgentMetadataEntry(BaseModel):
    key: str
    value: str | None


class DgApiAgent(BaseModel):
    id: str
    agent_label: str | None
    status: DgApiAgentStatus
    last_heartbeat_time: float
    metadata: list[DgApiAgentMetadataEntry]


class DgApiAgentList(DgApiTruncatedList[DgApiAgent]):
    pass
