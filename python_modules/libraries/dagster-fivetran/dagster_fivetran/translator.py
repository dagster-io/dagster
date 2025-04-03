from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from typing import Any, Callable, NamedTuple, Optional

from dagster import Failure
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster._record import as_dict, record
from dagster._utils.cached_method import cached_method
from dagster._vendored.dateutil import parser
from dagster_shared.serdes import whitelist_for_serdes
from typing_extensions import TypeAlias

from dagster_fivetran.utils import get_fivetran_connector_table_name, metadata_for_table

MIN_TIME_STR = "0001-01-01 00:00:00+00"

ConnectorSelectorFn: TypeAlias = Callable[["FivetranConnector"], bool]


class FivetranConnectorTableProps(NamedTuple):
    table: str
    connector_id: str
    name: str
    connector_url: str
    schema_config: "FivetranSchemaConfig"
    database: Optional[str]
    service: Optional[str]


class FivetranConnectorScheduleType(str, Enum):
    """Enum representing each schedule type for a connector in Fivetran's ontology."""

    AUTO = "auto"
    MANUAL = "manual"


class FivetranConnectorSetupStateType(Enum):
    """Enum representing each setup state for a connector in Fivetran's ontology."""

    INCOMPLETE = "incomplete"
    CONNECTED = "connected"
    BROKEN = "broken"


@whitelist_for_serdes
@record
class FivetranConnector:
    """Represents a Fivetran connector, based on data as returned from the API."""

    id: str
    name: str
    service: str
    group_id: str
    setup_state: str
    sync_state: str
    paused: bool
    succeeded_at: Optional[str]
    failed_at: Optional[str]

    @property
    def url(self) -> str:
        return f"https://fivetran.com/dashboard/connectors/{self.id}"

    @property
    def destination_id(self) -> str:
        return self.group_id

    @property
    def is_connected(self) -> bool:
        return self.setup_state == FivetranConnectorSetupStateType.CONNECTED.value

    @property
    def is_paused(self) -> bool:
        return self.paused

    @property
    def last_sync_completed_at(self) -> datetime:
        """Gets the datetime of the last completed sync of the Fivetran connector.

        Returns:
            datetime.datetime:
                The datetime of the last completed sync of the Fivetran connector.
        """
        succeeded_at = parser.parse(self.succeeded_at or MIN_TIME_STR)
        failed_at = parser.parse(self.failed_at or MIN_TIME_STR)

        return max(succeeded_at, failed_at)  # pyright: ignore[reportReturnType]

    @property
    def is_last_sync_successful(self) -> bool:
        """Gets a boolean representing whether the last completed sync of the Fivetran connector was successful or not.

        Returns:
            bool:
                Whether the last completed sync of the Fivetran connector was successful or not.
        """
        succeeded_at = parser.parse(self.succeeded_at or MIN_TIME_STR)
        failed_at = parser.parse(self.failed_at or MIN_TIME_STR)

        return succeeded_at > failed_at  # pyright: ignore[reportOperatorIssue]

    def validate_syncable(self) -> bool:
        """Confirms that the connector can be sync. Will raise a Failure in the event that
        the connector is either paused or not fully set up.
        """
        if self.is_paused:
            raise Failure(f"Connector '{self.id}' cannot be synced as it is currently paused.")
        if not self.is_connected:
            raise Failure(f"Connector '{self.id}' cannot be synced as it has not been setup")
        return True

    @classmethod
    def from_connector_details(
        cls,
        connector_details: Mapping[str, Any],
    ) -> "FivetranConnector":
        return cls(
            id=connector_details["id"],
            name=connector_details["schema"],
            service=connector_details["service"],
            group_id=connector_details["group_id"],
            setup_state=connector_details["status"]["setup_state"],
            sync_state=connector_details["status"]["sync_state"],
            paused=connector_details["paused"],
            succeeded_at=connector_details.get("succeeded_at"),
            failed_at=connector_details.get("failed_at"),
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
    # We keep the raw data for columns to add it as `column_info` in the metadata.
    columns: Optional[Mapping[str, Any]]

    @classmethod
    def from_table_details(cls, table_details: Mapping[str, Any]) -> "FivetranTable":
        return cls(
            enabled=table_details["enabled"],
            name_in_destination=table_details["name_in_destination"],
            columns=table_details.get("columns"),
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

    @property
    def has_schemas(self) -> bool:
        return bool(self.schemas)

    @classmethod
    def from_schema_config_details(
        cls, schema_config_details: Mapping[str, Any]
    ) -> "FivetranSchemaConfig":
        return cls(
            schemas={
                schema_key: FivetranSchema.from_schema_details(schema_details=schema_details)
                for schema_key, schema_details in schema_config_details.get("schemas", {}).items()
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
    schema_configs_by_connector_id: Mapping[str, FivetranSchemaConfig]

    @cached_method
    def to_fivetran_connector_table_props_data(self) -> Sequence[FivetranConnectorTableProps]:
        """Method that converts a `FivetranWorkspaceData` object
        to a collection of `FivetranConnectorTableProps` objects.
        """
        data: list[FivetranConnectorTableProps] = []

        for connector in self.connectors_by_id.values():
            destination = self.destinations_by_id[connector.destination_id]
            schema_config = self.schema_configs_by_connector_id[connector.id]

            for schema in schema_config.schemas.values():
                if schema.enabled:
                    for table in schema.tables.values():
                        if table.enabled:
                            data.append(
                                FivetranConnectorTableProps(
                                    table=get_fivetran_connector_table_name(
                                        schema_name=schema.name_in_destination,
                                        table_name=table.name_in_destination,
                                    ),
                                    connector_id=connector.id,
                                    name=connector.name,
                                    connector_url=connector.url,
                                    schema_config=schema_config,
                                    database=destination.database,
                                    service=destination.service,
                                )
                            )
        return data

    # Cache workspace data selection for a specific connector_selector_fn
    @cached_method
    def to_workspace_data_selection(
        self, connector_selector_fn: Optional[ConnectorSelectorFn]
    ) -> "FivetranWorkspaceData":
        if not connector_selector_fn:
            return self
        connectors_by_id_selection = {}
        destination_ids_selection = set()
        for connector_id, connector in self.connectors_by_id.items():
            if connector_selector_fn(connector):
                connectors_by_id_selection[connector_id] = connector
                destination_ids_selection.add(connector.destination_id)

        destinations_by_id_selection = {
            destination_id: destination
            for destination_id, destination in self.destinations_by_id.items()
            if destination_id in destination_ids_selection
        }
        schema_configs_by_connector_id_selection = {
            connector_id: schema_configs
            for connector_id, schema_configs in self.schema_configs_by_connector_id.items()
            if connector_id in connectors_by_id_selection.keys()
        }

        return FivetranWorkspaceData(
            connectors_by_id=connectors_by_id_selection,
            destinations_by_id=destinations_by_id_selection,
            schema_configs_by_connector_id=schema_configs_by_connector_id_selection,
        )


class FivetranMetadataSet(NamespacedMetadataSet):
    connector_id: Optional[str] = None
    destination_schema_name: Optional[str] = None
    destination_table_name: Optional[str] = None

    @classmethod
    def namespace(cls) -> str:
        return "dagster-fivetran"


class DagsterFivetranTranslator:
    """Translator class which converts a `FivetranConnectorTableProps` object into AssetSpecs.
    Subclass this class to implement custom logic on how to translate Fivetran content into asset spec.
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

        augmented_metadata = {
            **metadata,
            **FivetranMetadataSet(
                connector_id=props.connector_id,
                destination_schema_name=schema_name,
                destination_table_name=table_name,
            ),
        }

        return AssetSpec(
            key=AssetKey(props.table.split(".")),
            metadata=augmented_metadata,
            kinds={"fivetran", *({props.service} if props.service else set())},
        )
