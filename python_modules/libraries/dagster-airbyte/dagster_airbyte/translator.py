from typing import Any, Mapping, NamedTuple

from dagster._annotations import experimental
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes


class AirbyteConnectionTableProps(NamedTuple): ...


@whitelist_for_serdes
@record
class AirbyteConnection:
    """Represents an Airbyte connection, based on data as returned from the API."""

    @classmethod
    def from_connection_details(
        cls,
        connection_details: Mapping[str, Any],
    ) -> "AirbyteConnection":
        raise NotImplementedError()


@whitelist_for_serdes
@record
class AirbyteDestination:
    """Represents an Airbyte destination, based on data as returned from the API."""

    @classmethod
    def from_destination_details(
        cls,
        destination_details: Mapping[str, Any],
    ) -> "AirbyteDestination":
        raise NotImplementedError()


@record
class AirbyteWorkspaceData:
    """A record representing all content in an Airbyte workspace.
    This applies to both Airbyte OSS and Cloud.
    """

    connections_by_id: Mapping[str, AirbyteConnection]
    destinations_by_id: Mapping[str, AirbyteDestination]


@experimental
class DagsterAirbyteTranslator:
    """Translator class which converts a `AirbyteConnectionTableProps` object into AssetSpecs.
    Subclass this class to implement custom logic for Airbyte content.
    """

    def get_asset_spec(self, props: AirbyteConnectionTableProps) -> AssetSpec:
        """Get the AssetSpec for a table synced by an Airbyte connection."""
        raise NotImplementedError()
