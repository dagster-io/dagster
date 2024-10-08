import re
import urllib.parse
from enum import Enum
from typing import Any, Dict, Literal, Optional, Sequence

from dagster import (
    UrlMetadataValue,
    _check as check,
)
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.tags import build_kind_tag
from dagster._core.definitions.tags.tag_set import NamespacedTagSet
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes


def _get_last_filepath_component(path: str) -> str:
    """Returns the last component of a file path."""
    return path.split("/")[-1].split("\\")[-1]


def _remove_file_ext(name: str) -> str:
    """Removes the file extension from a given name."""
    return name.rsplit(".", 1)[0]


def _clean_asset_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)


@whitelist_for_serdes
class PowerBIContentType(Enum):
    """Enum representing each object in PowerBI's ontology, generically referred to as "content" by the API."""

    DASHBOARD = "dashboard"
    REPORT = "report"
    SEMANTIC_MODEL = "semantic_model"
    DATA_SOURCE = "data_source"


@whitelist_for_serdes
@record
class PowerBIContentData:
    """A record representing a piece of content in PowerBI.
    Includes the content's type and data as returned from the API.
    """

    content_type: PowerBIContentType
    properties: Dict[str, Any]


@whitelist_for_serdes
@record
class PowerBIWorkspaceData:
    """A record representing all content in a PowerBI workspace.

    Provided as context for the translator so that it can resolve dependencies between content.
    """

    workspace_id: str
    dashboards_by_id: Dict[str, PowerBIContentData]
    reports_by_id: Dict[str, PowerBIContentData]
    semantic_models_by_id: Dict[str, PowerBIContentData]
    data_sources_by_id: Dict[str, PowerBIContentData]

    @classmethod
    def from_content_data(
        cls, workspace_id: str, content_data: Sequence[PowerBIContentData]
    ) -> "PowerBIWorkspaceData":
        return cls(
            workspace_id=workspace_id,
            dashboards_by_id={
                dashboard.properties["id"]: dashboard
                for dashboard in content_data
                if dashboard.content_type == PowerBIContentType.DASHBOARD
            },
            reports_by_id={
                report.properties["id"]: report
                for report in content_data
                if report.content_type == PowerBIContentType.REPORT
            },
            semantic_models_by_id={
                dataset.properties["id"]: dataset
                for dataset in content_data
                if dataset.content_type == PowerBIContentType.SEMANTIC_MODEL
            },
            data_sources_by_id={
                data_source.properties["datasourceId"]: data_source
                for data_source in content_data
                if data_source.content_type == PowerBIContentType.DATA_SOURCE
            },
        )


class PowerBITagSet(NamespacedTagSet):
    asset_type: Optional[Literal["dashboard", "report", "semantic_model", "data_source"]] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-powerbi"


class PowerBIMetadataSet(NamespacedMetadataSet):
    web_url: Optional[UrlMetadataValue] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-powerbi"


class DagsterPowerBITranslator:
    """Translator class which converts raw response data from the PowerBI API into AssetSpecs.
    Subclass this class to implement custom logic for each type of PowerBI content.
    """

    def __init__(self, context: PowerBIWorkspaceData):
        self._context = context

    @property
    def workspace_data(self) -> PowerBIWorkspaceData:
        return self._context

    def get_asset_spec(self, data: PowerBIContentData) -> AssetSpec:
        if data.content_type == PowerBIContentType.DASHBOARD:
            return self.get_dashboard_spec(data)
        elif data.content_type == PowerBIContentType.REPORT:
            return self.get_report_spec(data)
        elif data.content_type == PowerBIContentType.SEMANTIC_MODEL:
            return self.get_semantic_model_spec(data)
        elif data.content_type == PowerBIContentType.DATA_SOURCE:
            return self.get_data_source_spec(data)
        else:
            check.assert_never(data.content_type)

    def get_dashboard_asset_key(self, data: PowerBIContentData) -> AssetKey:
        return AssetKey(
            [
                "dashboard",
                _clean_asset_name(_remove_file_ext(data.properties["displayName"])),
            ]
        )

    def get_dashboard_spec(self, data: PowerBIContentData) -> AssetSpec:
        tile_report_ids = [
            tile["reportId"] for tile in data.properties["tiles"] if "reportId" in tile
        ]
        report_keys = [
            self.get_report_asset_key(self.workspace_data.reports_by_id[report_id])
            for report_id in tile_report_ids
        ]
        url = data.properties.get("webUrl")

        return AssetSpec(
            key=self.get_dashboard_asset_key(data),
            deps=report_keys,
            metadata={**PowerBIMetadataSet(web_url=MetadataValue.url(url) if url else None)},
            tags={**PowerBITagSet(asset_type="dashboard"), **build_kind_tag("powerbi")},
        )

    def get_report_asset_key(self, data: PowerBIContentData) -> AssetKey:
        return AssetKey(["report", _clean_asset_name(data.properties["name"])])

    def get_report_spec(self, data: PowerBIContentData) -> AssetSpec:
        dataset_id = data.properties["datasetId"]
        dataset_data = self.workspace_data.semantic_models_by_id.get(dataset_id)
        dataset_key = self.get_semantic_model_asset_key(dataset_data) if dataset_data else None
        url = data.properties.get("webUrl")

        return AssetSpec(
            key=self.get_report_asset_key(data),
            deps=[dataset_key] if dataset_key else None,
            metadata={**PowerBIMetadataSet(web_url=MetadataValue.url(url) if url else None)},
            tags={**PowerBITagSet(asset_type="report"), **build_kind_tag("powerbi")},
        )

    def get_semantic_model_asset_key(self, data: PowerBIContentData) -> AssetKey:
        return AssetKey(["semantic_model", _clean_asset_name(data.properties["name"])])

    def get_semantic_model_spec(self, data: PowerBIContentData) -> AssetSpec:
        source_ids = data.properties["sources"]
        source_keys = [
            self.get_data_source_asset_key(self.workspace_data.data_sources_by_id[source_id])
            for source_id in source_ids
        ]
        url = data.properties.get("webUrl")

        return AssetSpec(
            key=self.get_semantic_model_asset_key(data),
            deps=source_keys,
            metadata={**PowerBIMetadataSet(web_url=MetadataValue.url(url) if url else None)},
            tags={**PowerBITagSet(asset_type="semantic_model"), **build_kind_tag("powerbi")},
        )

    def get_data_source_asset_key(self, data: PowerBIContentData) -> AssetKey:
        connection_name = (
            data.properties["connectionDetails"].get("path")
            or data.properties["connectionDetails"].get("url")
            or data.properties["connectionDetails"].get("database")
        )
        if not connection_name:
            return AssetKey([_clean_asset_name(data.properties["datasourceId"])])

        obj_name = _get_last_filepath_component(urllib.parse.unquote(connection_name))
        return AssetKey(path=[_clean_asset_name(obj_name)])

    def get_data_source_spec(self, data: PowerBIContentData) -> AssetSpec:
        return AssetSpec(
            key=self.get_data_source_asset_key(data),
            tags={**PowerBITagSet(asset_type="data_source"), **build_kind_tag("powerbi")},
        )
