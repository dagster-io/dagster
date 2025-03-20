import re
from typing import AbstractSet, Any, Optional, Union  # noqa: UP035

from dagster import AssetKey, AssetSpec, MetadataValue, TableSchema
from dagster._annotations import deprecated
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet, TableMetadataSet
from dagster._core.definitions.metadata.metadata_value import (
    JsonMetadataValue,
    TimestampMetadataValue,
    UrlMetadataValue,
)
from dagster._core.definitions.metadata.table import TableColumn
from dagster._record import record
from dagster._utils.cached_method import cached_method
from dagster._vendored.dateutil.parser import isoparse
from dagster_shared.serdes import whitelist_for_serdes


def _coerce_input_to_valid_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)


def asset_key_from_table_name(table_name: str) -> AssetKey:
    """Converts a reference to a table in a Sigma query to a Dagster AssetKey."""
    return AssetKey([_coerce_input_to_valid_name(part) for part in table_name.split(".")])


def _inode_from_url(url: str) -> str:
    """Builds a Sigma internal inode value from a Sigma URL."""
    return f'inode-{url.split("/")[-1]}'


class SigmaWorkbookMetadataSet(NamespacedMetadataSet):
    web_url: Optional[UrlMetadataValue]
    version: Optional[int]
    created_at: Optional[TimestampMetadataValue]
    properties: Optional[JsonMetadataValue]
    lineage: Optional[JsonMetadataValue]
    materialization_schedules: Optional[JsonMetadataValue] = None
    workbook_id: str

    @classmethod
    def namespace(cls) -> str:
        return "dagster_sigma"


@whitelist_for_serdes
@record
class SigmaWorkbook:
    """Represents a Sigma workbook, a collection of visualizations and queries
    for data exploration and analysis.

    https://help.sigmacomputing.com/docs/workbooks
    """

    properties: dict[str, Any]
    lineage: list[dict[str, Any]]
    datasets: AbstractSet[str]
    direct_table_deps: AbstractSet[str]
    owner_email: Optional[str]
    materialization_schedules: Optional[list[dict[str, Any]]]


@whitelist_for_serdes
@record
class SigmaDataset:
    """Represents a Sigma dataset, a centralized data definition which can
    contain aggregations or other manipulations.

    https://help.sigmacomputing.com/docs/datasets
    """

    properties: dict[str, Any]
    columns: AbstractSet[str]
    inputs: AbstractSet[str]


@whitelist_for_serdes
@record
class SigmaTable:
    """Represents a table loaded into Sigma."""

    properties: dict[str, Any]

    def get_table_path(self) -> list[str]:
        """Extracts the qualified table path from the name and path properties,
        e.g. ["MY_DB", "MY_SCHEMA", "MY_TABLE"].
        """
        return self.properties["path"].split("/")[1:] + [self.properties["name"]]


@record
class SigmaWorkbookTranslatorData:
    """A record representing a Sigma workbook and the Sigma organization data."""

    workbook: "SigmaWorkbook"
    organization_data: "SigmaOrganizationData"

    @property
    def properties(self) -> dict[str, Any]:
        return self.workbook.properties

    @property
    def lineage(self) -> list[dict[str, Any]]:
        return self.workbook.lineage

    @property
    def datasets(self) -> AbstractSet[str]:
        return self.workbook.datasets

    @property
    def direct_table_deps(self) -> AbstractSet[str]:
        return self.workbook.direct_table_deps

    @property
    def owner_email(self) -> Optional[str]:
        return self.workbook.owner_email

    @property
    def materialization_schedules(self) -> Optional[list[dict[str, Any]]]:
        return self.workbook.materialization_schedules


@record
class SigmaDatasetTranslatorData:
    """A record representing a Sigma dataset and the Sigma organization data."""

    dataset: "SigmaDataset"
    organization_data: "SigmaOrganizationData"

    @property
    def properties(self) -> dict[str, Any]:
        return self.dataset.properties

    @property
    def columns(self) -> AbstractSet[str]:
        return self.dataset.columns

    @property
    def inputs(self) -> AbstractSet[str]:
        return self.dataset.inputs


@whitelist_for_serdes
@record
class SigmaOrganizationData:
    workbooks: list[SigmaWorkbook]
    datasets: list[SigmaDataset]
    tables: list[SigmaTable]

    @cached_method
    def get_datasets_by_inode(self) -> dict[str, SigmaDataset]:
        return {_inode_from_url(dataset.properties["url"]): dataset for dataset in self.datasets}

    @cached_method
    def get_tables_by_inode(self) -> dict[str, SigmaTable]:
        return {_inode_from_url(table.properties["urlId"]): table for table in self.tables}


class DagsterSigmaTranslator:
    """Translator class which converts raw response data from the Sigma API into AssetSpecs.
    Subclass this class to provide custom translation logic.
    """

    @deprecated(
        breaking_version="1.10",
        additional_warn_text="Use `DagsterSigmaTranslator.get_asset_spec(...).key` instead",
    )
    def get_asset_key(
        self, data: Union[SigmaDatasetTranslatorData, SigmaWorkbookTranslatorData]
    ) -> AssetKey:
        """Get the AssetKey for a Sigma object, such as a workbook or dataset."""
        return self.get_asset_spec(data).key

    def get_asset_spec(
        self, data: Union[SigmaDatasetTranslatorData, SigmaWorkbookTranslatorData]
    ) -> AssetSpec:
        """Get the AssetSpec for a Sigma object, such as a workbook or dataset."""
        if isinstance(data, SigmaWorkbookTranslatorData):
            metadata = {
                **SigmaWorkbookMetadataSet(
                    web_url=MetadataValue.url(data.properties["url"]),
                    version=data.properties["latestVersion"],
                    created_at=MetadataValue.timestamp(isoparse(data.properties["createdAt"])),
                    properties=MetadataValue.json(data.properties),
                    lineage=MetadataValue.json(data.lineage),
                    workbook_id=data.properties["workbookId"],
                    **(
                        {
                            "materialization_schedules": MetadataValue.json(
                                data.materialization_schedules
                            )
                        }
                        if data.materialization_schedules
                        else {}
                    ),
                ),
            }
            datasets = [
                data.organization_data.get_datasets_by_inode()[inode] for inode in data.datasets
            ]
            tables = [
                data.organization_data.get_tables_by_inode()[inode]
                for inode in data.direct_table_deps
            ]

            return AssetSpec(
                key=AssetKey(_coerce_input_to_valid_name(data.properties["name"])),
                metadata=metadata,
                kinds={"sigma", "workbook"},
                deps={
                    *[
                        self.get_asset_key(
                            SigmaDatasetTranslatorData(
                                dataset=dataset, organization_data=data.organization_data
                            )
                        )
                        for dataset in datasets
                    ],
                    *[
                        asset_key_from_table_name(".".join(table.get_table_path()).lower())
                        for table in tables
                    ],
                },
                owners=[data.owner_email] if data.owner_email else None,
            )
        elif isinstance(data, SigmaDatasetTranslatorData):
            metadata = {
                "dagster_sigma/web_url": MetadataValue.url(data.properties["url"]),
                "dagster_sigma/created_at": MetadataValue.timestamp(
                    isoparse(data.properties["createdAt"])
                ),
                "dagster_sigma/properties": MetadataValue.json(data.properties),
                **TableMetadataSet(
                    column_schema=TableSchema(
                        columns=[
                            TableColumn(name=column_name) for column_name in sorted(data.columns)
                        ]
                    )
                ),
            }

            return AssetSpec(
                key=AssetKey(_coerce_input_to_valid_name(data.properties["name"])),
                metadata=metadata,
                kinds={"sigma", "dataset"},
                deps={
                    asset_key_from_table_name(input_table_name.lower())
                    for input_table_name in data.inputs
                },
                description=data.properties.get("description"),
            )
