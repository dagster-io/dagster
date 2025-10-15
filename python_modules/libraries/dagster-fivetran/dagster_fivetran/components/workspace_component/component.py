from collections import defaultdict
from collections.abc import Iterable, Sequence
from functools import cached_property
from pathlib import Path
from typing import Annotated, Callable, Optional, Union

import dagster as dg
import pydantic
from dagster._annotations import public
from dagster._utils.names import clean_name
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.base import resolve_fields
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dagster_shared import check
from dagster_shared.serdes.serdes import deserialize_value

from dagster_fivetran.components.workspace_component.scaffolder import (
    FivetranAccountComponentScaffolder,
)
from dagster_fivetran.resources import FivetranWorkspace
from dagster_fivetran.translator import (
    DagsterFivetranTranslator,
    FivetranConnector,
    FivetranConnectorTableProps,
    FivetranMetadataSet,
    FivetranWorkspaceData,
)
from dagster_fivetran.utils import DAGSTER_FIVETRAN_TRANSLATOR_METADATA_KEY


class FivetranWorkspaceModel(pydantic.BaseModel):
    account_id: str = pydantic.Field(..., description="The Fivetran account ID.")
    api_key: str = pydantic.Field(
        ..., description="API key used to authenticate to a Fivetran instance."
    )
    api_secret: str = pydantic.Field(
        ..., description="API secret used to authenticate to a Fivetran instance."
    )


class FivetranConnectorSelectorByName(pydantic.BaseModel):
    by_name: Sequence[str] = pydantic.Field(
        ...,
        description="A list of connector names to include in the collection.",
    )


class FivetranConnectorSelectorById(pydantic.BaseModel):
    by_id: Sequence[str] = pydantic.Field(
        ...,
        description="A list of connector IDs to include in the collection.",
    )


def resolve_connector_selector(
    context: dg.ResolutionContext, model
) -> Optional[Callable[[FivetranConnector], bool]]:
    if isinstance(model, str):
        model = context.resolve_value(model)

    if isinstance(model, FivetranConnectorSelectorByName):
        return lambda connector: connector.name in model.by_name
    elif isinstance(model, FivetranConnectorSelectorById):
        return lambda connector: connector.id in model.by_id
    else:
        check.failed(f"Unknown connector target type: {type(model)}")


@public
@dg.scaffold_with(FivetranAccountComponentScaffolder)
class FivetranAccountComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    """Loads Fivetran connectors from a given Fivetran instance as Dagster assets.
    Materializing these assets will trigger a sync of the Fivetran connector, enabling
    you to schedule Fivetran syncs using Dagster.
    """

    workspace: Annotated[
        FivetranWorkspace,
        dg.Resolver(
            lambda context, model: FivetranWorkspace(
                **resolve_fields(model, FivetranWorkspace, context)
            )
        ),
    ]
    connector_selector: Annotated[
        Optional[Callable[[FivetranConnector], bool]],
        dg.Resolver(
            resolve_connector_selector,
            model_field_type=Union[
                str, FivetranConnectorSelectorByName, FivetranConnectorSelectorById
            ],
        ),
    ] = None
    translation: Optional[
        Annotated[
            TranslationFn[FivetranConnectorTableProps],
            TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"props": data}),
        ]
    ] = pydantic.Field(
        default=None,
        description="Function used to translate Fivetran connector table properties into Dagster asset specs.",
    )
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.legacy_code_server_snapshots()

    @cached_property
    def workspace_resource(self) -> FivetranWorkspace:
        return self.workspace

    @cached_property
    def translator(self) -> DagsterFivetranTranslator:
        return FivetranComponentTranslator(self)

    @cached_property
    def _base_translator(self) -> DagsterFivetranTranslator:
        return DagsterFivetranTranslator()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.workspace_resource.account_id}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    def get_asset_spec(self, props: FivetranConnectorTableProps) -> dg.AssetSpec:
        return self._base_translator.get_asset_spec(props)

    def execute(
        self, context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
    ) -> Iterable[Union[dg.AssetMaterialization, dg.MaterializeResult]]:
        yield from fivetran.sync_and_poll(context=context)

    def _load_asset_specs(self, state: FivetranWorkspaceData) -> Sequence[dg.AssetSpec]:
        connector_selector_fn = self.connector_selector or (lambda connector: bool(connector))
        return [
            self.translator.get_asset_spec(props).merge_attributes(
                metadata={DAGSTER_FIVETRAN_TRANSLATOR_METADATA_KEY: self.translator}
            )
            for props in state.to_workspace_data_selection(
                connector_selector_fn=connector_selector_fn
            ).to_fivetran_connector_table_props_data()
        ]

    def _get_fivetran_assets_def(
        self, connector_name: str, specs: Sequence[dg.AssetSpec]
    ) -> dg.AssetsDefinition:
        @dg.multi_asset(name=f"fivetran_{clean_name(connector_name)}", can_subset=True, specs=specs)
        def _asset(context: dg.AssetExecutionContext):
            yield from self.execute(context=context, fivetran=self.workspace)

        return _asset

    async def write_state_to_path(self, state_path: Path) -> None:
        state = self.workspace_resource.fetch_fivetran_workspace_data()
        state_path.write_text(dg.serialize_value(state))

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()
        state = deserialize_value(state_path.read_text(), FivetranWorkspaceData)

        # group specs by their connector names
        specs_by_connector_name = defaultdict(list)
        for spec in self._load_asset_specs(state):
            connector_name = check.not_none(
                FivetranMetadataSet.extract(spec.metadata).connector_name
            )
            specs_by_connector_name[connector_name].append(spec)

        # create one assets definition per connector
        assets = [
            self._get_fivetran_assets_def(connector_name, specs)
            for connector_name, specs in specs_by_connector_name.items()
        ]
        return dg.Definitions(assets=assets)


class FivetranComponentTranslator(
    create_component_translator_cls(FivetranAccountComponent, DagsterFivetranTranslator),
    ComponentTranslator[FivetranAccountComponent],
):
    def __init__(self, component: "FivetranAccountComponent"):
        self._component = component

    def get_asset_spec(self, props: FivetranConnectorTableProps) -> dg.AssetSpec:
        base_asset_spec = super().get_asset_spec(props)
        if self.component.translation is None:
            return base_asset_spec
        else:
            return self.component.translation(base_asset_spec, props)
