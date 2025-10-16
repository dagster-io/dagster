from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Optional

import dagster as dg
from dagster._annotations import public
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster.components import ComponentLoadContext, Model, Resolvable, Resolver
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.base import resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from pydantic import BaseModel, Field

from dagster_tableau.components.translation import (
    ResolvedMultilayerTranslationFn,
    create_tableau_component_translator,
)
from dagster_tableau.resources import BaseTableauWorkspace, TableauCloudWorkspace
from dagster_tableau.translator import (
    DagsterTableauTranslator,
    TableauTranslatorData,
    TableauWorkspaceData,
)


class TableauWorkspaceArgs(Model, Resolvable):
    """Arguments for configuring a Tableau workspace connection."""

    connected_app_client_id: str = Field(
        ...,
        description="Tableau connected app client ID for authentication.",
    )
    connected_app_secret_id: str = Field(
        ...,
        description="Tableau connected app secret ID.",
    )
    connected_app_secret_value: str = Field(
        ...,
        description="Tableau connected app secret value.",
    )
    username: str = Field(
        ...,
        description="Tableau username for authentication.",
    )
    site_name: str = Field(
        ...,
        description="Tableau site name.",
    )
    pod_name: str = Field(
        default="10ax",
        description="Tableau pod name (e.g. '10ax', '10ay'). Defaults to '10ax'.",
    )


def _resolve_tableau_workspace(
    context: ResolutionContext, model: BaseModel
) -> TableauCloudWorkspace:
    """Resolves a TableauWorkspaceArgs model into a TableauCloudWorkspace resource."""
    resolved = resolve_fields(model=model, resolved_cls=TableauWorkspaceArgs, context=context)
    return TableauCloudWorkspace(**resolved)


@public
@dataclass
class TableauWorkspaceComponent(StateBackedComponent, Resolvable):
    """Pulls in the contents of a Tableau workspace into Dagster assets.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_tableau.TableauWorkspaceComponent
            attributes:
              workspace:
                connected_app_client_id: "{{ env.TABLEAU_CLIENT_ID }}"
                connected_app_secret_id: "{{ env.TABLEAU_SECRET_ID }}"
                connected_app_secret_value: "{{ env.TABLEAU_SECRET_VALUE }}"
                username: "{{ env.TABLEAU_USERNAME }}"
                site_name: my_site
                pod_name: 10ax
    """

    workspace: Annotated[
        BaseTableauWorkspace,
        Resolver(
            _resolve_tableau_workspace,
            model_field_name="workspace",
            model_field_type=TableauWorkspaceArgs.model(),
        ),
    ]
    translation: Optional[ResolvedMultilayerTranslationFn] = None
    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.legacy_code_server_snapshots
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.workspace.site_name}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    @cached_property
    def translator(self) -> DagsterTableauTranslator:
        translator_cls = create_tableau_component_translator(TableauWorkspaceComponent)
        return translator_cls(self)

    @cached_property
    def _base_translator(self) -> DagsterTableauTranslator:
        return DagsterTableauTranslator()

    def get_asset_spec(self, data: TableauTranslatorData) -> AssetSpec:
        return self._base_translator.get_asset_spec(data)

    def _load_asset_specs(self, state: TableauWorkspaceData) -> list[AssetSpec]:
        # Process all content types
        asset_specs = []
        for sheet_data in state.sheets_by_id.values():
            translator_data = TableauTranslatorData(content_data=sheet_data, workspace_data=state)
            asset_specs.append(self.translator.get_asset_spec(translator_data))

        for dashboard_data in state.dashboards_by_id.values():
            translator_data = TableauTranslatorData(
                content_data=dashboard_data, workspace_data=state
            )
            asset_specs.append(self.translator.get_asset_spec(translator_data))

        for data_source_data in state.data_sources_by_id.values():
            translator_data = TableauTranslatorData(
                content_data=data_source_data, workspace_data=state
            )
            asset_specs.append(self.translator.get_asset_spec(translator_data))

        return asset_specs

    async def write_state_to_path(self, state_path: Path) -> None:
        """Fetches Tableau workspace data and writes it to the state path."""
        # Fetch the workspace data
        workspace_data = self.workspace.fetch_tableau_workspace_data()

        # Serialize and write to path
        state_path.write_text(dg.serialize_value(workspace_data))

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        """Builds Dagster definitions from the cached Tableau workspace state."""
        if state_path is None:
            return dg.Definitions()

        # Deserialize workspace data
        workspace_data = dg.deserialize_value(state_path.read_text(), TableauWorkspaceData)

        specs = self._load_asset_specs(workspace_data)

        return dg.Definitions(assets=specs)
