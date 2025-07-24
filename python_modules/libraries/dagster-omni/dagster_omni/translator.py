from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from dagster import AssetKey, AssetSpec
from dagster._record import record
from dagster._utils.names import clean_name
from dagster_shared.serdes.serdes import whitelist_for_serdes

_clean_asset_name = clean_name


@whitelist_for_serdes
class OmniContentType(Enum):
    """Enumeration of Omni content types that can be represented as Dagster assets."""

    MODEL = "model"
    WORKBOOK = "workbook"
    QUERY = "query"


@whitelist_for_serdes
@record
class OmniContentData:
    """Represents a single piece of Omni content with its properties."""

    content_type: OmniContentType
    properties: Mapping[str, Any]


@whitelist_for_serdes
@record
class OmniWorkspaceData:
    """Represents the data from an Omni workspace, containing all content organized by type."""

    workspace_url: str
    models_by_id: Mapping[str, OmniContentData]
    workbooks_by_id: Mapping[str, OmniContentData]
    queries_by_id: Mapping[str, OmniContentData]

    @classmethod
    def from_content_data(
        cls, workspace_url: str, content_data: Sequence[OmniContentData]
    ) -> "OmniWorkspaceData":
        """Create OmniWorkspaceData from a sequence of content data objects."""
        models_by_id = {}
        workbooks_by_id = {}
        queries_by_id = {}

        for content in content_data:
            # For documents, use 'identifier', for models use 'id'
            content_id = content.properties.get("identifier") or content.properties.get("id")
            if not content_id:
                continue

            if content.content_type == OmniContentType.MODEL:
                models_by_id[content_id] = content
            elif content.content_type == OmniContentType.WORKBOOK:
                workbooks_by_id[content_id] = content
            elif content.content_type == OmniContentType.QUERY:
                queries_by_id[content_id] = content

        return cls(
            workspace_url=workspace_url,
            models_by_id=models_by_id,
            workbooks_by_id=workbooks_by_id,
            queries_by_id=queries_by_id,
        )


@record
class OmniTranslatorData:
    """Contains all the data needed for the translator to convert Omni content to Dagster asset specs."""

    content_data: OmniContentData
    workspace_data: OmniWorkspaceData

    @property
    def content_type(self) -> OmniContentType:
        return self.content_data.content_type

    @property
    def properties(self) -> Mapping[str, Any]:
        return self.content_data.properties


class DagsterOmniTranslator:
    """Translates Omni content into Dagster asset specs.

    This class can be subclassed to customize how Omni content is represented in Dagster.
    """

    def get_asset_spec(self, data: OmniTranslatorData) -> AssetSpec:
        """Get the asset spec for a given piece of Omni content."""
        if data.content_type == OmniContentType.MODEL:
            return self.get_model_spec(data)
        elif data.content_type == OmniContentType.WORKBOOK:
            return self.get_workbook_spec(data)
        elif data.content_type == OmniContentType.QUERY:
            return self.get_query_spec(data)
        else:
            raise ValueError(f"Unknown content type: {data.content_type}")

    def get_model_spec(self, data: OmniTranslatorData) -> AssetSpec:
        """Get the asset spec for an Omni model."""
        properties = data.properties
        name = properties.get("name", "unknown")
        content_id = properties.get("id") or properties.get("identifier") or "unknown"

        return AssetSpec(
            key=AssetKey(["omni", "model", _clean_asset_name(f"{name}_{content_id}")]),
            description=f"Omni Model: {name}. Data model providing structured access to underlying data sources.",
            metadata={
                "dagster_omni/id": content_id,
                "dagster_omni/workspace_url": data.workspace_data.workspace_url,
                "dagster_omni/content_type": "model",
                "dagster_omni/name": name,
                **{
                    f"dagster_omni/{k}": v
                    for k, v in properties.items()
                    if k in ["createdAt", "updatedAt", "description"]
                },
            },
            tags={"dagster_omni/asset_type": "model"},
            kinds={"omni", "model"},
        )

    def get_workbook_spec(self, data: OmniTranslatorData) -> AssetSpec:
        """Get the asset spec for an Omni workbook."""
        properties = data.properties
        name = properties.get("name", "unknown")
        content_id = properties.get("identifier") or properties.get("id") or "unknown"

        # Build dependencies - workbooks can depend on models via connectionId
        deps = []
        connection_id = properties.get("connectionId")
        if connection_id:
            for model_content in data.workspace_data.models_by_id.values():
                if model_content.properties.get("connectionId") == connection_id:
                    model_name = model_content.properties.get("name", "unknown")
                    model_id = (
                        model_content.properties.get("id")
                        or model_content.properties.get("identifier")
                        or "unknown"
                    )
                    deps.append(
                        AssetKey(["omni", "model", _clean_asset_name(f"{model_name}_{model_id}")])
                    )

        return AssetSpec(
            key=AssetKey(["omni", "workbook", _clean_asset_name(f"{name}_{content_id}")]),
            description=f"Omni Workbook: {name}. Analysis workbook containing queries and visualizations.",
            metadata={
                "dagster_omni/id": content_id,
                "dagster_omni/workspace_url": data.workspace_data.workspace_url,
                "dagster_omni/content_type": "workbook",
                "dagster_omni/name": name,
                **{
                    f"dagster_omni/{k}": v
                    for k, v in properties.items()
                    if k in ["createdAt", "updatedAt", "scope", "folder"]
                },
            },
            tags={"dagster_omni/asset_type": "workbook"},
            kinds={"omni", "workbook"},
            deps=deps,
        )

    def get_query_spec(self, data: OmniTranslatorData) -> AssetSpec:
        """Get the asset spec for an Omni query."""
        properties = data.properties
        name = properties.get("name", "unknown")
        content_id = properties.get("identifier") or properties.get("id") or "unknown"

        # Build dependencies - queries depend on the workbook they belong to
        deps = []
        workbook_id = properties.get("workbook_id")
        if workbook_id and workbook_id in data.workspace_data.workbooks_by_id:
            workbook_content = data.workspace_data.workbooks_by_id[workbook_id]
            workbook_name = workbook_content.properties.get("name", "unknown")
            deps.append(
                AssetKey(["omni", "workbook", _clean_asset_name(f"{workbook_name}_{workbook_id}")])
            )

        return AssetSpec(
            key=AssetKey(["omni", "query", _clean_asset_name(f"{name}_{content_id}")]),
            description=f"Omni Query: {name}. Executable query that produces analytical results.",
            metadata={
                "dagster_omni/id": content_id,
                "dagster_omni/workspace_url": data.workspace_data.workspace_url,
                "dagster_omni/content_type": "query",
                "dagster_omni/name": name,
                **{
                    f"dagster_omni/{k}": v
                    for k, v in properties.items()
                    if k in ["createdAt", "updatedAt", "workbook_name"]
                },
            },
            tags={"dagster_omni/asset_type": "query"},
            kinds={"omni", "query"},
            deps=deps,
        )
