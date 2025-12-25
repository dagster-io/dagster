from collections.abc import Callable, Mapping, Sequence
from enum import Enum
from typing import Any, Literal, Optional, TypeAlias

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster._core.definitions.tags.tag_set import NamespacedTagSet
from dagster._record import record
from dagster._serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method
from dagster._utils.names import clean_name_lower

TABLEAU_PREFIX = "tableau/"

_coerce_input_to_valid_name = clean_name_lower


WorkbookSelectorFn: TypeAlias = Callable[["TableauWorkbookMetadata"], bool]


def get_data_source_ids_from_sheet_props(props: Mapping[str, Any]) -> set[str]:
    sheet_embedded_data_sources = props.get("parentEmbeddedDatasources", [])

    data_source_ids = set()
    # If published data sources are available (i.e., parentPublishedDatasources exists and is not empty),
    # it means you can form the lineage by using the luid of those published sources.
    # If the published data sources are missing, you create assets for embedded data sources by using their id.
    for embedded_data_source in sheet_embedded_data_sources:
        published_data_source_list = embedded_data_source.get("parentPublishedDatasources", [])
        for published_data_source in published_data_source_list:
            data_source_ids.add(published_data_source["luid"])
        if not published_data_source_list:
            data_source_ids.add(embedded_data_source["id"])
    return data_source_ids


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
class TableauWorkbookMetadata:
    """Represents the metadata of a Tableau workbook, based on data as returned from the API."""

    id: str
    project_name: str
    project_id: str

    @classmethod
    def from_workbook_properties(
        cls,
        workbook_properties: Mapping[str, Any],
    ) -> "TableauWorkbookMetadata":
        return cls(
            id=workbook_properties["luid"],
            project_name=workbook_properties["projectName"],
            project_id=workbook_properties["projectLuid"],
        )


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
                sheet.properties["luid"] or sheet.properties["id"]: sheet
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

    # Cache workspace data selection for a specific workbook_selector_fn
    @cached_method
    def to_workspace_data_selection(
        self, workbook_selector_fn: Optional[WorkbookSelectorFn]
    ) -> "TableauWorkspaceData":
        if not workbook_selector_fn:
            return self

        workbooks_by_id_selection = {}
        for workbook_id, workbook in self.workbooks_by_id.items():
            tableau_workbook_metadata = TableauWorkbookMetadata.from_workbook_properties(
                workbook_properties=workbook.properties
            )
            if workbook_selector_fn(tableau_workbook_metadata):
                workbooks_by_id_selection[workbook_id] = workbook

        workbook_ids_selection = set(workbooks_by_id_selection.keys())

        sheets_by_id_selection = {
            sheet_id: sheet
            for sheet_id, sheet in self.sheets_by_id.items()
            if sheet.properties["workbook"]["luid"] in workbook_ids_selection
        }
        dashboards_by_id_selection = {
            dashboard_id: dashboard
            for dashboard_id, dashboard in self.dashboards_by_id.items()
            if dashboard.properties["workbook"]["luid"] in workbook_ids_selection
        }

        data_source_ids_selection = set()
        for sheet in sheets_by_id_selection.values():
            sheet_data_source_ids = get_data_source_ids_from_sheet_props(props=sheet.properties)
            data_source_ids_selection.update(sheet_data_source_ids)

        data_sources_by_id_selection = {
            data_source_id: data_source
            for data_source_id, data_source in self.data_sources_by_id.items()
            if data_source.properties["luid"] in data_source_ids_selection
        }

        return TableauWorkspaceData(
            site_name=self.site_name,
            workbooks_by_id=workbooks_by_id_selection,
            sheets_by_id=sheets_by_id_selection,
            dashboards_by_id=dashboards_by_id_selection,
            data_sources_by_id=data_sources_by_id_selection,
        )


class TableauTagSet(NamespacedTagSet):
    asset_type: Optional[Literal["dashboard", "data_source", "sheet"]] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-tableau"


class TableauMetadataSet(NamespacedMetadataSet):
    id: Optional[str] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-tableau"


class TableauViewMetadataSet(TableauMetadataSet):
    workbook_id: str
    project_name: str
    project_id: str


class TableauDataSourceMetadataSet(TableauMetadataSet):
    has_extracts: bool = False
    is_published: bool
    workbook_id: Optional[str] = None


class DagsterTableauTranslator:
    """Translator class which converts raw response data from the Tableau API into AssetSpecs.
    Subclass this class to implement custom logic for each type of Tableau content.
    """

    def get_asset_spec(self, data: TableauTranslatorData) -> AssetSpec:
        if data.content_type == TableauContentType.SHEET:
            return self.get_sheet_spec(data)
        elif data.content_type == TableauContentType.DASHBOARD:
            return self.get_dashboard_spec(data)
        elif data.content_type == TableauContentType.DATA_SOURCE:
            return self.get_data_source_spec(data)
        else:
            # switch back to check.assert_never when TableauContentType.WORKBOOK is handled
            check.failed(f"unhandled type {data.content_type}")

    def get_sheet_spec(self, data: TableauTranslatorData) -> AssetSpec:
        data_source_ids = get_data_source_ids_from_sheet_props(props=data.properties)

        data_source_keys = [
            self.get_asset_spec(
                TableauTranslatorData(
                    content_data=data.workspace_data.data_sources_by_id[data_source_id],
                    workspace_data=data.workspace_data,
                )
            ).key
            for data_source_id in data_source_ids
            if data_source_id in data.workspace_data.data_sources_by_id
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
                **TableauViewMetadataSet(
                    id=data.properties["luid"],
                    workbook_id=data.properties["workbook"]["luid"],
                    project_name=workbook_data.properties["projectName"],
                    project_id=workbook_data.properties["projectLuid"],
                )
            },
            kinds={"tableau", "sheet"},
        )

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
            if sheet_id in data.workspace_data.sheets_by_id
        ]

        dashboard_upstream_data_source_ids = data.properties.get("data_source_ids", [])

        data_source_keys = [
            self.get_asset_spec(
                TableauTranslatorData(
                    content_data=data.workspace_data.data_sources_by_id[data_source_id],
                    workspace_data=data.workspace_data,
                )
            ).key
            for data_source_id in dashboard_upstream_data_source_ids
            if data_source_id in data.workspace_data.data_sources_by_id
        ]

        upstream_keys = sheet_keys + data_source_keys

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
            deps=upstream_keys if upstream_keys else None,
            tags={"dagster/storage_kind": "tableau", **TableauTagSet(asset_type="dashboard")},
            metadata={
                **TableauViewMetadataSet(
                    id=data.properties["luid"],
                    workbook_id=data.properties["workbook"]["luid"],
                    project_name=workbook_data.properties["projectName"],
                    project_id=workbook_data.properties["projectLuid"],
                )
            },
            kinds={"tableau", "dashboard"},
        )

    def get_data_source_spec(self, data: TableauTranslatorData) -> AssetSpec:
        kinds = {
            "tableau",
            *["extract" if data.properties["hasExtracts"] else "live"],
            *["published datasource" if data.properties["isPublished"] else "embedded datasource"],
        }

        if data.properties["isPublished"]:
            asset_key = AssetKey([_coerce_input_to_valid_name(data.properties["name"])])
        else:
            workbook_id = data.properties["workbook"]["luid"]
            workbook_data = data.workspace_data.workbooks_by_id[workbook_id]
            asset_key = AssetKey(
                [
                    _coerce_input_to_valid_name(workbook_data.properties["name"]),
                    "embedded_datasource",
                    _coerce_input_to_valid_name(data.properties["name"]),
                ]
            )

        return AssetSpec(
            key=asset_key,
            tags={"dagster/storage_kind": "tableau", **TableauTagSet(asset_type="data_source")},
            metadata={
                **TableauDataSourceMetadataSet(
                    id=data.properties["luid"],
                    has_extracts=data.properties["hasExtracts"],
                    is_published=data.properties["isPublished"],
                    workbook_id=data.properties["workbook"]["luid"]
                    if not data.properties["isPublished"]
                    else None,
                )
            },
            kinds=kinds,
        )
