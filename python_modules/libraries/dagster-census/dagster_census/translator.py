from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple

import dagster as dg
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet, TableMetadataSet
from dagster._record import record
from dagster._utils.cached_method import cached_method
from dagster_shared.serdes import whitelist_for_serdes

DAGSTER_CENSUS_TRANSLATOR_METADATA_KEY = "dagster-census/dagster_census_translator"


class CensusSyncTableProps(NamedTuple):
    sync_id: int
    sync_name: str
    source_id: int
    destination_id: int
    mappings: list[dict[str, Any]]


@whitelist_for_serdes
@record
class CensusSync:
    """Represents a Fivetran sync, based on data as returned from the API."""

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

    @cached_method
    def to_census_sync_table_props_data(self) -> Sequence[CensusSyncTableProps]:
        data = []

        for sync in self.syncs:
            data.append(
                CensusSyncTableProps(
                    sync_id=sync.id,
                    sync_name=sync.name,
                    source_id=sync.source_id,
                    destination_id=sync.destination_id,
                    mappings=sync.mappings,
                )
            )

        return data


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
        return "dagster-airbyte"


class DagsterCensusTranslator:
    """Translator class which converts a `CensusSyncTableProps` object into AssetSpecs.
    Subclass this class to implement custom logic on how to translate Census content into asset spec.
    """

    def get_asset_spec(self, props: CensusSyncTableProps) -> dg.AssetSpec:
        """Get the AssetSpec for a table synced by a Census Sync."""
        metadata = {
            **TableMetadataSet(
                column_schema=generate_table_schema(props.mappings),
                table_name=props.sync_name,
            ),
            **CensusMetadataSet(
                sync_id=props.sync_id,
                sync_name=props.sync_name,
                source_id=props.source_id,
                destination_id=props.destination_id,
            ),
        }

        return dg.AssetSpec(
            key=dg.AssetKey(props.sync_name),
            metadata=metadata,
            description=f"Asset generated from Census sync {props.sync_id}",
            kinds={"census"},
        )
