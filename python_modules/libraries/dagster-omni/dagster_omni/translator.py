from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from dagster import AssetKey, AssetSpec
from dagster._record import record


class OmniContentType(Enum):
    """Enumeration of Omni content types that can be represented as Dagster assets."""

    MODEL = "model"
    WORKBOOK = "workbook"
    QUERY = "query"


@record
class OmniContentData:
    """Represents a single piece of Omni content with its properties."""

    content_type: OmniContentType
    properties: Mapping[str, Any]


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
class OmniMetadataSet:
    """Set of metadata values that can be associated with a Dagster asset spec."""

    id: str
    workspace_url: str

    @classmethod
    def extract(cls, metadata_by_key: Mapping[str, Any]) -> "OmniMetadataSet":
        return cls(
            id=metadata_by_key["dagster_omni/id"],
            workspace_url=metadata_by_key["dagster_omni/workspace_url"],
        )


@record
class OmniTagSet:
    """Set of tag values that can be associated with a Dagster asset spec."""

    asset_type: str

    @classmethod
    def extract(cls, tags_by_key: Mapping[str, str]) -> "OmniTagSet":
        return cls(asset_type=tags_by_key["dagster_omni/asset_type"])


@record
class OmniTranslatorData:
    """Contains all the data needed for the translator to convert Omni content to Dagster asset specs."""

    content_data: OmniContentData
    workspace_data: OmniWorkspaceData


class DagsterOmniTranslator(ABC):
    """Translates Omni content into Dagster asset specs.

    This class can be subclassed to customize how Omni content is represented in Dagster.
    """

    def get_asset_spec(self, data: OmniTranslatorData) -> AssetSpec:
        """Get the asset spec for a given piece of Omni content."""
        content = data.content_data

        if content.content_type == OmniContentType.MODEL:
            return self.get_model_asset_spec(data)
        elif content.content_type == OmniContentType.WORKBOOK:
            return self.get_workbook_asset_spec(data)
        elif content.content_type == OmniContentType.QUERY:
            return self.get_query_asset_spec(data)
        else:
            raise ValueError(f"Unknown content type: {content.content_type}")

    @abstractmethod
    def get_model_asset_spec(self, data: OmniTranslatorData) -> AssetSpec:
        """Get the asset spec for an Omni model."""
        ...

    @abstractmethod
    def get_workbook_asset_spec(self, data: OmniTranslatorData) -> AssetSpec:
        """Get the asset spec for an Omni workbook."""
        ...

    @abstractmethod
    def get_query_asset_spec(self, data: OmniTranslatorData) -> AssetSpec:
        """Get the asset spec for an Omni query."""
        ...

    def get_asset_key(
        self, content_type: OmniContentType, properties: Mapping[str, Any]
    ) -> AssetKey:
        """Get the asset key for a given piece of Omni content."""
        name = properties.get("name", "unknown")
        # For documents, use 'identifier', for models use 'id'
        content_id = properties.get("identifier") or properties.get("id") or "unknown"

        # Create hierarchical asset keys: omni/{content_type}/{name}
        return AssetKey(["omni", content_type.value, f"{name}_{content_id}"])

    def get_description(self, content_type: OmniContentType, properties: Mapping[str, Any]) -> str:
        """Get a description for the Dagster asset."""
        name = properties.get("name", "Unknown")
        content_type_display = content_type.value.title()

        base_description = f"Omni {content_type_display}: {name}"

        # Add additional context based on content type
        if content_type == OmniContentType.MODEL:
            return f"{base_description}. Data model providing structured access to underlying data sources."
        elif content_type == OmniContentType.WORKBOOK:
            created_at = properties.get("createdAt", "")
            created_info = f" (created {created_at})" if created_at else ""
            return f"{base_description}. Analysis workbook containing queries and visualizations{created_info}."
        elif content_type == OmniContentType.QUERY:
            return f"{base_description}. Executable query that produces analytical results."

        return base_description

    def get_metadata(
        self, content_type: OmniContentType, properties: Mapping[str, Any], workspace_url: str
    ) -> Mapping[str, Any]:
        """Get metadata for the Dagster asset."""
        # For documents, use 'identifier', for models use 'id'
        content_id = properties.get("identifier") or properties.get("id") or "unknown"

        metadata = {
            "dagster_omni/id": content_id,
            "dagster_omni/workspace_url": workspace_url,
            "dagster_omni/content_type": content_type.value,
        }

        # Add content-specific metadata
        if "createdAt" in properties:
            metadata["dagster_omni/created_at"] = properties["createdAt"]
        if "updatedAt" in properties:
            metadata["dagster_omni/updated_at"] = properties["updatedAt"]
        if "name" in properties:
            metadata["dagster_omni/name"] = properties["name"]

        return metadata

    def get_tags(
        self, content_type: OmniContentType, properties: Mapping[str, Any]
    ) -> Mapping[str, str]:
        """Get tags for the Dagster asset."""
        return {
            "dagster_omni/asset_type": content_type.value,
        }

    def get_deps(self, data: OmniTranslatorData) -> Sequence[AssetKey]:
        """Get dependencies for the asset based on Omni content relationships."""
        content = data.content_data
        workspace_data = data.workspace_data
        deps = []

        if content.content_type == OmniContentType.WORKBOOK:
            # Documents (workbooks) can depend on models via connectionId
            connection_id = content.properties.get("connectionId")
            if connection_id:
                # Look for models that use the same connection
                for model_content in workspace_data.models_by_id.values():
                    if model_content.properties.get("connectionId") == connection_id:
                        deps.append(
                            self.get_asset_key(OmniContentType.MODEL, model_content.properties)
                        )

        elif content.content_type == OmniContentType.QUERY:
            # Queries depend on the workbook they belong to
            workbook_id = content.properties.get("workbook_id")
            if workbook_id and workbook_id in workspace_data.workbooks_by_id:
                workbook_content = workspace_data.workbooks_by_id[workbook_id]
                deps.append(
                    self.get_asset_key(OmniContentType.WORKBOOK, workbook_content.properties)
                )

        return deps


class DefaultOmniTranslator(DagsterOmniTranslator):
    """Default implementation of the Omni translator."""

    def get_model_asset_spec(self, data: OmniTranslatorData) -> AssetSpec:
        content = data.content_data
        properties = content.properties
        workspace_data = data.workspace_data

        return AssetSpec(
            key=self.get_asset_key(OmniContentType.MODEL, properties),
            description=self.get_description(OmniContentType.MODEL, properties),
            metadata=self.get_metadata(
                OmniContentType.MODEL, properties, workspace_data.workspace_url
            ),
            tags=self.get_tags(OmniContentType.MODEL, properties),
            deps=self.get_deps(data),
        )

    def get_workbook_asset_spec(self, data: OmniTranslatorData) -> AssetSpec:
        content = data.content_data
        properties = content.properties
        workspace_data = data.workspace_data

        return AssetSpec(
            key=self.get_asset_key(OmniContentType.WORKBOOK, properties),
            description=self.get_description(OmniContentType.WORKBOOK, properties),
            metadata=self.get_metadata(
                OmniContentType.WORKBOOK, properties, workspace_data.workspace_url
            ),
            tags=self.get_tags(OmniContentType.WORKBOOK, properties),
            deps=self.get_deps(data),
        )

    def get_query_asset_spec(self, data: OmniTranslatorData) -> AssetSpec:
        content = data.content_data
        properties = content.properties
        workspace_data = data.workspace_data

        return AssetSpec(
            key=self.get_asset_key(OmniContentType.QUERY, properties),
            description=self.get_description(OmniContentType.QUERY, properties),
            metadata=self.get_metadata(
                OmniContentType.QUERY, properties, workspace_data.workspace_url
            ),
            tags=self.get_tags(OmniContentType.QUERY, properties),
            deps=self.get_deps(data),
        )
