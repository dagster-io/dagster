from enum import Enum
from typing import Any, Dict, Generic

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import record
from typing_extensions import TypeVar

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
    data: Dict[str, Any]


@record
class PowerBIWorkspaceData:
    """A record representing all content in a PowerBI workspace.

    Provided as context for the translator so that it can resolve dependencies between content.
    """

    dashboards_by_id: Dict[str, PowerBIContentData]
    reports_by_id: Dict[str, PowerBIContentData]
    datasets_by_id: Dict[str, PowerBIContentData]
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

    def get_dashboard_asset_key(self, data: PowerBIContentData) -> AssetKey: ...
    def get_dashboard_spec(self, data: PowerBIContentData) -> AssetSpec: ...

    def get_report_asset_key(self, data: PowerBIContentData) -> AssetKey: ...
    def get_report_spec(self, data: PowerBIContentData) -> AssetSpec: ...

    def get_semantic_model_asset_key(self, data: PowerBIContentData) -> AssetKey: ...
    def get_semantic_model_spec(self, data: PowerBIContentData) -> AssetSpec: ...

    def get_data_source_asset_key(self, data: PowerBIContentData) -> AssetKey: ...
    def get_data_source_spec(self, data: PowerBIContentData) -> AssetSpec: ...
