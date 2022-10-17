from enum import Enum
from typing import Any, Dict, Mapping, Optional


class AirbyteSyncMode(Enum):
    """
    Represents the sync mode for a given Airbyte stream.
    """

    FULL_REFRESH_APPEND = ("full_refresh", "append")
    FULL_REFRESH_OVERWRITE = ("full_refresh", "overwrite")
    INCREMENTAL_APPEND = ("incremental", "append")
    INCREMENTAL_OVERWRITE = ("incremental", "overwrite")
    INCREMENTAL_APPEND_DEDUP = ("incremental", "append_dedup")


class AirbyteSource:
    """
    Represents a user-defined Airbyte source.
    """

    def __init__(self, name: str, source_type: str, source_configuration: Dict[str, Any]):
        self.name = name
        self.source_type = source_type
        self.source_configuration = source_configuration

    def must_be_recreated(self, other: "AirbyteSource") -> bool:
        return self.name != other.name or self.source_configuration != other.source_configuration


class InitializedAirbyteSource:
    """
    User-defined Airbyte source bound to actual created Airbyte source.
    """

    def __init__(self, source: AirbyteSource, source_id: str, source_definition_id: str):
        self.source = source
        self.source_id = source_id
        self.source_definition_id = source_definition_id

    @classmethod
    def from_api_json(cls, api_json: Dict[str, Any]):
        return cls(
            AirbyteSource(
                api_json["name"],
                api_json["sourceName"],
                api_json["connectionConfiguration"],
            ),
            api_json["sourceId"],
            "",
        )


class AirbyteDestination:
    """
    Represents a user-defined Airbyte destination.
    """

    def __init__(self, name: str, destination_type: str, destination_configuration: Dict[str, Any]):
        self.name = name
        self.destination_type = destination_type
        self.destination_configuration = destination_configuration

    def must_be_recreated(self, other: "AirbyteDestination") -> bool:
        return (
            self.name != other.name
            or self.destination_configuration != other.destination_configuration
        )


class InitializedAirbyteDestination:
    """
    User-defined Airbyte destination bound to actual created Airbyte destination.
    """

    def __init__(
        self, destination: AirbyteDestination, destination_id: str, destination_definition_id: str
    ):
        self.destination = destination
        self.destination_id = destination_id
        self.destination_definition_id = destination_definition_id

    @classmethod
    def from_api_json(cls, api_json: Dict[str, Any]):
        return cls(
            AirbyteDestination(
                api_json["name"],
                api_json["destinationName"],
                api_json["connectionConfiguration"],
            ),
            api_json["destinationId"],
            "",
        )


class AirbyteConnection:
    """
    User-defined Airbyte connection.
    """

    def __init__(
        self,
        name: str,
        source: AirbyteSource,
        destination: AirbyteDestination,
        stream_config: Dict[str, AirbyteSyncMode],
        normalize_data: Optional[bool] = None,
    ):
        self.name = name
        self.source = source
        self.destination = destination
        self.stream_config = stream_config
        self.normalize_data = normalize_data

    def must_be_recreated(self, other: Optional["AirbyteConnection"]) -> bool:
        return (
            not other
            or self.source.must_be_recreated(other.source)
            or self.destination.must_be_recreated(other.destination)
        )


class InitializedAirbyteConnection:
    """
    User-defined Airbyte connection bound to actual created Airbyte connection.
    """

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
        api_dict: Dict[str, Any],
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

        streams = {
            stream["stream"]["name"]: AirbyteSyncMode(
                (
                    stream["config"]["syncMode"],
                    stream["config"]["destinationSyncMode"],
                )
            )
            for stream in api_dict["syncCatalog"]["streams"]
        }
        return cls(
            AirbyteConnection(
                api_dict["name"],
                source,
                dest,
                streams,
                len(api_dict["operationIds"]) > 0,
            ),
            api_dict["connectionId"],
        )
