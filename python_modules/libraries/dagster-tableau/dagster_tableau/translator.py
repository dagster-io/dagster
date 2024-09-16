from enum import Enum
from typing import Any, Mapping

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import record


class TableauContentType(Enum):
    """Enum representing each object in Tableau's ontology."""

    WORKBOOK = "workbook"
    VIEW = "view"
    DATA_SOURCE = "data_source"


@record
class TableauContentData:
    """A record representing a piece of content in Tableau.
    Includes the content's type and data as returned from the API.
    """

    content_type: TableauContentType
    properties: Mapping[str, Any]


@record
class TableauWorkspaceData:
    """A record representing all content in a Tableau workspace.
    Provided as context for the translator so that it can resolve dependencies between content.
    """

    site_name: str
    workbooks_by_id: Mapping[str, TableauContentData]
    views_by_id: Mapping[str, TableauContentData]
    data_sources_by_id: Mapping[str, TableauContentData]


class DagsterTableauTranslator:
    """Translator class which converts raw response data from the Tableau API into AssetSpecs.
    Subclass this class to implement custom logic for each type of Tableau content.
    """

    def __init__(self, context: TableauWorkspaceData):
        self._context = context

    @property
    def workspace_data(self) -> TableauWorkspaceData:
        return self._context

    def get_asset_spec(self, data: TableauContentData) -> AssetSpec:
        if data.content_type == TableauContentType.VIEW:
            return self.get_view_spec(data)
        elif data.content_type == TableauContentType.DATA_SOURCE:
            return self.get_data_source_spec(data)
        else:
            check.assert_never(data.content_type)

    def get_view_asset_key(self, data: TableauContentData) -> AssetKey: ...
    def get_view_spec(self, data: TableauContentData) -> AssetSpec: ...

    def get_data_source_asset_key(self, data: TableauContentData) -> AssetKey: ...
    def get_data_source_spec(self, data: TableauContentData) -> AssetSpec: ...
