from abc import ABC, abstractmethod
from typing import Any, Mapping, Optional, Sequence

from dagster import MaterializeResult, TableRecord, UrlMetadataValue, asset
from pydantic import BaseModel


class NamespacedMetadata(BaseModel, ABC):
    """Extend this class to define a set of metadata fields in the same namespace.

    Supports syntactic sugar for converting to a dictionary that can be placed inside a metadata
    argument along with other dictionary-structured metadata.

    .. code-block:: python

        my_metadata: Metadata = ...
        return MaterializeResult(metadata={**my_metadata, ...})
    """

    @classmethod
    @abstractmethod
    def namespace(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def from_metadata_dict(cls, metadata_dict: Mapping[str, Any]):
        return cls.parse_obj(metadata_dict["__namespaced_metadata"][cls.namespace()])


####################################################################################################
# Metadata that's relevant to all assets.
####################################################################################################


class AssetMetadata(NamespacedMetadata):
    """Metadata fields that apply to definitions, observations, or materializations of any asset."""

    storage_kind: Optional[str]
    storage_address_string: Optional[str]
    source_code_link: Optional[UrlMetadataValue]

    @classmethod
    def namespace(cls) -> str:
        return "dagster"


####################################################################################################
# Metadata that's relevant to assets that are tables. Lives inside the "dagster.table" package.
####################################################################################################


class TableColumn(BaseModel):
    name: str
    data_type: str


class TableMetadata(NamespacedMetadata):
    """Metadata fields that apply to definitions, observations, or materializations of assets that
    are tables.
    """

    columns: Optional[Sequence[TableColumn]]

    @classmethod
    def namespace(cls) -> str:
        return "dagster.table"


class TableObservationMetadata(TableMetadata):
    """Metadata fields that apply to observations or materializations of assets that are tables."""

    num_rows_total: Optional[int]
    sample: Optional[Sequence[TableRecord]]


class TableMaterializationMetadata(TableObservationMetadata):
    """Metadata fields that apply to materializations of assets that are tables."""

    num_rows_inserted: Optional[int]
    num_rows_updated: Optional[int]
    num_rows_deleted: Optional[int]
    num_rows_affected: Optional[int]


####################################################################################################
# Metadata that's relevant to assets that are Snowflake tables. Lives inside the "dagster_snowflake"
# package.
####################################################################################################


class SnowflakeTableAddress(BaseModel):
    """An identifier for a table in Snowflake."""

    database: Optional[str]
    db_schema: Optional[str]
    table_name: Optional[str]


class SnowflakeTableMetadata(NamespacedMetadata):
    """Metadata fields that apply to assets that are tables in Snowflake."""

    snowflake_address: Optional[SnowflakeTableAddress]
    cluster_by: Optional[str]

    @classmethod
    def namespace(cls) -> str:
        return "dagster_snowflake"


####################################################################################################
# An asset with metadata constructed using the structured metadata APIs.
####################################################################################################


def build_metadata_dict(
    namespaced_metadatas: Sequence[NamespacedMetadata], metadata: Mapping[str, Any]
) -> Mapping[str, Any]:
    namespaced_metadata_dict = {}
    for namespaced_metadata in namespaced_metadatas:
        namespaced_metadata_dict[namespaced_metadata.namespace()] = {}
        for key, value in namespaced_metadata.dict().items():
            if value is not None:
                namespaced_metadata_dict[namespaced_metadata.namespace()][key] = value

    return {**metadata, "__namespaced_metadata": namespaced_metadata_dict}


@asset
def asset1():
    return MaterializeResult(
        metadata=build_metadata_dict(
            namespaced_metadatas=[
                AssetMetadata(
                    storage_kind="snowflake", storage_address_string="my_db.my_schema.asset1"
                ),
                TableMaterializationMetadata(
                    num_rows_total=500,
                    num_rows_inserted=5,
                    columns=[TableColumn(name="user_id", data_type="str")],
                ),
                SnowflakeTableMetadata(
                    snowflake_address=SnowflakeTableAddress(
                        database="my_db", db_schema="my_schema", table_name="asset1"
                    )
                ),
            ],
            metadata={
                "my_unschematized_piece_of_metadata": 5,
                "staging_address": SnowflakeTableAddress(
                    database="my_staging_db", db_schema="my_schema", table_name="asset1"
                ).dict(),
            },
        )
    )


####################################################################################################
# An asset with metadata constructed using plain JSON-objects. Has identical metadata to the asset
# above.
####################################################################################################


@asset
def asset2():
    return MaterializeResult(
        metadata={
            "__namespaced_metadata": {
                "dagster.table": {
                    "num_rows_inserted": 5,
                    "columns": [{"name": "user_id", "data_type": "str"}],
                    "num_rows_total": 500,
                },
                "dagster": {
                    "storage_kind": "snowflake",
                    "storage_address_string": "my_db.my_schema.asset1",
                },
                "dagster_snowflake": {
                    "snowflake_address": {
                        "database": "my_db",
                        "db_schema": "my_schema",
                        "table_name": "asset1",
                    },
                },
            },
            "my_unschematized_piece_of_metadata": 5,
            "staging_address": {
                "database": "my_staging_db",
                "db_schema": "my_schema",
                "table_name": "asset1",
            },
        }
    )


####################################################################################################
# The Dagster asset UI displays a table of metadata fields. Below is a rough approximation of the
# logic that would be used to populate the rows of that table.
####################################################################################################


class UIMetadataTableRow(BaseModel):
    namespace: Optional[str]
    key: str
    value: Any


def get_ui_metadata_table_rows(metadata: Mapping[str, Any]) -> Sequence[UIMetadataTableRow]:
    result = []
    for key, value in metadata.items():
        if key == "__namespaced_metadata":
            for namespace, namespace_fields in metadata[key].items():
                for namespaced_field_key, namespaced_field_value in namespace_fields.items():
                    result.append(
                        UIMetadataTableRow(
                            namespace=namespace,
                            key=namespaced_field_key,
                            value=namespaced_field_value,
                        )
                    )
        else:
            result.append(UIMetadataTableRow(namespace=None, key=key, value=value))

    return result


####################################################################################################
# Test
####################################################################################################


def test():
    asset1_result = asset1()
    asset2_result = asset2()
    assert TableObservationMetadata.from_metadata_dict(asset1_result.metadata).num_rows_total == 500
    assert asset1_result.metadata == asset2_result.metadata
    assert len(get_ui_metadata_table_rows(asset1_result.metadata)) == 8
