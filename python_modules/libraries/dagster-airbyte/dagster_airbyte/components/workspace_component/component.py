from collections import defaultdict
from collections.abc import Iterable, Sequence
from functools import cached_property
from pathlib import Path
from typing import Annotated, Callable, Optional, Union

import dagster as dg
import pydantic
from dagster._annotations import superseded
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

from dagster_airbyte.components.workspace_component.scaffolder import (
    AirbyteWorkspaceComponentScaffolder,
)
from dagster_airbyte.resources import AirbyteCloudWorkspace, AirbyteWorkspace, BaseAirbyteWorkspace
from dagster_airbyte.translator import (
    AirbyteConnection,
    AirbyteConnectionTableProps,
    AirbyteMetadataSet,
    AirbyteWorkspaceData,
    DagsterAirbyteTranslator,
)
from dagster_airbyte.utils import DAGSTER_AIRBYTE_TRANSLATOR_METADATA_KEY


class BaseAirbyteWorkspaceModel(dg.Model, dg.Resolvable):
    request_max_retries: Annotated[
        int,
        pydantic.Field(
            default=3,
            description=(
                "The maximum number of times requests to the Airbyte API should be retried "
                "before failing."
            ),
        ),
    ]
    request_retry_delay: Annotated[
        float,
        pydantic.Field(
            default=0.25,
            description="Time (in seconds) to wait between each request retry.",
        ),
    ]
    request_timeout: Annotated[
        int,
        pydantic.Field(
            default=15,
            description="Time (in seconds) after which the requests to Airbyte are declared timed out.",
        ),
    ]


class AirbyteWorkspaceModel(BaseAirbyteWorkspaceModel):
    rest_api_base_url: Annotated[
        str,
        pydantic.Field(
            ...,
            description=(
                "The base URL for the Airbyte REST API. "
                "For Airbyte Cloud, leave this as the default. "
                "For self-managed Airbyte, this is usually <your Airbyte host>/api/public/v1."
            ),
            examples=[
                "http://localhost:8000/api/public/v1",
                "https://my-airbyte-server.com/api/public/v1",
                "http://airbyte-airbyte-server-svc.airbyte.svc.cluster.local:8001/api/public/v1",
            ],
        ),
    ]
    configuration_api_base_url: Annotated[
        str,
        pydantic.Field(
            ...,
            description=(
                "The base URL for the Airbyte Configuration API. "
                "For Airbyte Cloud, leave this as the default. "
                "For self-managed Airbyte, this is usually <your Airbyte host>/api/v1."
            ),
            examples=[
                "http://localhost:8000/api/v1",
                "https://my-airbyte-server.com/api/v1",
                "http://airbyte-airbyte-server-svc.airbyte.svc.cluster.local:8001/api/v1",
            ],
        ),
    ]
    workspace_id: Annotated[str, pydantic.Field(..., description="The Airbyte workspace ID.")]
    client_id: Annotated[
        Optional[str],
        pydantic.Field(None, description="Client ID used to authenticate to Airbyte."),
    ]
    client_secret: Annotated[
        Optional[str],
        pydantic.Field(None, description="Client secret used to authenticate to Airbyte."),
    ]
    username: Annotated[
        Optional[str],
        pydantic.Field(
            None,
            description="Username used to authenticate to Airbyte. Used for self-managed Airbyte with basic auth.",
        ),
    ]
    password: Annotated[
        Optional[str],
        pydantic.Field(
            None,
            description="Password used to authenticate to Airbyte. Used for self-managed Airbyte with basic auth.",
        ),
    ]


class AirbyteCloudWorkspaceModel(BaseAirbyteWorkspaceModel):
    workspace_id: Annotated[str, pydantic.Field(..., description="The Airbyte workspace ID.")]
    client_id: Annotated[
        Optional[str],
        pydantic.Field(..., description="Client ID used to authenticate to Airbyte."),
    ]
    client_secret: Annotated[
        Optional[str],
        pydantic.Field(..., description="Client secret used to authenticate to Airbyte."),
    ]


class AirbyteConnectionSelectorByName(dg.Model):
    by_name: Annotated[
        Sequence[str],
        pydantic.Field(..., description="A list of connection names to include in the collection."),
    ]


class AirbyteConnectionSelectorById(dg.Model):
    by_id: Annotated[
        Sequence[str],
        pydantic.Field(..., description="A list of connection IDs to include in the collection."),
    ]


def resolve_connection_selector(
    context: dg.ResolutionContext, model
) -> Optional[Callable[[AirbyteConnection], bool]]:
    if isinstance(model, str):
        model = context.resolve_value(model)

    if isinstance(model, AirbyteConnectionSelectorByName):
        return lambda connection: connection.name in model.by_name
    elif isinstance(model, AirbyteConnectionSelectorById):
        return lambda connection: connection.id in model.by_id
    else:
        check.failed(f"Unknown connection target type: {type(model)}")


def resolve_airbyte_workspace_type(context: dg.ResolutionContext, model):
    if isinstance(model, AirbyteWorkspaceModel):
        return AirbyteWorkspace(**resolve_fields(model, AirbyteWorkspaceModel, context))
    elif isinstance(model, AirbyteCloudWorkspaceModel):
        return AirbyteCloudWorkspace(**resolve_fields(model, AirbyteCloudWorkspaceModel, context))
    else:
        check.failed(f"Unknown Airbyte workspace type: {type(model)}")


@dg.scaffold_with(AirbyteWorkspaceComponentScaffolder)
class AirbyteWorkspaceComponent(StateBackedComponent, dg.Model, dg.Resolvable):
    """Loads Airbyte connections from a given Airbyte workspace as Dagster assets.
    Materializing these assets will trigger a sync of the Airbyte connection, enabling
    you to schedule Airbyte syncs using Dagster.
    """

    workspace: Annotated[
        Union[AirbyteWorkspace, AirbyteCloudWorkspace],
        dg.Resolver(
            resolve_airbyte_workspace_type,
            model_field_type=Union[AirbyteWorkspaceModel, AirbyteCloudWorkspaceModel],
        ),
    ]
    connection_selector: Annotated[
        Optional[Callable[[AirbyteConnection], bool]],
        dg.Resolver(
            resolve_connection_selector,
            model_field_type=Union[
                str, AirbyteConnectionSelectorByName, AirbyteConnectionSelectorById
            ],
            description="Function used to select Airbyte connections to pull into Dagster.",
        ),
    ] = None
    translation: Optional[
        Annotated[
            TranslationFn[AirbyteConnectionTableProps],
            TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"props": data}),
        ]
    ] = pydantic.Field(
        default=None,
        description="Function used to translate Airbyte connection table properties into Dagster asset specs.",
    )
    defs_state: ResolvedDefsStateConfig = DefsStateConfigArgs.legacy_code_server_snapshots()

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.workspace.workspace_id}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    @cached_property
    def translator(self) -> DagsterAirbyteTranslator:
        return AirbyteComponentTranslator(self)

    @cached_property
    def _base_translator(self) -> DagsterAirbyteTranslator:
        return DagsterAirbyteTranslator()

    def get_asset_spec(self, props: AirbyteConnectionTableProps) -> dg.AssetSpec:
        return self._base_translator.get_asset_spec(props)

    def execute(
        self, context: dg.AssetExecutionContext, airbyte: BaseAirbyteWorkspace
    ) -> Iterable[Union[dg.AssetMaterialization, dg.MaterializeResult]]:
        yield from airbyte.sync_and_poll(context=context)

    def _load_asset_specs(self, state: AirbyteWorkspaceData) -> Sequence[dg.AssetSpec]:
        connection_selector_fn = self.connection_selector or (lambda connection: True)
        return [
            self.translator.get_asset_spec(props).merge_attributes(
                metadata={DAGSTER_AIRBYTE_TRANSLATOR_METADATA_KEY: self.translator}
            )
            for props in state.to_airbyte_connection_table_props_data()
            if connection_selector_fn(state.connections_by_id[props.connection_id])
        ]

    def _get_airbyte_assets_def(
        self, connection_name: str, specs: Sequence[dg.AssetSpec]
    ) -> dg.AssetsDefinition:
        @dg.multi_asset(
            name=f"airbyte_{clean_name(connection_name)}",
            can_subset=True,
            specs=specs,
        )
        def _asset(context: dg.AssetExecutionContext):
            yield from self.execute(context=context, airbyte=self.workspace)

        return _asset

    async def write_state_to_path(self, state_path: Path) -> None:
        state = self.workspace.fetch_airbyte_workspace_data()
        state_path.write_text(dg.serialize_value(state))

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()
        state = deserialize_value(state_path.read_text(), AirbyteWorkspaceData)

        # group specs by their connector names
        specs_by_connection_name = defaultdict(list)
        for spec in self._load_asset_specs(state):
            connection_name = check.not_none(
                AirbyteMetadataSet.extract(spec.metadata).connection_name
            )
            specs_by_connection_name[connection_name].append(spec)

        # create one assets definition per connection
        assets = [
            self._get_airbyte_assets_def(connection_name, specs)
            for connection_name, specs in specs_by_connection_name.items()
        ]
        return dg.Definitions(assets=assets)


# Subclassing to create the alias to be able to use the superseded decorator.
@superseded(additional_warn_text="Superseded. Use AirbyteWorkspaceComponent instead.")
class AirbyteCloudWorkspaceComponent(AirbyteWorkspaceComponent): ...


class AirbyteComponentTranslator(
    create_component_translator_cls(AirbyteWorkspaceComponent, DagsterAirbyteTranslator),
    ComponentTranslator[AirbyteWorkspaceComponent],
):
    def __init__(self, component: AirbyteWorkspaceComponent):
        self._component = component

    def get_asset_spec(self, props: AirbyteConnectionTableProps) -> dg.AssetSpec:
        base_asset_spec = super().get_asset_spec(props)
        if self.component.translation is None:
            return base_asset_spec
        else:
            return self.component.translation(base_asset_spec, props)
