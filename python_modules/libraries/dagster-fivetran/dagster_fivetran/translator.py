from typing import Any, List, Mapping, NamedTuple, Optional, Sequence

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import as_dict, record
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method

from dagster_fivetran.utils import get_fivetran_connector_table_name, metadata_for_table


class FivetranConnectorTableProps(NamedTuple):
    table: str
    connector_id: str
    name: str
    connector_url: str
    schema_config: "FivetranSchemaConfig"
    database: Optional[str]
    service: Optional[str]


@whitelist_for_serdes
@record
class FivetranConnector:
    """Represents a Fivetran connector, based on data as returned from the API."""

    id: str
    name: str
    service: str
    schema_config: "FivetranSchemaConfig"
    destination_id: str

    @property
    def url(self) -> str:
        return f"https://fivetran.com/dashboard/connectors/{self.service}/{self.name}"

    @classmethod
    def from_api_details(
        cls,
        connector_details: Mapping[str, Any],
        destination_details: Mapping[str, Any],
        schema_config_details: Mapping[str, Any],
    ) -> "FivetranConnector":
        return cls(
            id=connector_details["id"],
            name=connector_details["schema"],
            service=connector_details["service"],
            schema_config=FivetranSchemaConfig.from_schema_config_details(
                schema_config_details=schema_config_details
            ),
            destination_id=destination_details["id"],
        )


@whitelist_for_serdes
@record
class FivetranDestination:
    """Represents a Fivetran destination, based on data as returned from the API."""

    id: str
    database: Optional[str]
    service: str

    @classmethod
    def from_destination_details(
        cls, destination_details: Mapping[str, Any]
    ) -> "FivetranDestination":
        return cls(
            id=destination_details["id"],
            database=destination_details.get("config", {}).get("database"),
            service=destination_details["service"],
        )


@whitelist_for_serdes
@record
class FivetranTable:
    """Represents a Fivetran table, based on data as returned from the API."""

    enabled: bool
    name_in_destination: str
    # We keep the raw data for columns to add it as `column_info in the metadata.
    columns: Mapping[str, Any]

    @classmethod
    def from_table_details(cls, table_details: Mapping[str, Any]) -> "FivetranTable":
        return cls(
            enabled=table_details["enabled"],
            name_in_destination=table_details["name_in_destination"],
            columns=table_details["columns"],
        )


@whitelist_for_serdes
@record
class FivetranSchema:
    """Represents a Fivetran schema, based on data as returned from the API."""

    enabled: bool
    name_in_destination: str
    tables: Mapping[str, "FivetranTable"]

    @classmethod
    def from_schema_details(cls, schema_details: Mapping[str, Any]) -> "FivetranSchema":
        return cls(
            enabled=schema_details["enabled"],
            name_in_destination=schema_details["name_in_destination"],
            tables={
                table_key: FivetranTable.from_table_details(table_details=table_details)
                for table_key, table_details in schema_details["tables"].items()
            },
        )


@whitelist_for_serdes
@record
class FivetranSchemaConfig:
    """Represents a Fivetran schema config, based on data as returned from the API."""

    schemas: Mapping[str, FivetranSchema]

    @classmethod
    def from_schema_config_details(
        cls, schema_config_details: Mapping[str, Any]
    ) -> "FivetranSchemaConfig":
        return cls(
            schemas={
                schema_key: FivetranSchema.from_schema_details(schema_details=schema_details)
                for schema_key, schema_details in schema_config_details["schemas"].items()
            }
        )


@whitelist_for_serdes
@record
class FivetranWorkspaceData:
    """A record representing all content in a Fivetran workspace.
    Provided as context for the translator so that it can resolve dependencies between content.
    """

    connectors_by_id: Mapping[str, FivetranConnector]
    destinations_by_id: Mapping[str, FivetranDestination]

    @cached_method
    def to_fivetran_connector_table_props_data(self) -> Sequence[FivetranConnectorTableProps]:
        """Method that converts a `FivetranWorkspaceData` object
        to a collection of `FivetranConnectorTableProps` objects.
        """
        data: List[FivetranConnectorTableProps] = []

        for connector_id, connector in self.connectors_by_id.items():
            destination = self.destinations_by_id[connector.destination_id]

            for schema in connector.schema_config.schemas.values():
                if schema.enabled:
                    for table in schema.tables.values():
                        if table.enabled:
                            data.append(
                                FivetranConnectorTableProps(
                                    table=get_fivetran_connector_table_name(
                                        schema_name=schema.name_in_destination,
                                        table_name=table.name_in_destination,
                                    ),
                                    connector_id=connector_id,
                                    name=connector.name,
                                    connector_url=connector.url,
                                    schema_config=connector.schema_config,
                                    database=destination.database,
                                    service=destination.service,
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
            for schema in props.schema_config.schemas.values()
            if schema.name_in_destination == schema_name
        )
        table_entry = next(
            table_entry
            for table_entry in schema_entry.tables.values()
            if table_entry.name_in_destination == table_name
        )

        metadata = metadata_for_table(
            as_dict(table_entry),
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
