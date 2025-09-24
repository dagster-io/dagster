from functools import cached_property
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
    favorites: Optional[int] = None
    views: Optional[int] = None

    @classmethod
    def from_json(cls, data: dict[str, Any], queries: list["OmniQuery"]) -> "OmniDocument":
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
            queries=queries,
            favorites=data.get("_count", {}).get("favorites", None),
            views=data.get("_count", {}).get("views", None),
        )


@whitelist_for_serdes
@record
class OmniQueryConfig:
    """Represents the essential query configuration needed for asset creation."""

    table: str
    fields: list[str]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniQueryConfig":
        """Create OmniQueryConfig from JSON query configuration data."""
        return cls(
            table=data["table"],
            fields=data["fields"],
        )


@whitelist_for_serdes
@record
class OmniQuery:
    id: str
    name: str
    query_config: OmniQueryConfig

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniQuery":
        """Create OmniQuery from JSON response data."""
        return cls(
            id=data["id"],
            name=data["name"],
            query_config=OmniQueryConfig.from_json(data["query"]),
        )


@whitelist_for_serdes
@record
class OmniUser:
    """Represents an Omni user with all user information in a single class."""

    id: str
    name: Optional[str]
    display_name: str
    user_name: str
    active: bool
    primary_email: Optional[str]
    groups: list[str]
    created: str
    last_modified: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniUser":
        """Create OmniUser from JSON response data."""
        primary_email = next(
            (email["value"] for email in data.get("emails", []) if email["primary"]), None
        )
        groups = [group["display"] for group in data.get("groups", [])]

        return cls(
            id=data["id"],
            name=data.get("displayName") or data.get("userName") or "",
            display_name=data.get("displayName", ""),
            user_name=data.get("userName", ""),
            active=data.get("active", True),
            primary_email=primary_email,
            groups=groups,
            created=data.get("meta", {}).get("created", ""),
            last_modified=data.get("meta", {}).get("lastModified", ""),
        )


@whitelist_for_serdes
@record
class OmniWorkspaceData:
    """Serializable container object for recording the state of the Omni API at a given point in time.

    Properties:
        documents: list[OmniDocument]
        users: list[OmniUser]
    """

    documents: list[OmniDocument]
    users: list[OmniUser]

    @cached_property
    def _users_by_id(self) -> dict[str, OmniUser]:
        return {user.id: user for user in self.users}

    def get_user(self, user_id: str) -> Optional[OmniUser]:
        return self._users_by_id.get(user_id)
