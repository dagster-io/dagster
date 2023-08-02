import json
from abc import ABC
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Union

import dagster._check as check
from dagster._annotations import public


class AirbyteSyncMode(ABC):
    """Represents the sync mode for a given Airbyte stream, which governs how Airbyte reads
    from a source and writes to a destination.

    For more information, see https://docs.airbyte.com/understanding-airbyte/connections/.
    """

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, AirbyteSyncMode) and self.to_json() == other.to_json()

    def __init__(self, json_repr: Dict[str, Any]):
        self.json_repr = json_repr

    def to_json(self) -> Dict[str, Any]:
        return self.json_repr

    @classmethod
    def from_json(cls, json_repr: Dict[str, Any]) -> "AirbyteSyncMode":
        return cls(
            {
                k: v
                for k, v in json_repr.items()
                if k in ("syncMode", "destinationSyncMode", "cursorField", "primaryKey")
            }
        )

    @public
    @classmethod
    def full_refresh_append(cls) -> "AirbyteSyncMode":
        """Syncs the entire data stream from the source, appending rows to the destination.

        https://docs.airbyte.com/understanding-airbyte/connections/full-refresh-append/
        """
        return cls({"syncMode": "full_refresh", "destinationSyncMode": "append"})

    @public
    @classmethod
    def full_refresh_overwrite(cls) -> "AirbyteSyncMode":
        """Syncs the entire data stream from the source, replaces data in the destination by
        overwriting it.

        https://docs.airbyte.com/understanding-airbyte/connections/full-refresh-overwrite
        """
        return cls({"syncMode": "full_refresh", "destinationSyncMode": "overwrite"})

    @public
    @classmethod
    def incremental_append(
        cls,
        cursor_field: Optional[str] = None,
    ) -> "AirbyteSyncMode":
        """Syncs only new records from the source, appending rows to the destination.
        May optionally specify the cursor field used to determine which records
        are new.

        https://docs.airbyte.com/understanding-airbyte/connections/incremental-append/
        """
        cursor_field = check.opt_str_param(cursor_field, "cursor_field")

        return cls(
            {
                "syncMode": "incremental",
                "destinationSyncMode": "append",
                **({"cursorField": [cursor_field]} if cursor_field else {}),
            }
        )

    @public
    @classmethod
    def incremental_append_dedup(
        cls,
        cursor_field: Optional[str] = None,
        primary_key: Optional[Union[str, List[str]]] = None,
    ) -> "AirbyteSyncMode":
        """Syncs new records from the source, appending to an append-only history
        table in the destination. Also generates a deduplicated view mirroring the
        source table. May optionally specify the cursor field used to determine
        which records are new, and the primary key used to determine which records
        are duplicates.

        https://docs.airbyte.com/understanding-airbyte/connections/incremental-append-dedup/
        """
        cursor_field = check.opt_str_param(cursor_field, "cursor_field")
        if isinstance(primary_key, str):
            primary_key = [primary_key]
        primary_key = check.opt_list_param(primary_key, "primary_key", of_type=str)

        return cls(
            {
                "syncMode": "incremental",
                "destinationSyncMode": "append_dedup",
                **({"cursorField": [cursor_field]} if cursor_field else {}),
                **({"primaryKey": [[x] for x in primary_key]} if primary_key else {}),
            }
        )


class AirbyteSource:
    """Represents a user-defined Airbyte source.

    Args:
        name (str): The display name of the source.
        source_type (str): The type of the source, from Airbyte's list
            of sources https://airbytehq.github.io/category/sources/.
        source_configuration (Mapping[str, Any]): The configuration for the
            source, as defined by Airbyte's API.
    """

    @public
    def __init__(self, name: str, source_type: str, source_configuration: Mapping[str, Any]):
        self.name = check.str_param(name, "name")
        self.source_type = check.str_param(source_type, "source_type")
        self.source_configuration = check.mapping_param(
            source_configuration, "source_configuration", key_type=str
        )

    def must_be_recreated(self, other: "AirbyteSource") -> bool:
        return self.name != other.name or self.source_type != other.source_type


class InitializedAirbyteSource:
    """User-defined Airbyte source bound to actual created Airbyte source."""

    def __init__(self, source: AirbyteSource, source_id: str, source_definition_id: Optional[str]):
        self.source = source
        self.source_id = source_id
        self.source_definition_id = source_definition_id

    @classmethod
    def from_api_json(cls, api_json: Mapping[str, Any]):
        return cls(
            source=AirbyteSource(
                name=api_json["name"],
                source_type=api_json["sourceName"],
                source_configuration=api_json["connectionConfiguration"],
            ),
            source_id=api_json["sourceId"],
            source_definition_id=None,
        )


class AirbyteDestination:
    """Represents a user-defined Airbyte destination.

    Args:
        name (str): The display name of the destination.
        destination_type (str): The type of the destination, from Airbyte's list
            of destinations https://airbytehq.github.io/category/destinations/.
        destination_configuration (Mapping[str, Any]): The configuration for the
            destination, as defined by Airbyte's API.
    """

    @public
    def __init__(
        self, name: str, destination_type: str, destination_configuration: Mapping[str, Any]
    ):
        self.name = check.str_param(name, "name")
        self.destination_type = check.str_param(destination_type, "destination_type")
        self.destination_configuration = check.mapping_param(
            destination_configuration, "destination_configuration", key_type=str
        )

    def must_be_recreated(self, other: "AirbyteDestination") -> bool:
        return self.name != other.name or self.destination_type != other.destination_type


class InitializedAirbyteDestination:
    """User-defined Airbyte destination bound to actual created Airbyte destination."""

    def __init__(
        self,
        destination: AirbyteDestination,
        destination_id: str,
        destination_definition_id: Optional[str],
    ):
        self.destination = destination
        self.destination_id = destination_id
        self.destination_definition_id = destination_definition_id

    @classmethod
    def from_api_json(cls, api_json: Mapping[str, Any]):
        return cls(
            destination=AirbyteDestination(
                name=api_json["name"],
                destination_type=api_json["destinationName"],
                destination_configuration=api_json["connectionConfiguration"],
            ),
            destination_id=api_json["destinationId"],
            destination_definition_id=None,
        )


class AirbyteDestinationNamespace(Enum):
    """Represents the sync mode for a given Airbyte stream."""

    SAME_AS_SOURCE = "source"
    DESTINATION_DEFAULT = "destination"


class AirbyteConnection:
    """A user-defined Airbyte connection, pairing an Airbyte source and destination and configuring
    which streams to sync.

    Args:
        name (str): The display name of the connection.
        source (AirbyteSource): The source to sync from.
        destination (AirbyteDestination): The destination to sync to.
        stream_config (Mapping[str, AirbyteSyncMode]): A mapping from stream name to
            the sync mode for that stream, including any additional configuration
            of primary key or cursor field.
        normalize_data (Optional[bool]): Whether to normalize the data in the
            destination.
        destination_namespace (Optional[Union[AirbyteDestinationNamespace, str]]):
            The namespace to sync to in the destination. If set to
            AirbyteDestinationNamespace.SAME_AS_SOURCE, the namespace will be the
            same as the source namespace. If set to
            AirbyteDestinationNamespace.DESTINATION_DEFAULT, the namespace will be
            the default namespace for the destination. If set to a string, the
            namespace will be that string.
        prefix (Optional[str]): A prefix to add to the table names in the destination.

    Example:
        .. code-block:: python

            from dagster_airbyte.managed.generated.sources import FileSource
            from dagster_airbyte.managed.generated.destinations import LocalJsonDestination
            from dagster_airbyte import AirbyteConnection, AirbyteSyncMode

            cereals_csv_source = FileSource(...)
            local_json_destination = LocalJsonDestination(...)

            cereals_connection = AirbyteConnection(
                name="download-cereals",
                source=cereals_csv_source,
                destination=local_json_destination,
                stream_config={"cereals": AirbyteSyncMode.full_refresh_overwrite()},
            )
    """

    @public
    def __init__(
        self,
        name: str,
        source: AirbyteSource,
        destination: AirbyteDestination,
        stream_config: Mapping[str, AirbyteSyncMode],
        normalize_data: Optional[bool] = None,
        destination_namespace: Optional[
            Union[AirbyteDestinationNamespace, str]
        ] = AirbyteDestinationNamespace.SAME_AS_SOURCE,
        prefix: Optional[str] = None,
    ):
        self.name = check.str_param(name, "name")
        self.source = check.inst_param(source, "source", AirbyteSource)
        self.destination = check.inst_param(destination, "destination", AirbyteDestination)
        self.stream_config = check.mapping_param(
            stream_config, "stream_config", key_type=str, value_type=AirbyteSyncMode
        )
        self.normalize_data = check.opt_bool_param(normalize_data, "normalize_data")
        self.destination_namespace = check.opt_inst_param(
            destination_namespace, "destination_namespace", (str, AirbyteDestinationNamespace)
        )
        self.prefix = check.opt_str_param(prefix, "prefix")

    def must_be_recreated(self, other: Optional["AirbyteConnection"]) -> bool:
        return (
            not other
            or self.source.must_be_recreated(other.source)
            or self.destination.must_be_recreated(other.destination)
        )


class InitializedAirbyteConnection:
    """User-defined Airbyte connection bound to actual created Airbyte connection."""

    def __init__(
        self,
        connection: AirbyteConnection,
        connection_id: str,
    ):
        self.connection = connection
        self.connection_id = connection_id

    @classmethod
    def from_api_json(
        cls,
        api_dict: Mapping[str, Any],
        init_sources: Mapping[str, InitializedAirbyteSource],
        init_dests: Mapping[str, InitializedAirbyteDestination],
    ):
        source = next(
            (
                source.source
                for source in init_sources.values()
                if source.source_id == api_dict["sourceId"]
            ),
            None,
        )
        dest = next(
            (
                dest.destination
                for dest in init_dests.values()
                if dest.destination_id == api_dict["destinationId"]
            ),
            None,
        )

        source = check.not_none(source, f"Could not find source with id {api_dict['sourceId']}")
        dest = check.not_none(
            dest, f"Could not find destination with id {api_dict['destinationId']}"
        )

        streams = {
            stream["stream"]["name"]: AirbyteSyncMode.from_json(stream["config"])
            for stream in api_dict["syncCatalog"]["streams"]
        }
        return cls(
            AirbyteConnection(
                name=api_dict["name"],
                source=source,
                destination=dest,
                stream_config=streams,
                normalize_data=len(api_dict["operationIds"]) > 0,
                destination_namespace=(
                    api_dict["namespaceFormat"]
                    if api_dict["namespaceDefinition"] == "customformat"
                    else AirbyteDestinationNamespace(api_dict["namespaceDefinition"])
                ),
                prefix=api_dict["prefix"] if api_dict.get("prefix") else None,
            ),
            api_dict["connectionId"],
        )


def _remove_none_values(obj: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in obj.items() if v is not None}


def _dump_class(obj: Any) -> Dict[str, Any]:
    return json.loads(json.dumps(obj, default=lambda o: _remove_none_values(o.__dict__)))


class GeneratedAirbyteSource(AirbyteSource):
    """Base class used by the codegen Airbyte sources. This class is not intended to be used directly.

    Converts all of its attributes into a source configuration dict which is passed down to the base
    AirbyteSource class.
    """

    def __init__(self, source_type: str, name: str):
        source_configuration = _dump_class(self)
        super().__init__(
            name=name, source_type=source_type, source_configuration=source_configuration
        )


class GeneratedAirbyteDestination(AirbyteDestination):
    """Base class used by the codegen Airbyte destinations. This class is not intended to be used directly.

    Converts all of its attributes into a destination configuration dict which is passed down to the
    base AirbyteDestination class.
    """

    def __init__(self, source_type: str, name: str):
        destination_configuration = _dump_class(self)
        super().__init__(
            name=name,
            destination_type=source_type,
            destination_configuration=destination_configuration,
        )
