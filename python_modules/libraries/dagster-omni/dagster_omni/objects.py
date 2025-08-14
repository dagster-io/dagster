from typing import Any, Optional

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class OmniFolder:
    id: str
    name: str
    path: str
    scope: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniFolder":
        """Create OmniFolder from JSON response data."""
        return cls(id=data["id"], name=data["name"], path=data["path"], scope=data["scope"])


@whitelist_for_serdes
@record
class OmniLabel:
    name: str
    verified: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniLabel":
        """Create OmniLabel from JSON response data."""
        return cls(name=data["name"], verified=data["verified"])


@whitelist_for_serdes
@record
class OmniOwner:
    id: str
    name: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniOwner":
        """Create OmniOwner from JSON response data."""
        return cls(id=data["id"], name=data["name"])


@whitelist_for_serdes
@record
class OmniDocument:
    identifier: str
    name: str
    scope: str
    connection_id: str
    deleted: bool
    has_dashboard: bool
    type: str
    updated_at: str
    owner: OmniOwner
    folder: Optional[OmniFolder]
    labels: list[OmniLabel]
    queries: list["OmniQuery"]

    @classmethod
    def from_json(
        cls, data: dict[str, Any], queries: Optional[list["OmniQuery"]] = None
    ) -> "OmniDocument":
        """Create OmniDocument from JSON response data."""
        folder = None
        if data.get("folder"):
            folder = OmniFolder.from_json(data["folder"])

        labels = [OmniLabel.from_json(label_data) for label_data in data.get("labels", [])]
        owner = OmniOwner.from_json(data["owner"])

        return cls(
            identifier=data["identifier"],
            name=data["name"],
            scope=data["scope"],
            connection_id=data["connectionId"],
            deleted=data["deleted"],
            has_dashboard=data["hasDashboard"],
            type=data.get("type", "document"),
            updated_at=data["updatedAt"],
            owner=owner,
            folder=folder,
            labels=labels,
            queries=queries or [],
        )


@whitelist_for_serdes
@record
class OmniQueryConfig:
    """Represents the essential query configuration needed for asset creation."""

    table: Optional[str]
    model_id: Optional[str]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniQueryConfig":
        """Create OmniQueryConfig from JSON query configuration data."""
        return cls(
            table=data.get("table"),
            model_id=data.get("modelId"),
        )


@whitelist_for_serdes
@record
class OmniQuery:
    id: str
    name: str
    query_config: Optional[OmniQueryConfig]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniQuery":
        """Create OmniQuery from JSON response data."""
        query_config = None
        if data.get("query"):
            query_config = OmniQueryConfig.from_json(data["query"])

        return cls(
            id=data["id"],
            name=data.get("name") or f"query_{data['id']}",
            query_config=query_config,
        )


@whitelist_for_serdes
@record
class OmniState:
    """Serializable container object for recording the state of the Omni API at a given point in time.

    Properties:
        documents: list[OmniDocument] - Documents contain their queries directly
    """

    documents: list[OmniDocument]
