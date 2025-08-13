import json
from pathlib import Path
from typing import Optional

import dagster as dg
from dagster import deserialize_value, serialize_value
from dagster.components.component.state_backed_component import StateBackedComponent

from dagster_omni.objects import OmniDocument, OmniState
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

        # Use Dagster's serialization system
        serialized_state = serialize_value(state)

        with open(state_path, "w") as f:
            json.dump(serialized_state, f, indent=2)

    def load_state_from_path(self, state_path: Path) -> OmniState:
        """Load state from path using Dagster's deserialization system."""
        with open(state_path) as f:
            serialized_data = json.load(f)

        return deserialize_value(serialized_data, OmniState)

    def get_key_for_query_id(self, state: OmniState, query_id: str) -> Optional[dg.AssetKey]:
        query = state.get_query_by_id(query_id)
        if query and query.query_config and query.query_config.table:
            return dg.AssetKey([query.query_config.table])
        return None

    def get_asset_spec(self, obj: OmniDocument, state: OmniState) -> Optional[dg.AssetSpec]:
        deps = filter(
            None,
            [self.get_key_for_query_id(state, query_id) for query_id in obj.query_ids],
        )

        if obj.folder is None or obj.folder.path.startswith("sales"):
            return None

        prefix = obj.folder.path.split("/") if obj.folder else []
        return dg.AssetSpec(
            key=dg.AssetKey([*prefix, obj.name]),
            group_name=prefix[0].replace("-", "_") if prefix else None,
            tags={label.name: "" for label in obj.labels},
            deps=deps,
            metadata={
                "omni/document_id": obj.identifier,
                "omni/document_name": obj.name,
                "omni/document_type": obj.type,
                "omni/document_scope": obj.scope,
                "omni/document_connection_id": obj.connection_id,
                "omni/document_has_dashboard": obj.has_dashboard,
            },
            kinds={"omni"},
        )

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        with open(state_path) as f:
            serialized_state = json.load(f)

        state = deserialize_value(serialized_state, OmniState)

        return dg.Definitions(
            assets=list(filter(None, [self.get_asset_spec(doc, state) for doc in state.documents]))
        )
