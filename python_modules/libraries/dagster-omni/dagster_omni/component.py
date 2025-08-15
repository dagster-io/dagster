from pathlib import Path
from typing import Optional

import dagster as dg
from dagster import deserialize_value, serialize_value
from dagster.components.component.state_backed_component import StateBackedComponent

from dagster_omni.objects import OmniDocument, OmniQuery, OmniState
from dagster_omni.workspace import OmniWorkspace


class OmniComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    base_url: str
    api_key: str

    @property
    def workspace(self) -> OmniWorkspace:
        """Return an instance of OmniWorkspace for API interactions."""
        return OmniWorkspace(self.base_url, self.api_key)

    async def write_state_to_path(self, state_path: Path) -> None:
        """Fetch documents, models, and topics from Omni API and write state to path."""
        state = await self.workspace.fetch_omni_state()
        state_path.write_text(serialize_value(state))

    def load_state_from_path(self, state_path: Path) -> OmniState:
        """Load state from path using Dagster's deserialization system."""
        return deserialize_value(state_path.read_text(), OmniState)

    def _get_table_dependencies(self, document: OmniDocument) -> list[dg.AssetKey]:
        """Get unique table dependencies from document's queries."""
        tables = set()
        for query in document.queries:
            if query.query_config and query.query_config.table:
                tables.add(query.query_config.table)
        return [dg.AssetKey([table]) for table in tables]

    def get_asset_key_for_query(self, query: OmniQuery) -> Optional[dg.AssetKey]:
        if query.query_config and query.query_config.table:
            return dg.AssetKey([query.query_config.table])
        return None

    def get_asset_spec(self, document: OmniDocument) -> Optional[dg.AssetSpec]:
        deps = list(
            filter(None, [self.get_asset_key_for_query(query) for query in document.queries])
        )

        if document.folder is None or document.folder.path.startswith("sales"):
            return None

        prefix = document.folder.path.split("/") if document.folder else []
        return dg.AssetSpec(
            key=dg.AssetKey([*prefix, document.name]),
            group_name=prefix[0].replace("-", "_") if prefix else None,
            tags={label.name: "" for label in document.labels},
            deps=deps,
            metadata={
                "omni/document_id": document.identifier,
                "omni/document_name": document.name,
                "omni/document_type": document.type,
                "omni/document_connection_id": document.connection_id,
            },
            kinds={"omni"},
        )

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state = self.load_state_from_path(state_path)

        return dg.Definitions(
            assets=list(filter(None, [self.get_asset_spec(doc) for doc in state.documents]))
        )
