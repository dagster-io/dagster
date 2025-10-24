from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Optional

import dagster as dg
from dagster._annotations import beta, public
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster.components import ComponentLoadContext, Model, Resolvable, Resolver
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster_shared.serdes.serdes import deserialize_value
from pydantic import Field

from dagster_looker.api.components.translation import (
    ResolvedMultilayerTranslationFn,
    create_looker_component_translator,
)
from dagster_looker.api.dagster_looker_api_translator import (
    DagsterLookerApiTranslator,
    LookerApiTranslatorStructureData,
    LookerInstanceData,
    LookerStructureData,
    LookerStructureType,
)
from dagster_looker.api.resource import LookerApiDefsLoader, LookerFilter, LookerResource


class LookerInstanceArgs(Model, Resolvable):
    """Arguments for configuring a Looker instance connection."""

    base_url: str = Field(
        ...,
        description="Base URL for your Looker instance, e.g. https://your-company.looker.com",
    )
    client_id: str = Field(..., description="A client ID with access to the Looker API.")
    client_secret: str = Field(..., description="A client secret with access to the Looker API.")


class LookerFilterArgs(Model, Resolvable):
    """Arguments for filtering which Looker content to load."""

    dashboard_folders: Optional[list[list[str]]] = Field(
        default=None,
        description=(
            "A list of folder paths to load dashboards from. Each folder path is a list of "
            "folder names, starting from the root folder. If not provided, all dashboards "
            "will be loaded."
        ),
    )
    only_fetch_explores_used_in_dashboards: bool = Field(
        default=False,
        description="If True, only load explores that are used in dashboards. If False, load all explores.",
    )


@beta
@public
@dataclass
class LookerComponent(StateBackedComponent, Resolvable):
    """Pulls in the contents of a Looker instance into Dagster assets.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_looker.LookerComponent
            attributes:
              looker_resource:
                base_url: https://your-company.looker.com
                client_id: "{{ env.LOOKER_CLIENT_ID }}"
                client_secret: "{{ env.LOOKER_CLIENT_SECRET }}"
              looker_filter:
                dashboard_folders:
                  - ["Shared"]
                only_fetch_explores_used_in_dashboards: true
    """

    looker_resource: Annotated[
        LookerResource,
        Resolver.default(
            model_field_type=LookerInstanceArgs.model(),
            description="Configuration for connecting to the Looker instance",
            examples=[
                {
                    "base_url": "https://your-company.looker.com",
                    "client_id": "{{ env.LOOKER_CLIENT_ID }}",
                    "client_secret": "{{ env.LOOKER_CLIENT_SECRET }}",
                }
            ],
        ),
    ]

    looker_filter: Annotated[
        Optional[LookerFilter],
        Resolver.default(
            model_field_type=LookerFilterArgs.model(),
            description="Filters for which Looker content to load",
            examples=[
                {
                    "dashboard_folders": [["Shared", "Team"]],
                    "only_fetch_explores_used_in_dashboards": True,
                }
            ],
        ),
    ] = None
    translation: Optional[ResolvedMultilayerTranslationFn] = None
    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.legacy_code_server_snapshots
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.looker_resource.base_url}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    @cached_property
    def translator(self) -> DagsterLookerApiTranslator:
        translator_cls = create_looker_component_translator(LookerComponent)
        return translator_cls(self)

    @cached_property
    def _base_translator(self) -> DagsterLookerApiTranslator:
        return DagsterLookerApiTranslator()

    def get_asset_spec(self, looker_structure: LookerApiTranslatorStructureData) -> AssetSpec:
        return self._base_translator.get_asset_spec(looker_structure)

    def _load_asset_specs(self, state: LookerInstanceData) -> list[AssetSpec]:
        explores = [
            self.translator.get_asset_spec(
                LookerApiTranslatorStructureData(
                    structure_data=LookerStructureData(
                        structure_type=LookerStructureType.EXPLORE,
                        data=lookml_explore,
                        base_url=self.looker_resource.base_url,
                    ),
                    instance_data=state,
                )
            )
            for lookml_explore in state.explores_by_id.values()
        ]

        dashboards = [
            self.translator.get_asset_spec(
                LookerApiTranslatorStructureData(
                    structure_data=LookerStructureData(
                        structure_type=LookerStructureType.DASHBOARD,
                        data=looker_dashboard,
                        base_url=self.looker_resource.base_url,
                    ),
                    instance_data=state,
                )
            )
            for looker_dashboard in state.dashboards_by_id.values()
        ]

        return [*explores, *dashboards]

    def write_state_to_path(self, state_path: Path) -> None:
        """Fetches Looker instance data and writes it to the state path."""
        sdk = self.looker_resource.get_sdk()

        # Create a loader to fetch the instance data
        loader = LookerApiDefsLoader(
            looker_resource=self.looker_resource,
            translator=self._base_translator,
            looker_filter=self.looker_filter or LookerFilter(),
        )

        # Fetch the instance data
        instance_data = loader.fetch_looker_instance_data()

        # Convert to state format and serialize
        state = instance_data.to_state(sdk)
        state_path.write_text(dg.serialize_value(state))

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        """Builds Dagster definitions from the cached Looker instance state."""
        if state_path is None:
            return dg.Definitions()

        sdk = self.looker_resource.get_sdk()

        # Deserialize and convert from state format
        state = deserialize_value(state_path.read_text(), dict)
        instance_data = LookerInstanceData.from_state(sdk, state)

        specs = self._load_asset_specs(instance_data)

        return dg.Definitions(assets=specs)
