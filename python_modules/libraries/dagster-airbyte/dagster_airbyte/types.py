from typing import Any, Mapping, NamedTuple, Optional

from dagster._core.definitions.metadata.table import TableSchema


class AirbyteTableMetadata:
    def __init__(
        self,
        schema: TableSchema,
        normalization_tables: Optional[Mapping[str, "AirbyteTableMetadata"]] = None,
    ):
        """Contains metadata about an Airbyte table, including its schema and any created normalization tables."""
        self.schema = schema
        self.normalization_tables = normalization_tables or dict()


class AirbyteOutput(
    NamedTuple(
        "_AirbyteOutput",
        [
            ("job_details", Mapping[str, Any]),
            ("connection_details", Mapping[str, Any]),
        ],
    )
):
    """Contains recorded information about the state of a Airbyte connection job after a sync completes.

    Attributes:
        job_details (Dict[str, Any]):
            The raw Airbyte API response containing the details of the initiated job. For info
            on the schema of this dictionary, see: https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#post-/v1/jobs/get
        connection_details (Dict[str, Any]):
            The raw Airbyte API response containing the details of the sync'd connector. For info
            on the schema of this dictionary, see: https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#post-/v1/connections/get
    """
