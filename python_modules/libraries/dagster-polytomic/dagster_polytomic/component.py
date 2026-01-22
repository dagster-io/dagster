import itertools
from collections import defaultdict
from pathlib import Path
from typing import Optional

import dagster as dg
from dagster._annotations import preview
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from pydantic import Field

from dagster_polytomic.objects import PolytomicBulkSyncEnrichedSchema, PolytomicWorkspaceData
from dagster_polytomic.translation import (
    _TRANSLATOR_DATA_METADATA_KEY,
    PolytomicSchemaMetadataSet,
    PolytomicTranslatorData,
    ResolvedPolytomicTranslationFn,
)
from dagster_polytomic.workspace import PolytomicWorkspace


@preview
class PolytomicComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    workspace: PolytomicWorkspace = Field(
        description="Defines configuration for interacting with a Polytomic organization.",
    )
    translation: Optional[ResolvedPolytomicTranslationFn] = Field(
        default=None,
        description="Defines how to translate a Polytomic object into an AssetSpec object.",
    )
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.local_filesystem()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.workspace.identity.organization_name}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    async def write_state_to_path(self, state_path: Path) -> None:
        """Fetch documents from Polytomic API and write state to path."""
        state = await self.workspace.fetch_polytomic_state()
        state_path.write_text(dg.serialize_value(state))

    def load_state_from_path(self, state_path: Path) -> PolytomicWorkspaceData:
        """Load state from path using Dagster's deserialization system."""
        return dg.deserialize_value(state_path.read_text(), PolytomicWorkspaceData)

    def _get_default_polytomic_spec(self, data: PolytomicTranslatorData) -> Optional[dg.AssetSpec]:
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
                    **TableMetadataSet(
                        table_name=f"{enriched_schema.destination_configuration_schema}.{enriched_schema.id}"
                        if enriched_schema.destination_configuration_schema
                        else enriched_schema.id
                    ),
                },
                kinds={"polytomic"},
            )
        return None

    def get_asset_spec(self, data: PolytomicTranslatorData) -> Optional[dg.AssetSpec]:
        """Core function for converting a Polytomic object into an AssetSpec object."""
        base_asset_spec = self._get_default_polytomic_spec(data)
        if self.translation and base_asset_spec:
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
