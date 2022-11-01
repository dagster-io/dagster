from enum import Enum
from typing import Any, Dict, Mapping, Optional

import dagster._check as check


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
        self.name = check.str_param(name, "name")
        self.source_type = check.str_param(source_type, "source_type")
        self.source_configuration = check.dict_param(
            source_configuration, "source_configuration", key_type=str
        )

    def must_be_recreated(self, other: "AirbyteSource") -> bool:
        return self.name != other.name or self.source_configuration != other.source_configuration


class InitializedAirbyteSource:
    """
    User-defined Airbyte source bound to actual created Airbyte source.
    """

    def __init__(self, source: AirbyteSource, source_id: str, source_definition_id: Optional[str]):
        self.source = source
        self.source_id = source_id
        self.source_definition_id = source_definition_id

    @classmethod
    def from_api_json(cls, api_json: Dict[str, Any]):
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
    """
    Represents a user-defined Airbyte destination.
    """

    def __init__(self, name: str, destination_type: str, destination_configuration: Dict[str, Any]):
        self.name = check.str_param(name, "name")
        self.destination_type = check.str_param(destination_type, "destination_type")
        self.destination_configuration = check.dict_param(
            destination_configuration, "destination_configuration", key_type=str
        )

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
        self,
        destination: AirbyteDestination,
        destination_id: str,
        destination_definition_id: Optional[str],
    ):
        self.destination = destination
        self.destination_id = destination_id
        self.destination_definition_id = destination_definition_id

    @classmethod
    def from_api_json(cls, api_json: Dict[str, Any]):
        return cls(
            destination=AirbyteDestination(
                name=api_json["name"],
                destination_type=api_json["destinationName"],
                destination_configuration=api_json["connectionConfiguration"],
            ),
            destination_id=api_json["destinationId"],
            destination_definition_id=None,
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
        self.name = check.str_param(name, "name")
        self.source = check.inst_param(source, "source", AirbyteSource)
        self.destination = check.inst_param(destination, "destination", AirbyteDestination)
        self.stream_config = check.dict_param(
            stream_config, "stream_config", key_type=str, value_type=AirbyteSyncMode
        )
        self.normalize_data = check.opt_bool_param(normalize_data, "normalize_data")

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

        source = check.not_none(source, f"Could not find source with id {api_dict['sourceId']}")
        dest = check.not_none(
            dest, f"Could not find destination with id {api_dict['destinationId']}"
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
                name=api_dict["name"],
                source=source,
                destination=dest,
                stream_config=streams,
                normalize_data=len(api_dict["operationIds"]) > 0,
            ),
            api_dict["connectionId"],
        )
