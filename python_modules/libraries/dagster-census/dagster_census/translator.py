from collections.abc import Mapping
from typing import Any

import dagster as dg
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster._record import record
from dagster_shared.serdes import whitelist_for_serdes


@whitelist_for_serdes
@record
class CensusSync:
    """Represents a Census sync, based on data as returned from the API."""

    id: int
    name: str
    source_id: int
    destination_id: int
    mappings: list[dict[str, Any]]


@whitelist_for_serdes
@record
class CensusWorkspaceData:
    """A record representing all content in a Census workspace.
    Provided as context for the translator so that it can resolve dependencies between content.
    """

    syncs: list[CensusSync]

    @property
    def syncs_by_id(self) -> Mapping[int, CensusSync]:
        """Returns a mapping of sync IDs to CensusSync objects."""
        return {sync.id: sync for sync in self.syncs}


def generate_table_schema(sync_mappings_props: list[dict[str, Any]]) -> dg.TableSchema:
    return dg.TableSchema(
        columns=sorted(
            [
                dg.TableColumn(name=mapping["to"], type=mapping.get("field_type", "unknown"))
                for mapping in sync_mappings_props
            ],
            key=lambda col: col.name,
        )
    )


class CensusMetadataSet(NamespacedMetadataSet):
    sync_id: int
    sync_name: str
    source_id: int
    destination_id: int

    @classmethod
    def namespace(cls) -> str:
        return "dagster-census"
