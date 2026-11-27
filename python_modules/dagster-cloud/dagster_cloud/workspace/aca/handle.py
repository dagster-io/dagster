from typing import NamedTuple


class AcaServerHandle(NamedTuple):
    """Handle for an Azure Container App acting as a Dagster code server."""

    app_name: str
    hostname: str
    tags: dict[str, str]
    create_timestamp: float | None
