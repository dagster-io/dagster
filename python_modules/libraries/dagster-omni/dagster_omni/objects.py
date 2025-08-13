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
class OmniDocumentCount:
    favorites: int
    views: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniDocumentCount":
        """Create OmniDocumentCount from JSON response data."""
        return cls(favorites=data["favorites"], views=data["views"])


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
    count: Optional[OmniDocumentCount]
    query_ids: list[str]

    @classmethod
    def from_json(
        cls, data: dict[str, Any], query_ids: Optional[list[str]] = None
    ) -> "OmniDocument":
        """Create OmniDocument from JSON response data."""
        folder = None
        if data.get("folder"):
            folder = OmniFolder.from_json(data["folder"])

        labels = [OmniLabel.from_json(label_data) for label_data in data.get("labels", [])]

        owner = OmniOwner.from_json(data["owner"])

        count = None
        if data.get("_count"):
            count = OmniDocumentCount.from_json(data["_count"])

        return cls(
            identifier=data["identifier"],
            name=data["name"],
            scope=data["scope"],
            connection_id=data["connectionId"],
            deleted=data["deleted"],
            has_dashboard=data["hasDashboard"],
            type=data.get("type", "document"),  # Default to "document" if missing
            updated_at=data["updatedAt"],
            owner=owner,
            folder=folder,
            labels=labels,
            count=count,
            query_ids=query_ids or [],
        )


@whitelist_for_serdes
@record
class OmniPageInfo:
    has_next_page: bool
    next_cursor: Optional[str]
    page_size: int
    total_records: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniPageInfo":
        """Create OmniPageInfo from JSON response data."""
        return cls(
            has_next_page=data["hasNextPage"],
            next_cursor=data.get("nextCursor"),
            page_size=data["pageSize"],
            total_records=data["totalRecords"],
        )


@whitelist_for_serdes
@record
class OmniQueryConfig:
    """Represents the nested query configuration object."""

    table: Optional[str]
    fields: list[str]
    filters: dict[str, Any]
    sorts: list[dict[str, Any]]
    pivots: list[str]
    calculations: list[dict[str, Any]]
    model_id: Optional[str]
    limit: Optional[int]
    version: Optional[int]
    manual_sort: Optional[bool]
    rewrite_sql: Optional[bool]
    user_edited_sql: Optional[str]
    column_limit: Optional[int]
    default_group_by: Optional[bool]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "OmniQueryConfig":
        """Create OmniQueryConfig from JSON query configuration data."""
        return cls(
            table=data.get("table"),
            fields=data.get("fields", []),
            filters=data.get("filters", {}),
            sorts=data.get("sorts", []),
            pivots=data.get("pivots", []),
            calculations=data.get("calculations", []),
            model_id=data.get("modelId"),
            limit=data.get("limit"),
            version=data.get("version"),
            manual_sort=data.get("manualSort"),
            rewrite_sql=data.get("rewriteSql"),
            user_edited_sql=data.get("userEditedSQL"),
            column_limit=data.get("column_limit"),
            default_group_by=data.get("default_group_by"),
        )


@whitelist_for_serdes
@record
class OmniQuery:
    id: str
    name: str
    query_config: Optional[OmniQueryConfig]
    query_identifier_map_key: Optional[str]
    description: Optional[str]
    query_type: str
    created_at: str
    updated_at: str

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
            query_identifier_map_key=data.get("queryIdentifierMapKey"),
            description=data.get("description"),
            query_type=data.get("queryType", "unknown"),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
        )


@whitelist_for_serdes
@record
class OmniState:
    documents: list[OmniDocument]
    queries: list[OmniQuery]

    @classmethod
    def from_json(
        cls,
        documents_data: list[dict[str, Any]],
        queries_data: list[dict[str, Any]],
    ) -> "OmniState":
        """Create OmniState from JSON data."""
        documents = [OmniDocument.from_json(doc_data) for doc_data in documents_data]
        queries = [OmniQuery.from_json(query_data) for query_data in queries_data]

        return cls(documents=documents, queries=queries)

    @cached_property
    def _queries_by_id(self) -> dict[str, OmniQuery]:
        return {query.id: query for query in self.queries}

    def get_query_by_id(self, id: str) -> Optional[OmniQuery]:
        return self._queries_by_id.get(id)
