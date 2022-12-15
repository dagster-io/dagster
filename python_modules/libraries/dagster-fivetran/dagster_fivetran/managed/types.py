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
        destination_configuration: Dict[str, Any],
        region: str = "GCP_US_EAST4",
        time_zone_offset: Optional[int] = None,
    ):
        """
        Args:
            name (str): The name of the destination.
            destination_type (str): The type of the destination. See the Fivetran API docs for a list
                of valid destination types.
            destination_configuration (Dict[str, Any]): The configuration of the destination.
            region (str): The region of the destination. Defaults to "GCP_US_EAST4".
            time_zone_offset (Optional[int]): The UTC time zone offset of the destination. Defaults to 0 (UTC).
        """
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
    """
    Represents a user-defined Fivetran connector.
    """

    def __init__(
        self,
        schema_name: str,
        source_type: str,
        source_configuration: Dict[str, Any],
        destination: Optional[FivetranDestination],
        schema_configuration: Optional[Dict[str, Any]] = None,
        auth_configuration: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            schema_name (str): The name of the schema to create in the destination.
            source_type (str): The type of source to connect to. See the Fivetran API docs for a
                list of supported source types: https://fivetran.com/docs/rest-api/connectors#create-a-connector
            source_configuration (Dict[str, Any]): The configuration for the source, as defined by the Fivetran API.
            destination (Optional[FivetranDestination]): The destination to connect to.
            schema_configuration (Optional[Dict[str, Any]]): Optional schema configuration, to select certain schemas
                or tables from the source to sync. By default, selects all schemas and tables. Input is a map of schema
                names to either True (to select all tables in the schema) or a map of table names to True (to select
                individual tables). For example, to select all tables in schema "my_schema_1" and only table "my_table_1"
                in schema "my_schema_2", use the following configuration:

                .. code-block:: python
                    {
                        "my_schema_1": True,
                        "my_schema_2": {
                            "my_table_1": True,
                            "my_table_2": False,
                        },
                    }
        """
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
        self.schema_configuration = check.opt_dict_param(
            schema_configuration, "schema_configuration", key_type=str
        )

    def must_be_recreated(self, other: "FivetranConnector") -> bool:
        return self.schema_name != other.schema_name or self.source_type != other.source_type


def _table_json_to_table_configuration(schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        table["name_in_destination"]: True
        for table in schema["tables"].values()
        if table["enabled"]
    }


def _schemas_json_to_schema_configuration(schemas: Dict[str, Any]) -> Dict[str, Any]:
    if not "schemas" in schemas:
        return {}
    return {
        schema["name_in_destination"]: schema["enabled"]
        if "tables" not in schema
        else _table_json_to_table_configuration(schema)
        for schema in schemas["schemas"].values()
    }


class InitializedFivetranConnector:
    def __init__(self, connector: FivetranConnector, connector_id: str):
        self.connector = connector
        self.connector_id = connector_id

    @classmethod
    def from_api_json(cls, api_json: Dict[str, Any], schemas_json: Dict[str, Any]):
        return cls(
            connector=FivetranConnector(
                schema_name=api_json["schema"],
                source_type=api_json["service"],
                source_configuration=api_json["config"] or {},
                auth_configuration=api_json.get("auth") or {},
                destination=None,
                schema_configuration=_schemas_json_to_schema_configuration(schemas_json),
            ),
            connector_id=api_json["id"],
        )
