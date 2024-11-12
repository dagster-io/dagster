from enum import Enum
from typing import Any, Dict, List, Mapping, NamedTuple, Optional, Sequence, cast

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method

from dagster_fivetran.utils import (
    get_fivetran_connector_table_name,
    get_fivetran_connector_url,
    metadata_for_table,
)


class FivetranConnectorTableProps(NamedTuple):
    table: str
    connector_id: str
    name: str
    connector_url: str
    schema_config: Mapping[str, Any]
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
        return cls(
            connectors_by_id={
                connector.properties["id"]: connector
                for connector in content_data
                if connector.content_type == FivetranContentType.CONNECTOR
            },
            destinations_by_id={
                destination.properties["id"]: destination
                for destination in content_data
                if destination.content_type == FivetranContentType.DESTINATION
            },
        )

    @cached_method
    def to_fivetran_connector_table_props_data(self) -> Sequence[FivetranConnectorTableProps]:
        """Method that converts a `FivetranWorkspaceData` object
        to a collection of `FivetranConnectorTableProps` objects.
        """
        data: List[FivetranConnectorTableProps] = []

        for connector_id, connector_data in self.connectors_by_id.items():
            connector_details = connector_data.properties
            connector_name = connector_details["schema"]
            connector_url = get_fivetran_connector_url(connector_details)

            schema_config = connector_details["schema_config"]

            destination_details = self.destinations_by_id[
                connector_details["destination_id"]
            ].properties
            database = destination_details.get("config", {}).get("database")
            service = destination_details.get("service")

            schemas_data = cast(Dict[str, Any], schema_config["schemas"])
            for schema in schemas_data.values():
                if schema["enabled"]:
                    schema_name = schema["name_in_destination"]
                    schema_tables: Dict[str, Dict[str, Any]] = cast(
                        Dict[str, Dict[str, Any]], schema["tables"]
                    )
                    for table in schema_tables.values():
                        if table["enabled"]:
                            table_name = table["name_in_destination"]
                            data.append(
                                FivetranConnectorTableProps(
                                    table=get_fivetran_connector_table_name(
                                        schema_name=schema_name, table_name=table_name
                                    ),
                                    connector_id=connector_id,
                                    name=connector_name,
                                    connector_url=connector_url,
                                    schema_config=schema_config,
                                    database=database,
                                    service=service,
                                )
                            )

        return data


class DagsterFivetranTranslator:
    """Translator class which converts a `FivetranConnectorTableProps` object into AssetSpecs.
    Subclass this class to implement custom logic for each type of Fivetran content.
    """

    def get_asset_spec(self, props: FivetranConnectorTableProps) -> AssetSpec:
        """Get the AssetSpec for a table synced by a Fivetran connector."""
        schema_name, table_name = props.table.split(".")
        schema_entry = next(
            schema
            for schema in props.schema_config["schemas"].values()
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
