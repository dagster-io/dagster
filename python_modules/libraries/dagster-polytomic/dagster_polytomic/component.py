import itertools
from collections import defaultdict
from pathlib import Path
from typing import Optional, Self

import dagster as dg
from dagster._annotations import preview
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster.components.utils.translation import ResolvedTranslationFn
from dagster_shared.record import record
from pydantic import Field

from dagster_polytomic.objects import PolytomicBulkSyncEnrichedSchema, PolytomicWorkspaceData
from dagster_polytomic.workspace import PolytomicWorkspace

_TRANSLATOR_DATA_METADATA_KEY = ".dagster-polytomic/translator_data"


class PolytomicSchemaMetadataSet(NamespacedMetadataSet):
    """Represents metadata that is captured from a Polytomic schema."""

    id: str
    bulk_sync_id: str
    output_name: Optional[str] = None
    partition_key: Optional[str] = None
    tracking_field: Optional[str] = None
    source_connection_id: Optional[str] = None
    source_connection_name: Optional[str] = None
    destination_connection_id: Optional[str] = None
    destination_connection_name: Optional[str] = None

    @classmethod
    def from_enriched_schema(cls, enriched_schema: PolytomicBulkSyncEnrichedSchema) -> Self:
        return cls(
            id=enriched_schema.id,
            bulk_sync_id=enriched_schema.bulk_sync_id,
            output_name=enriched_schema.output_name,
            partition_key=enriched_schema.partition_key,
            tracking_field=enriched_schema.tracking_field,
            source_connection_id=enriched_schema.source_connection_id,
            source_connection_name=enriched_schema.source_connection_name,
            destination_connection_id=enriched_schema.destination_connection_id,
            destination_connection_name=enriched_schema.destination_connection_name,
        )

    @classmethod
    def namespace(cls) -> str:
        return "dagster-omni"


@record
class PolytomicTranslatorData:
    """Container class for data required to translate an object in an
    Polytomic workspace into a Dagster definition.

    Properties:
        obj (PolytomicBulkSyncEnrichedSchema): The object to translate.
        workspace_data (PolytomicWorkspaceData): Global workspace data.
    """

    obj: PolytomicBulkSyncEnrichedSchema
    workspace_data: PolytomicWorkspaceData


@preview
class PolytomicComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    workspace: PolytomicWorkspace = Field(
        description="Defines configuration for interacting with a Polytomic organization.",
    )
    translation: Optional[ResolvedTranslationFn[PolytomicTranslatorData]] = Field(
        default=None,
        description="Defines how to translate a Polytomic object into an AssetSpec object.",
    )
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.versioned_state_storage()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig.from_args(self.defs_state, default_key=self.__class__.__name__)

    async def write_state_to_path(self, state_path: Path) -> None:
        """Fetch documents from Polytomic API and write state to path."""
        state = await self.workspace.fetch_polytomic_state()
        state_path.write_text(dg.serialize_value(state))

    def load_state_from_path(self, state_path: Path) -> PolytomicWorkspaceData:
        """Load state from path using Dagster's deserialization system."""
        return dg.deserialize_value(state_path.read_text(), PolytomicWorkspaceData)

    def _get_default_asset_spec(self, data: PolytomicTranslatorData) -> dg.AssetSpec:
        """Core function for converting a Polytomic schema into an AssetSpec object."""
        if isinstance(data.obj, PolytomicBulkSyncEnrichedSchema):
            enriched_schema = data.obj
            return dg.AssetSpec(
                key=dg.AssetKey(
                    [enriched_schema.destination_configuration_schema or "", enriched_schema.id]
                ),
                group_name=enriched_schema.destination_configuration_schema.replace("-", "_")
                if enriched_schema.destination_configuration_schema
                else None,
                metadata={
                    _TRANSLATOR_DATA_METADATA_KEY: data,
                    **PolytomicSchemaMetadataSet.from_enriched_schema(
                        enriched_schema=enriched_schema
                    ),
                },
                kinds={"polytomic"},
            )
        else:
            raise ValueError(f"Unsupported object type: {type(data.obj)}")

    def get_asset_spec(self, data: PolytomicTranslatorData) -> dg.AssetSpec:
        """Core function for converting a Polytomic object into an AssetSpec object."""
        base_asset_spec = self._get_default_asset_spec(data)
        if self.translation:
            return self.translation(base_asset_spec, data)
        else:
            return base_asset_spec

    def _build_asset_specs(self, workspace_data: PolytomicWorkspaceData) -> list[dg.AssetSpec]:
        """Invokes the `get_asset_spec` method on all objects in the provided `workspace_data`.
        Filters out any cases where the asset_spec is `None`, and provides a helpful error
        message in cases where keys overlap between different documents.
        """
        maybe_specs = [
            self.get_asset_spec(
                PolytomicTranslatorData(obj=enriched_schema, workspace_data=workspace_data)
            )
            for enriched_schema in itertools.chain.from_iterable(
                workspace_data.enriched_schemas_by_bulk_sync_id.values()
            )
        ]

        specs_by_key: dict[dg.AssetKey, list[dg.AssetSpec]] = defaultdict(list)
        for spec in filter(None, maybe_specs):
            specs_by_key[spec.key].append(spec)

        for key, specs in specs_by_key.items():
            if len(specs) == 1:
                continue

            ids = [
                PolytomicSchemaMetadataSet.extract(spec.metadata).bulk_sync_id or spec
                for spec in specs
            ]
            ids_str = "\n\t".join(map(str, ids))
            raise DagsterInvalidDefinitionError(
                f"Multiple objects map to the same key {key}:"
                f"\n\t{ids_str}\n"
                "Please ensure that each object has a unique name by updating the `translation` function."
            )

        return list(itertools.chain.from_iterable(specs_by_key.values()))

    def build_defs_from_workspace_data(
        self, workspace_data: PolytomicWorkspaceData
    ) -> dg.Definitions:
        return dg.Definitions(assets=self._build_asset_specs(workspace_data))

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state = self.load_state_from_path(state_path)
        return self.build_defs_from_workspace_data(state)
