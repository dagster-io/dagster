from collections import defaultdict
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

import dagster as dg
from dagster._annotations import beta, public
from dagster._utils.names import clean_name_lower
from dagster.components import ComponentLoadContext, Model, Resolvable, Resolver
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.base import resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster_shared import check
from pydantic import BaseModel, Field

from dagster_tableau.components.translation import (
    ResolvedMultilayerTranslationFn,
    create_tableau_component_translator,
)
from dagster_tableau.resources import (
    BaseTableauWorkspace,
    TableauCloudWorkspace,
    TableauServerWorkspace,
)
from dagster_tableau.translator import (
    DagsterTableauTranslator,
    TableauDataSourceMetadataSet,
    TableauTranslatorData,
    TableauWorkspaceData,
)


class TableauCloudWorkspaceArgs(Model, Resolvable):
    """Arguments for configuring a Tableau Cloud workspace connection."""

    type: Literal["cloud"] = Field(
        default="cloud",
        description="Type of Tableau workspace. Must be 'cloud' for Tableau Cloud.",
    )
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


class TableauServerWorkspaceArgs(Model, Resolvable):
    """Arguments for configuring a Tableau Server workspace connection."""

    type: Literal["server"] = Field(
        ...,
        description="Type of Tableau workspace. Must be 'server' for Tableau Server.",
    )
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
    server_name: str = Field(
        ...,
        description="Tableau server name (e.g. 'tableau.example.com').",
    )


def _resolve_tableau_workspace(
    context: ResolutionContext, model: BaseModel
) -> BaseTableauWorkspace:
    """Resolves TableauCloudWorkspaceArgs or TableauServerWorkspaceArgs into the appropriate workspace resource."""
    # First, check which type we're dealing with
    workspace_type = (
        model.get("type", "cloud") if isinstance(model, dict) else getattr(model, "type", "cloud")
    )

    if workspace_type == "cloud":
        resolved = resolve_fields(
            model=model, resolved_cls=TableauCloudWorkspaceArgs, context=context
        )
        return TableauCloudWorkspace(
            connected_app_client_id=resolved["connected_app_client_id"],
            connected_app_secret_id=resolved["connected_app_secret_id"],
            connected_app_secret_value=resolved["connected_app_secret_value"],
            username=resolved["username"],
            site_name=resolved["site_name"],
            pod_name=resolved["pod_name"],
        )
    else:
        resolved = resolve_fields(
            model=model, resolved_cls=TableauServerWorkspaceArgs, context=context
        )
        return TableauServerWorkspace(
            connected_app_client_id=resolved["connected_app_client_id"],
            connected_app_secret_id=resolved["connected_app_secret_id"],
            connected_app_secret_value=resolved["connected_app_secret_value"],
            username=resolved["username"],
            site_name=resolved["site_name"],
            server_name=resolved["server_name"],
        )


@beta
@public
@dataclass
class TableauComponent(StateBackedComponent, Resolvable):
    """Pulls in the contents of a Tableau workspace into Dagster assets.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_tableau.TableauComponent
            attributes:
              workspace:
                type: cloud
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
            model_field_type=Union[
                TableauCloudWorkspaceArgs.model(), TableauServerWorkspaceArgs.model()
            ],
            description="Configuration for connecting to the Tableau workspace. Use 'type: cloud' for Tableau Cloud or 'type: server' for Tableau Server.",
            examples=[
                {
                    "type": "cloud",
                    "connected_app_client_id": "{{ env.TABLEAU_CLIENT_ID }}",
                    "connected_app_secret_id": "{{ env.TABLEAU_SECRET_ID }}",
                    "connected_app_secret_value": "{{ env.TABLEAU_SECRET_VALUE }}",
                    "username": "{{ env.TABLEAU_USERNAME }}",
                    "site_name": "my_site",
                    "pod_name": "10ax",
                },
                {
                    "type": "server",
                    "connected_app_client_id": "{{ env.TABLEAU_CLIENT_ID }}",
                    "connected_app_secret_id": "{{ env.TABLEAU_SECRET_ID }}",
                    "connected_app_secret_value": "{{ env.TABLEAU_SECRET_VALUE }}",
                    "username": "{{ env.TABLEAU_USERNAME }}",
                    "site_name": "my_site",
                    "server_name": "tableau.example.com",
                },
            ],
        ),
    ]

    # Takes a list of workbook names or ids to enable refresh for, or True to enable for all embedded datasources
    enable_embedded_datasource_refresh: Union[bool, list[str]] = False
    # Takes a list of published datasource names or id's to enable refresh for, or True to enable for all published datasources
    enable_published_datasource_refresh: Union[bool, list[str]] = False

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
        translator_cls = create_tableau_component_translator(TableauComponent)
        return translator_cls(self)

    @cached_property
    def _base_translator(self) -> DagsterTableauTranslator:
        return DagsterTableauTranslator()

    @public
    def get_asset_spec(self, data: TableauTranslatorData) -> dg.AssetSpec:
        """Generates an AssetSpec for a given Tableau content item.

        This method can be overridden in a subclass to customize how Tableau content
        (workbooks, dashboards, sheets, data sources) are converted to Dagster asset specs.
        By default, it delegates to the configured DagsterTableauTranslator.

        Args:
            data: The TableauTranslatorData containing information about the Tableau content
                item and workspace

        Returns:
            An AssetSpec that represents the Tableau content as a Dagster asset

        Example:
            Override this method to add custom metadata based on content properties:

            .. code-block:: python

                from dagster_tableau import TableauComponent
                from dagster import AssetSpec

                class CustomTableauComponent(TableauComponent):
                    def get_asset_spec(self, data):
                        base_spec = super().get_asset_spec(data)
                        return base_spec.replace_attributes(
                            metadata={
                                **base_spec.metadata,
                                "tableau_type": data.content_data.content_type,
                                "project": data.content_data.properties.get("project", {}).get("name")
                            }
                        )
        """
        return self._base_translator.get_asset_spec(data)

    def _load_asset_specs(self, state: TableauWorkspaceData) -> list[dg.AssetSpec]:
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

    def execute_embedded_data_sources(
        self, context: dg.AssetExecutionContext, workspace: BaseTableauWorkspace, workbook_id: str
    ):
        """Executes a refresh for embedded data sources within a Tableau workbook.

        This method can be overridden in a subclass to customize the refresh execution behavior,
        such as adding custom logging or handling refresh results differently.

        Args:
            context: The asset execution context provided by Dagster
            workspace: The BaseTableauWorkspace used to trigger and monitor refreshes
            workbook_id: The ID of the Tableau workbook containing the embedded data sources

        Yields:
            AssetMaterialization events for each embedded data source in the workbook

        Example:
            Override this method to add custom logging during refresh execution:

            .. code-block:: python

                from dagster_tableau import TableauComponent
                import dagster as dg

                class CustomTableauComponent(TableauComponent):
                    def execute_embedded_data_sources(self, context, workspace, workbook_id):
                        context.log.info(f"Starting refresh for workbook {workbook_id}")
                        result = yield from super().execute_embedded_data_sources(context, workspace, workbook_id)
                        context.log.info("Workbook refresh completed successfully")
                        return result
        """
        with workspace.get_client() as client:
            client.refresh_and_poll_workbook(workbook_id)
            for asset_key in context.selected_asset_keys:
                yield dg.AssetMaterialization(
                    asset_key=asset_key,
                )

    def execute_published_data_sources(
        self,
        context: dg.AssetExecutionContext,
        workspace: BaseTableauWorkspace,
        workspace_data: TableauWorkspaceData,
    ):
        """Executes a refresh for published data sources in the Tableau workspace.

        This method can be overridden in a subclass to customize the refresh execution behavior,
        such as adding custom logging or handling refresh results differently.

        Args:
            context: The asset execution context provided by Dagster. Only the assets that are in this context should be refreshed.
            workspace: The BaseTableauWorkspace used to trigger and monitor refreshes
            workspace_data: The TableauWorkspaceData containing information about all workspace content

        Yields:
            AssetMaterialization events for each published data source that was refreshed

        Example:
            Override this method to add custom logging during refresh execution:

            .. code-block:: python

                from dagster_tableau import TableauComponent
                import dagster as dg

                class CustomTableauComponent(TableauComponent):
                    def execute_published_data_sources(self, context, workspace, workspace_data):
                        context.log.info(f"Starting refresh for {len(context.selected_asset_keys)} published data sources")
                        result = yield from super().execute_published_data_sources(context, workspace, workspace_data)
                        context.log.info("Published data source refreshes completed successfully")
                        return result
        """
        specs_by_data_source_id = {
            k: self.get_asset_spec(
                TableauTranslatorData(content_data=v, workspace_data=workspace_data)
            )
            for k, v in workspace_data.data_sources_by_id.items()
        }
        specs_by_data_source_id = {  # Filter to only selected asset keys
            k: v for k, v in specs_by_data_source_id.items() if v.key in context.selected_asset_keys
        }

        with workspace.get_client() as client:
            for datasource_id in client.refresh_and_poll_data_sources(
                list(specs_by_data_source_id.keys())
            ):
                yield dg.AssetMaterialization(asset_key=specs_by_data_source_id[datasource_id].key)

    def build_refreshable_embedded_data_sources_asset_definition(
        self, workbook_id: str, specs: list[dg.AssetSpec]
    ) -> dg.AssetsDefinition:
        @dg.multi_asset(specs=specs, can_subset=False, name=clean_name_lower(workbook_id))
        def asset_fn(context: dg.AssetExecutionContext):
            yield from self.execute_embedded_data_sources(context, self.workspace, workbook_id)

        return asset_fn

    def build_refreshable_published_data_sources_asset_definition(
        self, specs: list[dg.AssetSpec], workspace_data: TableauWorkspaceData
    ) -> dg.AssetsDefinition:
        @dg.multi_asset(
            specs=specs,
            can_subset=True,
            name=clean_name_lower(
                f"tableau_published_data_sources_{clean_name_lower(self.workspace.site_name)}"
            ),
        )
        def asset_fn(context: dg.AssetExecutionContext):
            yield from self.execute_published_data_sources(context, self.workspace, workspace_data)

        return asset_fn

    def is_refreshable_published_data_source(
        self, spec: dg.AssetSpec, workspace_data: TableauWorkspaceData
    ) -> bool:
        if not self.enable_published_datasource_refresh:
            return False

        if ("published datasource" not in spec.kinds) or ("extract" not in spec.kinds):
            return False

        metadataset = TableauDataSourceMetadataSet.extract(spec.metadata)
        data_source_id = check.not_none(metadataset.id)
        data_source_name = workspace_data.data_sources_by_id[data_source_id].properties["name"]

        if (
            isinstance(self.enable_published_datasource_refresh, list)
            and (data_source_id not in self.enable_published_datasource_refresh)
            and (data_source_name not in self.enable_published_datasource_refresh)
        ):
            return False
        return True

    def is_refreshable_embedded_data_source(
        self, spec: dg.AssetSpec, workspace_data: TableauWorkspaceData
    ) -> bool:
        if not self.enable_embedded_datasource_refresh:
            return False

        if ("embedded datasource" not in spec.kinds) or ("extract" not in spec.kinds):
            return False

        metadataset = TableauDataSourceMetadataSet.extract(spec.metadata)
        workbook_id = check.not_none(metadataset.workbook_id)

        workbook_name = workspace_data.workbooks_by_id[workbook_id].properties["name"]

        if (
            isinstance(self.enable_embedded_datasource_refresh, list)
            and (workbook_id not in self.enable_embedded_datasource_refresh)
            and (workbook_name not in self.enable_embedded_datasource_refresh)
        ):
            return False
        return True

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        """Builds Dagster definitions from the cached Tableau workspace state."""
        if state_path is None:
            return dg.Definitions()

        # Deserialize workspace data
        workspace_data = dg.deserialize_value(state_path.read_text(), TableauWorkspaceData)

        specs = self._load_asset_specs(workspace_data)

        non_refreshable_specs = [
            spec
            for spec in specs
            if (not self.is_refreshable_embedded_data_source(spec, workspace_data))
            and (not self.is_refreshable_published_data_source(spec, workspace_data))
        ]
        refreshable_embedded_data_source_specs = [
            spec for spec in specs if self.is_refreshable_embedded_data_source(spec, workspace_data)
        ]
        refreshable_published_data_source_specs = [
            spec
            for spec in specs
            if self.is_refreshable_published_data_source(spec, workspace_data)
        ]

        refreshable_specs_by_workbook_id = defaultdict(list)
        for spec in refreshable_embedded_data_source_specs:
            workbook_id = TableauDataSourceMetadataSet.extract(spec.metadata).workbook_id
            refreshable_specs_by_workbook_id[workbook_id].append(spec)

        assets_defs = []

        for workbook_id, specs in refreshable_specs_by_workbook_id.items():
            assets_defs.append(
                self.build_refreshable_embedded_data_sources_asset_definition(workbook_id, specs)
            )

        assets_defs.append(
            self.build_refreshable_published_data_sources_asset_definition(
                refreshable_published_data_source_specs, workspace_data
            )
        )

        return dg.Definitions(assets=non_refreshable_specs + assets_defs)
