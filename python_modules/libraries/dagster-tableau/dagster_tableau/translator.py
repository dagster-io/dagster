import re
from enum import Enum
from typing import Any, Mapping, Sequence

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import record

TABLEAU_PREFIX = "tableau/"


def _clean_asset_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name."""
    return re.sub(r"[^a-z0-9A-Z.]+", "_", name).lower()


class TableauContentType(Enum):
    """Enum representing each object in Tableau's ontology."""

    WORKBOOK = "workbook"
    SHEET = "sheet"
    DASHBOARD = "dashboard"
    DATA_SOURCE = "data_source"


@record
class TableauContentData:
    """A record representing a piece of content in Tableau.
    Includes the content's type and data as returned from the API.
    """

    content_type: TableauContentType
    properties: Mapping[str, Any]

    def to_cached_data(self) -> Mapping[str, Any]:
        return {"content_type": self.content_type.value, "properties": self.properties}

    @classmethod
    def from_cached_data(cls, data: Mapping[Any, Any]) -> "TableauContentData":
        return cls(
            content_type=TableauContentType(data["content_type"]),
            properties=data["properties"],
        )


@record
class TableauWorkspaceData:
    """A record representing all content in a Tableau workspace.
    Provided as context for the translator so that it can resolve dependencies between content.
    """

    site_name: str
    workbooks_by_id: Mapping[str, TableauContentData]
    sheets_by_id: Mapping[str, TableauContentData]
    dashboards_by_id: Mapping[str, TableauContentData]
    data_sources_by_id: Mapping[str, TableauContentData]

    @classmethod
    def from_content_data(
        cls, site_name: str, content_data: Sequence[TableauContentData]
    ) -> "TableauWorkspaceData":
        return cls(
            site_name=site_name,
            workbooks_by_id={
                workbook.properties["luid"]: workbook
                for workbook in content_data
                if workbook.content_type == TableauContentType.WORKBOOK
            },
            sheets_by_id={
                sheet.properties["luid"]: sheet
                for sheet in content_data
                if sheet.content_type == TableauContentType.SHEET
            },
            dashboards_by_id={
                dashboard.properties["luid"]: dashboard
                for dashboard in content_data
                if dashboard.content_type == TableauContentType.DASHBOARD
            },
            data_sources_by_id={
                data_source.properties["luid"]: data_source
                for data_source in content_data
                if data_source.content_type == TableauContentType.DATA_SOURCE
            },
        )


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
        if data.content_type == TableauContentType.SHEET:
            return self.get_sheet_spec(data)
        elif data.content_type == TableauContentType.DASHBOARD:
            return self.get_dashboard_spec(data)
        elif data.content_type == TableauContentType.DATA_SOURCE:
            return self.get_data_source_spec(data)
        else:
            check.assert_never(data.content_type)

    def get_sheet_asset_key(self, data: TableauContentData) -> AssetKey:
        workbook_id = data.properties["workbook"]["luid"]
        workbook_data = self.workspace_data.workbooks_by_id[workbook_id]
        return AssetKey(
            [
                _clean_asset_name(workbook_data.properties["name"]),
                "sheet",
                _clean_asset_name(data.properties["name"]),
            ]
        )

    def get_sheet_spec(self, data: TableauContentData) -> AssetSpec:
        sheet_embedded_data_sources = data.properties.get("parentEmbeddedDatasources", [])
        data_source_ids = {
            published_data_source["luid"]
            for embedded_data_source in sheet_embedded_data_sources
            for published_data_source in embedded_data_source.get("parentPublishedDatasources", [])
        }

        data_source_keys = [
            self.get_data_source_asset_key(self.workspace_data.data_sources_by_id[data_source_id])
            for data_source_id in data_source_ids
        ]

        return AssetSpec(
            key=self.get_sheet_asset_key(data),
            deps=data_source_keys if data_source_keys else None,
            tags={"dagster/storage_kind": "tableau"},
        )

    def get_dashboard_asset_key(self, data: TableauContentData) -> AssetKey:
        workbook_id = data.properties["workbook"]["luid"]
        workbook_data = self.workspace_data.workbooks_by_id[workbook_id]
        return AssetKey(
            [
                _clean_asset_name(workbook_data.properties["name"]),
                "dashboard",
                _clean_asset_name(data.properties["name"]),
            ]
        )

    def get_dashboard_spec(self, data: TableauContentData) -> AssetSpec:
        dashboard_upstream_sheets = data.properties.get("sheets", [])
        sheet_ids = {sheet["luid"] for sheet in dashboard_upstream_sheets if sheet["luid"]}

        sheet_keys = [
            self.get_sheet_asset_key(self.workspace_data.sheets_by_id[sheet_id])
            for sheet_id in sheet_ids
        ]

        return AssetSpec(
            key=self.get_dashboard_asset_key(data),
            deps=sheet_keys if sheet_keys else None,
            tags={"dagster/storage_kind": "tableau"},
        )

    def get_data_source_asset_key(self, data: TableauContentData) -> AssetKey:
        return AssetKey([_clean_asset_name(data.properties["name"])])

    def get_data_source_spec(self, data: TableauContentData) -> AssetSpec:
        return AssetSpec(
            key=self.get_data_source_asset_key(data),
            tags={"dagster/storage_kind": "tableau"},
        )
