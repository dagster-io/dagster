from enum import Enum
from typing import Any, Mapping, NamedTuple, Optional, Sequence

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes

from dagster_fivetran.utils import metadata_for_table


class FivetranConnectorTableProps(NamedTuple):
    table: str
    connector_id: str
    name: str
    connector_url: str
    schemas: Mapping[str, Any]
    database: Optional[str]
    service: Optional[str]


class FivetranContentType(Enum):
    """Enum representing each object in Fivetran's ontology."""

    CONNECTOR = "connector"
    DESTINATION = "destination"


@whitelist_for_serdes
@record
class FivetranContentData:
    """A record representing a piece of content in a Fivetran workspace.
    Includes the object's type and data as returned from the API.
    """

    content_type: FivetranContentType
    properties: Mapping[str, Any]


@record
class FivetranWorkspaceData:
    """A record representing all content in a Fivetran workspace.
    Provided as context for the translator so that it can resolve dependencies between content.
    """

    connectors_by_id: Mapping[str, FivetranContentData]
    destinations_by_id: Mapping[str, FivetranContentData]

    @classmethod
    def from_content_data(
        cls, content_data: Sequence[FivetranContentData]
    ) -> "FivetranWorkspaceData":
        raise NotImplementedError()

    def to_fivetran_connector_table_props_data(self) -> Sequence[FivetranConnectorTableProps]:
        """Method that converts a `FivetranWorkspaceData` object
        to a collection of `FivetranConnectorTableProps` objects.
        """
        raise NotImplementedError()


class DagsterFivetranTranslator:
    """Translator class which converts a `FivetranConnectorTableProps` object into AssetSpecs.
    Subclass this class to implement custom logic for each type of Fivetran content.
    """

    def get_asset_spec(self, props: FivetranConnectorTableProps) -> AssetSpec:
        """Get the AssetSpec for a table synced by a Fivetran connector."""
        schema_name, table_name = props.table.split(".")
        schema_entry = next(
            schema
            for schema in props.schemas["schemas"].values()
            if schema["name_in_destination"] == schema_name
        )
        table_entry = next(
            table_entry
            for table_entry in schema_entry["tables"].values()
            if table_entry["name_in_destination"] == table_name
        )

        metadata = metadata_for_table(
            table_entry,
            props.connector_url,
            database=props.database,
            schema=schema_name,
            table=table_name,
        )

        return AssetSpec(
            key=AssetKey(props.table.split(".")),
            metadata=metadata,
            kinds={"fivetran", *({props.service} if props.service else set())},
        )
