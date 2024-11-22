import re
from typing import AbstractSet, Any, Dict, List, Optional, Union

from dagster import AssetKey, AssetSpec, MetadataValue, TableSchema
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.table import TableColumn
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method
from dagster._vendored.dateutil.parser import isoparse


def _coerce_input_to_valid_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name."""
    return re.sub(r"[^A-Za-z0-9_]+", "_", name)


def asset_key_from_table_name(table_name: str) -> AssetKey:
    """Converts a reference to a table in a Sigma query to a Dagster AssetKey."""
    return AssetKey([_coerce_input_to_valid_name(part) for part in table_name.split(".")])


def _inode_from_url(url: str) -> str:
    """Builds a Sigma internal inode value from a Sigma URL."""
    return f'inode-{url.split("/")[-1]}'


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

    def __init__(self, context: SigmaOrganizationData):
        self._context = context

    @property
    def organization_data(self) -> SigmaOrganizationData:
        return self._context

    def get_asset_key(self, data: Union[SigmaDataset, SigmaWorkbook]) -> AssetKey:
        """Get the AssetKey for a Sigma object, such as a workbook or dataset."""
        return AssetKey(_coerce_input_to_valid_name(data.properties["name"]))

    def get_asset_spec(self, data: Union[SigmaDataset, SigmaWorkbook]) -> AssetSpec:
        """Get the AssetSpec for a Sigma object, such as a workbook or dataset."""
        if isinstance(data, SigmaWorkbook):
            metadata = {
                "dagster_sigma/web_url": MetadataValue.url(data.properties["url"]),
                "dagster_sigma/version": data.properties["latestVersion"],
                "dagster_sigma/created_at": MetadataValue.timestamp(
                    isoparse(data.properties["createdAt"])
                ),
                "dagster_sigma/properties": MetadataValue.json(data.properties),
                "dagster_sigma/lineage": MetadataValue.json(data.lineage),
            }
            datasets = [self._context.get_datasets_by_inode()[inode] for inode in data.datasets]
            tables = [
                self._context.get_tables_by_inode()[inode] for inode in data.direct_table_deps
            ]

            return AssetSpec(
                key=self.get_asset_key(data),
                metadata=metadata,
                kinds={"sigma", "workbook"},
                deps={
                    *[self.get_asset_key(dataset) for dataset in datasets],
                    *[
                        asset_key_from_table_name(".".join(table.get_table_path()).lower())
                        for table in tables
                    ],
                },
                owners=[data.owner_email] if data.owner_email else None,
            )
        elif isinstance(data, SigmaDataset):
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
                key=self.get_asset_key(data),
                metadata=metadata,
                kinds={"sigma", "dataset"},
                deps={
                    asset_key_from_table_name(input_table_name.lower())
                    for input_table_name in data.inputs
                },
                description=data.properties.get("description"),
            )
