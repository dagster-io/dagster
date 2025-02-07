import re
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Literal, Optional

from dagster import _check as check
from dagster._annotations import deprecated
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


@record
class TableauTranslatorData:
    """A record representing a piece of content in Tableau and the Tableau workspace data.
    Includes the content's type and data as returned from the API.
    """

    content_data: "TableauContentData"
    workspace_data: "TableauWorkspaceData"

    @property
    def content_type(self) -> TableauContentType:
        return self.content_data.content_type

    @property
    def properties(self) -> Mapping[str, Any]:
        return self.content_data.properties


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

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterTableauTranslator.get_asset_spec(...).key` instead",
    )
    def get_asset_key(self, data: TableauTranslatorData) -> AssetKey:
        return self.get_asset_spec(data).key

    def get_asset_spec(self, data: TableauTranslatorData) -> AssetSpec:
        if data.content_type == TableauContentType.SHEET:
            return self.get_sheet_spec(data)
        elif data.content_type == TableauContentType.DASHBOARD:
            return self.get_dashboard_spec(data)
        elif data.content_type == TableauContentType.DATA_SOURCE:
            return self.get_data_source_spec(data)
        else:
            check.assert_never(data.content_type)

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterTableauTranslator.get_asset_spec(...).key` instead",
    )
    def get_sheet_asset_key(self, data: TableauTranslatorData) -> AssetKey:
        return self.get_sheet_spec(data).key

    """ If published data sources are available (i.e., parentPublishedDatasources exists and is not empty), it means you can form the lineage by using the luid of those published sources.
    If the published data sources are missing, you create assets for embedded data sources by using their id.
    """

    def get_sheet_spec(self, data: TableauTranslatorData) -> AssetSpec:
        sheet_embedded_data_sources = data.properties.get("parentEmbeddedDatasources", [])

        data_source_ids = set()
        for embedded_data_source in sheet_embedded_data_sources:
            published_data_source_list = embedded_data_source.get("parentPublishedDatasources", [])
            for published_data_source in published_data_source_list:
                data_source_ids.add(published_data_source["luid"])
            if not published_data_source_list:
                data_source_ids.add(embedded_data_source["id"])

        data_source_keys = [
            self.get_asset_spec(
                TableauTranslatorData(
                    content_data=data.workspace_data.data_sources_by_id[data_source_id],
                    workspace_data=data.workspace_data,
                )
            ).key
            for data_source_id in data_source_ids
        ]

        workbook_id = data.properties["workbook"]["luid"]
        workbook_data = data.workspace_data.workbooks_by_id[workbook_id]
        asset_key = AssetKey(
            [
                _coerce_input_to_valid_name(workbook_data.properties["name"]),
                "sheet",
                _coerce_input_to_valid_name(data.properties["name"]),
            ]
        )

        return AssetSpec(
            key=asset_key,
            deps=data_source_keys if data_source_keys else None,
            tags={"dagster/storage_kind": "tableau", **TableauTagSet(asset_type="sheet")},
            metadata={
                **TableauMetadataSet(
                    id=data.properties["luid"], workbook_id=data.properties["workbook"]["luid"]
                )
            },
        )

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterTableauTranslator.get_asset_spec(...).key` instead",
    )
    def get_dashboard_asset_key(self, data: TableauTranslatorData) -> AssetKey:
        return self.get_dashboard_spec(data).key

    def get_dashboard_spec(self, data: TableauTranslatorData) -> AssetSpec:
        dashboard_upstream_sheets = data.properties.get("sheets", [])
        sheet_ids = {sheet["luid"] for sheet in dashboard_upstream_sheets if sheet["luid"]}

        sheet_keys = [
            self.get_asset_spec(
                TableauTranslatorData(
                    content_data=data.workspace_data.sheets_by_id[sheet_id],
                    workspace_data=data.workspace_data,
                )
            ).key
            for sheet_id in sheet_ids
        ]

        workbook_id = data.properties["workbook"]["luid"]
        workbook_data = data.workspace_data.workbooks_by_id[workbook_id]
        asset_key = AssetKey(
            [
                _coerce_input_to_valid_name(workbook_data.properties["name"]),
                "dashboard",
                _coerce_input_to_valid_name(data.properties["name"]),
            ]
        )

        return AssetSpec(
            key=asset_key,
            deps=sheet_keys if sheet_keys else None,
            tags={"dagster/storage_kind": "tableau", **TableauTagSet(asset_type="dashboard")},
            metadata={
                **TableauMetadataSet(
                    id=data.properties["luid"], workbook_id=data.properties["workbook"]["luid"]
                )
            },
        )

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterTableauTranslator.get_asset_spec(...).key` instead",
    )
    def get_data_source_asset_key(self, data: TableauTranslatorData) -> AssetKey:
        return self.get_data_source_spec(data).key

    def get_data_source_spec(self, data: TableauTranslatorData) -> AssetSpec:
        return AssetSpec(
            key=AssetKey([_coerce_input_to_valid_name(data.properties["name"])]),
            tags={"dagster/storage_kind": "tableau", **TableauTagSet(asset_type="data_source")},
            metadata={**TableauMetadataSet(id=data.properties["luid"], workbook_id=None)},
        )
