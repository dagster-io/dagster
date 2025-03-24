import re
import urllib.parse
from collections.abc import Sequence
from enum import Enum
from typing import Any, Literal, Optional

from dagster import (
    UrlMetadataValue,
    _check as check,
)
from dagster._annotations import deprecated
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet, TableMetadataSet
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.definitions.tags.tag_set import NamespacedTagSet
from dagster._core.definitions.utils import is_valid_asset_owner
from dagster._record import record
from dagster_shared.serdes import whitelist_for_serdes


def _get_last_filepath_component(path: str) -> str:
    """Returns the last component of a file path."""
    return path.split("/")[-1].split("\\")[-1]


def _remove_file_ext(name: str) -> str:
    """Removes the file extension from a given name."""
    return name.rsplit(".", 1)[0]


def _clean_asset_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)


# regex to find objects of form
# [Name="ANALYTICS",Kind="Schema"]
PARSE_M_QUERY_OBJECT = re.compile(r'\[Name="(?P<name>[^"]+)",Kind="(?P<kind>[^"]+)"\]')


def _attempt_parse_m_query_source(sources: list[dict[str, Any]]) -> Optional[AssetKey]:
    for source in sources:
        if "expression" in source:
            objects = PARSE_M_QUERY_OBJECT.findall(source["expression"])
            objects_by_kind = {obj[1]: obj[0].lower() for obj in objects}

            if "Schema" in objects_by_kind and "Table" in objects_by_kind:
                if "Database" in objects_by_kind:
                    return AssetKey(
                        [
                            objects_by_kind["Database"],
                            objects_by_kind["Schema"],
                            objects_by_kind["Table"],
                        ]
                    )
                else:
                    return AssetKey([objects_by_kind["Schema"], objects_by_kind["Table"]])


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
    properties: dict[str, Any]


@record
class PowerBITranslatorData:
    """A record representing a piece of content in PowerBI and the PowerBI workspace data.
    Includes the content's type and data as returned from the API.
    """

    content_data: "PowerBIContentData"
    workspace_data: "PowerBIWorkspaceData"

    @property
    def content_type(self) -> PowerBIContentType:
        return self.content_data.content_type

    @property
    def properties(self) -> dict[str, Any]:
        return self.content_data.properties


@whitelist_for_serdes
@record
class PowerBIWorkspaceData:
    """A record representing all content in a PowerBI workspace.

    Provided as context for the translator so that it can resolve dependencies between content.
    """

    workspace_id: str
    dashboards_by_id: dict[str, PowerBIContentData]
    reports_by_id: dict[str, PowerBIContentData]
    semantic_models_by_id: dict[str, PowerBIContentData]
    data_sources_by_id: dict[str, PowerBIContentData]

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
    id: Optional[str] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-powerbi"


def _build_table_metadata(table: dict[str, Any]) -> TableMetadataSet:
    return TableMetadataSet(
        table_name=table["name"],
        column_schema=TableSchema(
            columns=[
                TableColumn(name=column["name"].lower(), type=column.get("dataType"))
                for column in table["columns"]
            ]
        ),
    )


class DagsterPowerBITranslator:
    """Translator class which converts raw response data from the PowerBI API into AssetSpecs.
    Subclass this class to implement custom logic for each type of PowerBI content.
    """

    def get_asset_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        data = check.inst(data, PowerBITranslatorData)
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

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterPowerBITranslator.get_asset_spec(...).key` instead",
    )
    def get_dashboard_asset_key(self, data: PowerBITranslatorData) -> AssetKey:
        data = check.inst(data, PowerBITranslatorData)
        return self.get_dashboard_spec(data).key

    def get_dashboard_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        data = check.inst(data, PowerBITranslatorData)
        dashboard_id = data.properties["id"]
        tile_report_ids = [
            tile["reportId"] for tile in data.properties["tiles"] if "reportId" in tile
        ]
        report_keys = [
            self.get_report_spec(
                PowerBITranslatorData(
                    content_data=data.workspace_data.reports_by_id[report_id],
                    workspace_data=data.workspace_data,
                )
            ).key
            for report_id in tile_report_ids
        ]
        url = (
            data.properties.get("webUrl")
            or f"https://app.powerbi.com/groups/{data.workspace_data.workspace_id}/dashboards/{dashboard_id}"
        )

        return AssetSpec(
            key=AssetKey(
                [
                    "dashboard",
                    _clean_asset_name(_remove_file_ext(data.properties["displayName"])),
                ]
            ),
            deps=report_keys,
            metadata={**PowerBIMetadataSet(web_url=MetadataValue.url(url) if url else None)},
            tags={**PowerBITagSet(asset_type="dashboard")},
            kinds={"powerbi", "dashboard"},
        )

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterPowerBITranslator.get_asset_spec(...).key` instead",
    )
    def get_report_asset_key(self, data: PowerBITranslatorData) -> AssetKey:
        data = check.inst(data, PowerBITranslatorData)
        return self.get_report_spec(data).key

    def get_report_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        data = check.inst(data, PowerBITranslatorData)
        report_id = data.properties["id"]
        dataset_id = data.properties.get("datasetId")
        dataset_data = (
            data.workspace_data.semantic_models_by_id.get(dataset_id) if dataset_id else None
        )
        dataset_key = (
            self.get_semantic_model_spec(
                PowerBITranslatorData(
                    content_data=dataset_data,
                    workspace_data=data.workspace_data,
                )
            ).key
            if dataset_data
            else None
        )
        url = (
            data.properties.get("webUrl")
            or f"https://app.powerbi.com/groups/{data.workspace_data.workspace_id}/reports/{report_id}"
        )

        owner = data.properties.get("createdBy")

        return AssetSpec(
            key=AssetKey(["report", _clean_asset_name(data.properties["name"])]),
            deps=[dataset_key] if dataset_key else None,
            metadata={**PowerBIMetadataSet(web_url=MetadataValue.url(url) if url else None)},
            tags={**PowerBITagSet(asset_type="report")},
            kinds={"powerbi", "report"},
            owners=[owner] if owner and is_valid_asset_owner(owner) else None,
        )

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterPowerBITranslator.get_asset_spec(...).key` instead",
    )
    def get_semantic_model_asset_key(self, data: PowerBITranslatorData) -> AssetKey:
        data = check.inst(data, PowerBITranslatorData)
        return self.get_semantic_model_spec(data).key

    def get_semantic_model_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        data = check.inst(data, PowerBITranslatorData)
        dataset_id = data.properties["id"]
        source_ids = data.properties.get("sources", [])
        source_keys = [
            self.get_data_source_spec(
                PowerBITranslatorData(
                    content_data=data.workspace_data.data_sources_by_id[source_id],
                    workspace_data=data.workspace_data,
                )
            ).key
            for source_id in source_ids
        ]
        url = (
            data.properties.get("webUrl")
            or f"https://app.powerbi.com/groups/{data.workspace_data.workspace_id}/datasets/{dataset_id}"
        )

        for table in data.properties.get("tables", []):
            source = table.get("source", [])
            source_key = _attempt_parse_m_query_source(source)
            if source_key:
                source_keys.append(source_key)

        owner = data.properties.get("configuredBy")

        tables = data.properties.get("tables")
        table_meta = {}
        if tables:
            if len(tables) == 1:
                table_meta = _build_table_metadata(tables[0])
            else:
                table_meta = {
                    f"{table['name'].lower()}_column_schema": _build_table_metadata(
                        table
                    ).column_schema
                    for table in tables
                }

        return AssetSpec(
            key=AssetKey(["semantic_model", _clean_asset_name(data.properties["name"])]),
            deps=source_keys,
            metadata={
                **PowerBIMetadataSet(
                    web_url=MetadataValue.url(url) if url else None, id=data.properties["id"]
                ),
                **table_meta,
            },
            tags={**PowerBITagSet(asset_type="semantic_model")},
            kinds={"powerbi", "semantic model"},
            owners=[owner] if owner and is_valid_asset_owner(owner) else None,
        )

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterPowerBITranslator.get_asset_spec(...).key` instead",
    )
    def get_data_source_asset_key(self, data: PowerBITranslatorData) -> AssetKey:
        data = check.inst(data, PowerBITranslatorData)
        return self.get_data_source_spec(data).key

    def get_data_source_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        data = check.inst(data, PowerBITranslatorData)
        connection_name = (
            data.properties["connectionDetails"].get("path")
            or data.properties["connectionDetails"].get("url")
            or data.properties["connectionDetails"].get("database")
        )
        if not connection_name:
            asset_key = AssetKey([_clean_asset_name(data.properties["datasourceId"])])
        else:
            obj_name = _get_last_filepath_component(urllib.parse.unquote(connection_name))
            asset_key = AssetKey(path=[_clean_asset_name(obj_name)])

        return AssetSpec(
            key=asset_key,
            tags={**PowerBITagSet(asset_type="data_source")},
            kinds={"powerbi"},
        )
