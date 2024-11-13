import re
from enum import Enum
from typing import Any, Literal, Mapping, Optional, Sequence

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster._core.definitions.tags.tag_set import NamespacedTagSet
from dagster._record import record
from dagster._serdes import whitelist_for_serdes

TABLEAU_PREFIX = "tableau/"


def _coerce_input_to_valid_name(name: str) -> str:
    """Cleans an input to be a valid Dagster name."""
    return re.sub(r"[^a-z0-9A-Z.]+", "_", name).lower()


@whitelist_for_serdes
class TableauContentType(Enum):
    """Enum representing each object in Tableau's ontology."""

    WORKBOOK = "workbook"
    SHEET = "sheet"
    DASHBOARD = "dashboard"
    DATA_SOURCE = "data_source"


@whitelist_for_serdes
@record
class TableauContentData:
    """A record representing a piece of content in Tableau.
    Includes the content's type and data as returned from the API.
    """

    content_type: TableauContentType
    properties: Mapping[str, Any]


@whitelist_for_serdes
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


class TableauTagSet(NamespacedTagSet):
    asset_type: Optional[Literal["dashboard", "data_source", "sheet"]] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-tableau"


class TableauMetadataSet(NamespacedMetadataSet):
    id: Optional[str] = None
    workbook_id: Optional[str] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-tableau"


class DagsterTableauTranslator:
    """Translator class which converts raw response data from the Tableau API into AssetSpecs.
    Subclass this class to implement custom logic for each type of Tableau content.
    """

    def __init__(self, context: TableauWorkspaceData):
        self._context = context

    @property
    def workspace_data(self) -> TableauWorkspaceData:
        return self._context

    def get_asset_key(self, data: TableauContentData) -> AssetKey:
        if data.content_type == TableauContentType.SHEET:
            return self.get_sheet_asset_key(data)
        elif data.content_type == TableauContentType.DASHBOARD:
            return self.get_dashboard_asset_key(data)
        elif data.content_type == TableauContentType.DATA_SOURCE:
            return self.get_data_source_asset_key(data)
        else:
            check.assert_never(data.content_type)

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
                _coerce_input_to_valid_name(workbook_data.properties["name"]),
                "sheet",
                _coerce_input_to_valid_name(data.properties["name"]),
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
            self.get_asset_key(self.workspace_data.data_sources_by_id[data_source_id])
            for data_source_id in data_source_ids
        ]

        return AssetSpec(
            key=self.get_asset_key(data),
            deps=data_source_keys if data_source_keys else None,
            tags={"dagster/storage_kind": "tableau", **TableauTagSet(asset_type="sheet")},
            metadata={
                **TableauMetadataSet(
                    id=data.properties["luid"], workbook_id=data.properties["workbook"]["luid"]
                )
            },
        )

    def get_dashboard_asset_key(self, data: TableauContentData) -> AssetKey:
        workbook_id = data.properties["workbook"]["luid"]
        workbook_data = self.workspace_data.workbooks_by_id[workbook_id]
        return AssetKey(
            [
                _coerce_input_to_valid_name(workbook_data.properties["name"]),
                "dashboard",
                _coerce_input_to_valid_name(data.properties["name"]),
            ]
        )

    def get_dashboard_spec(self, data: TableauContentData) -> AssetSpec:
        dashboard_upstream_sheets = data.properties.get("sheets", [])
        sheet_ids = {sheet["luid"] for sheet in dashboard_upstream_sheets if sheet["luid"]}

        sheet_keys = [
            self.get_asset_key(self.workspace_data.sheets_by_id[sheet_id]) for sheet_id in sheet_ids
        ]

        return AssetSpec(
            key=self.get_asset_key(data),
            deps=sheet_keys if sheet_keys else None,
            tags={"dagster/storage_kind": "tableau", **TableauTagSet(asset_type="dashboard")},
            metadata={
                **TableauMetadataSet(
                    id=data.properties["luid"], workbook_id=data.properties["workbook"]["luid"]
                )
            },
        )

    def get_data_source_asset_key(self, data: TableauContentData) -> AssetKey:
        return AssetKey([_coerce_input_to_valid_name(data.properties["name"])])

    def get_data_source_spec(self, data: TableauContentData) -> AssetSpec:
        return AssetSpec(
            key=self.get_asset_key(data),
            tags={"dagster/storage_kind": "tableau", **TableauTagSet(asset_type="data_source")},
            metadata={**TableauMetadataSet(id=data.properties["luid"], workbook_id=None)},
        )
