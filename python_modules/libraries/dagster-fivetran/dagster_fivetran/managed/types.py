from typing import Any, Dict, Optional

import dagster._check as check


class FivetranDestination:
    """
    Represents a user-defined Fivetran destination.
    """

    def __init__(
        self,
        name: str,
        destination_type: str,
        region: str,
        destination_configuration: Dict[str, Any],
        time_zone_offset: Optional[int] = None,
    ):
        self.name = check.str_param(name, "name")
        self.region = check.str_param(region, "region")
        self.time_zone_offset = check.opt_int_param(time_zone_offset, "time_zone_offset") or 0
        self.destination_type = check.str_param(destination_type, "destination_type")
        self.destination_configuration = check.dict_param(
            destination_configuration, "destination_configuration", key_type=str
        )

    def must_be_recreated(self, other: "FivetranDestination") -> bool:
        return self.name != other.name or self.destination_type != other.destination_type


class InitializedFivetranDestination:
    def __init__(self, destination: FivetranDestination, destination_id: str):
        self.destination = destination
        self.destination_id = destination_id

    @classmethod
    def from_api_json(cls, name: str, api_json: Dict[str, Any]):
        return cls(
            destination=FivetranDestination(
                name=name,
                destination_type=api_json["service"],
                region=api_json["region"],
                time_zone_offset=int(api_json["time_zone_offset"]),
                destination_configuration=api_json["config"],
            ),
            destination_id=api_json["id"],
        )


class FivetranConnector:
    def __init__(
        self,
        schema_name: str,
        source_type: str,
        source_configuration: Dict[str, Any],
        destination: Optional[FivetranDestination],
        auth_configuration: Optional[Dict[str, Any]] = None,
    ):
        self.schema_name = check.str_param(schema_name, "schema_name")
        self.source_type = check.str_param(source_type, "source_type")
        self.source_configuration = check.dict_param(
            source_configuration, "source_configuration", key_type=str
        )
        self.auth_configuration = check.opt_dict_param(
            auth_configuration, "auth_configuration", key_type=str
        )
        self.paused = True
        self.destination = check.opt_inst_param(destination, "destination", FivetranDestination)

    def must_be_recreated(self, other: "FivetranConnector") -> bool:
        return self.schema_name != other.schema_name or self.source_type != other.source_type


class InitializedFivetranConnector:
    def __init__(self, connector: FivetranConnector, connector_id: str):
        self.connector = connector
        self.connector_id = connector_id

    @classmethod
    def from_api_json(cls, api_json: Dict[str, Any]):
        return cls(
            connector=FivetranConnector(
                schema_name=api_json["schema"],
                source_type=api_json["service"],
                source_configuration=api_json["config"] or {},
                auth_configuration=api_json.get("auth") or {},
                destination=None,
            ),
            connector_id=api_json["id"],
        )
