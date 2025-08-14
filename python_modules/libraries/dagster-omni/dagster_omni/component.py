import itertools
from collections import defaultdict
from pathlib import Path
from typing import Optional, Union

import dagster as dg
from dagster._annotations import preview
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster._core.definitions.metadata.metadata_value import UrlMetadataValue
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.translation import ResolvedTranslationFn
from dagster_shared.record import record
from pydantic import Field
from typing_extensions import Self

from dagster_omni.objects import OmniDocument, OmniQuery, OmniWorkspaceData
from dagster_omni.workspace import OmniWorkspace

_TRANSLATOR_DATA_METADATA_KEY = ".dagster-omni/translator_data"


class OmniDocumentMetadataSet(NamespacedMetadataSet):
    url: Optional[UrlMetadataValue] = None
    document_name: str
    document_type: str

    @classmethod
    def from_document(cls, workspace: OmniWorkspace, document: OmniDocument) -> Self:
        url_str = f"{workspace.base_url.rstrip('/')}/dashboards/{document.identifier}"
        return cls(
            url=UrlMetadataValue(url_str) if document.has_dashboard else None,
            document_name=document.name,
            document_type=document.type,
        )

    @classmethod
    def namespace(cls) -> str:
        return "dagster-omni"


@record
class OmniTranslatorData:
    """Container class for data required to translate an object in an
    Omni workspace into a Dagster definition.

    Properties:
        obj (Union[OmniDocument, OmniQuery]): The object to translate.
        workspace_data (OmniWorkspaceData): Global workspace data.
    """

    obj: Union[OmniDocument, OmniQuery]
    workspace_data: OmniWorkspaceData


@preview
class OmniComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    workspace: OmniWorkspace = Field(
        description="Defines configuration for interacting with an Omni instance.",
    )
    translation: Optional[ResolvedTranslationFn[OmniTranslatorData]] = Field(
        default=None,
        description="Defines how to translate an Omni object into an AssetSpec object.",
    )

    async def write_state_to_path(self, state_path: Path) -> None:
        """Fetch documents from Omni API and write state to path."""
        state = await self.workspace.fetch_omni_state()
        state_path.write_text(dg.serialize_value(state))

    def load_state_from_path(self, state_path: Path) -> OmniWorkspaceData:
        """Load state from path using Dagster's deserialization system."""
        return dg.deserialize_value(state_path.read_text(), OmniWorkspaceData)

    def _get_default_asset_spec(self, data: OmniTranslatorData) -> dg.AssetSpec:
        """Core function for converting an Omni document into an AssetSpec object."""
        if isinstance(data.obj, OmniDocument):
            doc = data.obj
            deps = [
                self.get_asset_spec(
                    OmniTranslatorData(obj=query, workspace_data=data.workspace_data)
                )
                for query in doc.queries
            ]

            prefix = doc.folder.path.split("/") if doc.folder else []
            return dg.AssetSpec(
                key=dg.AssetKey([*prefix, doc.name]),
                group_name=prefix[0].replace("-", "_") if prefix else None,
                tags={label.name: "" for label in doc.labels},
                deps=deps,
                metadata={
                    **OmniDocumentMetadataSet.from_document(self.workspace, doc),
                    _TRANSLATOR_DATA_METADATA_KEY: data,
                },
                kinds={"omni"},
            )
        elif isinstance(data.obj, OmniQuery):
            return dg.AssetSpec(key=dg.AssetKey([data.obj.query_config.table]))
        else:
            raise ValueError(f"Unsupported object type: {type(data.obj)}")

    def get_asset_spec(self, data: OmniTranslatorData) -> dg.AssetSpec:
        """Core function for converting an Omni document into an AssetSpec object."""
        base_asset_spec = self._get_default_asset_spec(data)
        if self.translation:
            return self.translation(base_asset_spec, data)
        else:
            return base_asset_spec

    def _build_asset_specs(self, workspace_data: OmniWorkspaceData) -> list[dg.AssetSpec]:
        """Invokes the `get_asset_spec` method on all objects in the provided `workspace_data`.
        Filters out any cases where the asset_spec is `None`, and provides a helpful error
        message in cases where keys overlap between different documents.
        """
        maybe_specs = [
            self.get_asset_spec(OmniTranslatorData(obj=doc, workspace_data=workspace_data))
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

    def build_defs_from_workspace_data(self, workspace_data: OmniWorkspaceData) -> dg.Definitions:
        return dg.Definitions(assets=self._build_asset_specs(workspace_data))

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state = self.load_state_from_path(state_path)
        return self.build_defs_from_workspace_data(state)
