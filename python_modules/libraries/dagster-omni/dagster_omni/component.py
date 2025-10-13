import itertools
from collections import defaultdict
from pathlib import Path
from typing import Optional

import dagster as dg
from dagster._annotations import preview
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from pydantic import Field

from dagster_omni.objects import OmniDocument, OmniQuery, OmniWorkspaceData
from dagster_omni.translation import (
    TRANSLATOR_DATA_METADATA_KEY,
    OmniDocumentMetadataSet,
    OmniTranslatorData,
    ResolvedOmniTranslationFn,
)
from dagster_omni.workspace import OmniWorkspace


@preview
class OmniComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    workspace: OmniWorkspace = Field(
        description="Defines configuration for interacting with an Omni instance.",
    )
    translation: Optional[ResolvedOmniTranslationFn] = Field(
        default=None,
        description="Defines how to translate an Omni object into an AssetSpec object.",
    )
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.versioned_state_storage()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig.from_args(self.defs_state, default_key=self.__class__.__name__)

    async def write_state_to_path(self, state_path: Path) -> None:
        """Fetch documents from Omni API and write state to path."""
        state = await self.workspace.fetch_omni_state()
        state_path.write_text(dg.serialize_value(state))

    def load_state_from_path(self, state_path: Path) -> OmniWorkspaceData:
        """Load state from path using Dagster's deserialization system."""
        return dg.deserialize_value(state_path.read_text(), OmniWorkspaceData)

    def _get_default_omni_spec(
        self, context: dg.ComponentLoadContext, data: OmniTranslatorData, workspace: OmniWorkspace
    ) -> Optional[dg.AssetSpec]:
        """Core function for converting an Omni document into an AssetSpec object."""
        if isinstance(data.obj, OmniDocument):
            doc = data.obj
            maybe_deps = [
                self.get_asset_spec(
                    context, OmniTranslatorData(obj=query, workspace_data=data.workspace_data)
                )
                for query in data.obj.queries
            ]

            prefix = doc.folder.path.split("/") if doc.folder else []
            user = data.workspace_data.get_user(doc.owner.id)
            owner_email = user.primary_email if user else None

            return dg.AssetSpec(
                key=dg.AssetKey([*prefix, doc.name]),
                group_name=prefix[0].replace("-", "_") if prefix else None,
                tags={label.name: "" for label in doc.labels},
                deps=list(filter(None, maybe_deps)),
                metadata={
                    **OmniDocumentMetadataSet.from_document(workspace, doc),
                    TRANSLATOR_DATA_METADATA_KEY: data,
                },
                kinds={"omni"},
                owners=[owner_email] if owner_email else None,
            )
        if isinstance(data.obj, OmniQuery):
            return dg.AssetSpec(key=dg.AssetKey([data.obj.query_config.table]))
        return None

    def get_asset_spec(
        self, context: dg.ComponentLoadContext, data: OmniTranslatorData
    ) -> Optional[dg.AssetSpec]:
        """Core function for converting an Omni document into an AssetSpec object."""
        base_asset_spec = self._get_default_omni_spec(context, data, self.workspace)
        if self.translation and base_asset_spec:
            return self.translation(base_asset_spec, data)
        else:
            return base_asset_spec

    def _build_asset_specs(
        self, context: dg.ComponentLoadContext, workspace_data: OmniWorkspaceData
    ) -> list[dg.AssetSpec]:
        """Invokes the `get_asset_spec` method on all objects in the provided `workspace_data`.
        Filters out any cases where the asset_spec is `None`, and provides a helpful error
        message in cases where keys overlap between different documents.
        """
        maybe_specs = [
            self.get_asset_spec(context, OmniTranslatorData(obj=doc, workspace_data=workspace_data))
            for doc in workspace_data.documents
        ]

        specs_by_key: dict[dg.AssetKey, list[dg.AssetSpec]] = defaultdict(list)
        for spec in filter(None, maybe_specs):
            specs_by_key[spec.key].append(spec)

        for key, specs in specs_by_key.items():
            if len(specs) == 1:
                continue

            ids = [OmniDocumentMetadataSet.extract(spec.metadata).url or spec for spec in specs]
            ids_str = "\n\t".join(map(str, ids))
            raise DagsterInvalidDefinitionError(
                f"Multiple objects map to the same key {key}:"
                f"\n\t{ids_str}\n"
                "Please ensure that each object has a unique name by updating the `translation` function."
            )

        return list(itertools.chain.from_iterable(specs_by_key.values()))

    def build_defs_from_workspace_data(
        self, context: dg.ComponentLoadContext, workspace_data: OmniWorkspaceData
    ) -> dg.Definitions:
        return dg.Definitions(assets=self._build_asset_specs(context, workspace_data))

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state = self.load_state_from_path(state_path)
        return self.build_defs_from_workspace_data(context, state)
