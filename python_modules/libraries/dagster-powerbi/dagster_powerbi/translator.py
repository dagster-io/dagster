import re
import urllib.parse
from enum import Enum
from typing import Any, Dict, Generic

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import record
from typing_extensions import TypeVar


def _get_last_filepath_component(path: str) -> str:
    """Returns the last component of a file path."""
    return path.split("/")[-1].split("\\")[-1]


def _remove_file_ext(name: str) -> str:
    """Removes the file extension from a given name."""
    return name.rsplit(".", 1)[0]


def _clean_asset_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name."""
    return re.sub(r"[^a-z0-9A-Z.]+", "_", name)


T = TypeVar("T")
U = TypeVar("U")


# scaffold out what a generic translator class might look like
class DagsterTranslator(Generic[T, U]):
    def __init__(self, context: U):
        self._context = context

    def get_asset_spec(self, data: T) -> AssetSpec:
        raise NotImplementedError


class PowerBIContentType(Enum):
    """Enum representing each object in PowerBI's ontology, generically referred to as "content" by the API."""

    DASHBOARD = "dashboard"
    REPORT = "report"
    SEMANTIC_MODEL = "semantic_model"
    DATA_SOURCE = "data_source"


@record
class PowerBIContentData:
    """A record representing a piece of content in PowerBI.
    Includes the content's type and data as returned from the API.
    """

    content_type: PowerBIContentType
    properties: Dict[str, Any]


@record
class PowerBIWorkspaceData:
    """A record representing all content in a PowerBI workspace.

    Provided as context for the translator so that it can resolve dependencies between content.
    """

    dashboards_by_id: Dict[str, PowerBIContentData]
    reports_by_id: Dict[str, PowerBIContentData]
    semantic_models_by_id: Dict[str, PowerBIContentData]
    data_sources_by_id: Dict[str, PowerBIContentData]


class DagsterPowerBITranslator(DagsterTranslator[PowerBIContentData, PowerBIWorkspaceData]):
    """Translator class which converts raw response data from the PowerBI API into AssetSpecs.
    Subclass this class to implement custom logic for each type of PowerBI content.
    """

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
            ["dashboard", _clean_asset_name(_remove_file_ext(data.properties["displayName"]))]
        )

    def get_dashboard_spec(self, data: PowerBIContentData) -> AssetSpec:
        tile_report_ids = [
            tile["reportId"] for tile in data.properties["tiles"] if "reportId" in tile
        ]
        report_keys = [
            self.get_report_asset_key(self.workspace_data.reports_by_id[report_id])
            for report_id in tile_report_ids
        ]

        return AssetSpec(
            key=self.get_dashboard_asset_key(data),
            tags={"dagster/storage_kind": "powerbi"},
            deps=report_keys,
        )

    def get_report_asset_key(self, data: PowerBIContentData) -> AssetKey:
        return AssetKey(["report", _clean_asset_name(data.properties["name"])])

    def get_report_spec(self, data: PowerBIContentData) -> AssetSpec:
        dataset_id = data.properties["datasetId"]
        dataset_data = self.workspace_data.semantic_models_by_id.get(dataset_id)
        dataset_key = self.get_semantic_model_asset_key(dataset_data) if dataset_data else None

        return AssetSpec(
            key=self.get_report_asset_key(data),
            deps=[dataset_key] if dataset_key else None,
            tags={"dagster/storage_kind": "powerbi"},
        )

    def get_semantic_model_asset_key(self, data: PowerBIContentData) -> AssetKey:
        return AssetKey(["semantic_model", _clean_asset_name(data.properties["name"])])

    def get_semantic_model_spec(self, data: PowerBIContentData) -> AssetSpec:
        source_ids = data.properties["sources"]
        source_keys = [
            self.get_data_source_asset_key(self.workspace_data.data_sources_by_id[source_id])
            for source_id in source_ids
        ]

        return AssetSpec(
            key=self.get_semantic_model_asset_key(data),
            tags={"dagster/storage_kind": "powerbi"},
            deps=source_keys,
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
            tags={"dagster/storage_kind": "powerbi"},
        )
