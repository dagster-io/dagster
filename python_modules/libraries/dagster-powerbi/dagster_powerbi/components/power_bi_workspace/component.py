from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Optional, TypeAlias, Union

import dagster as dg
from dagster._annotations import public
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import ComponentLoadContext, Model, Resolvable, Resolver
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.base import resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetSpecKeyUpdateKwargs, AssetSpecUpdateKwargs
from dagster.components.utils import TranslatorResolvingInfo
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
from dagster_shared.record import record
from dagster_shared.serdes.serdes import deserialize_value
from pydantic import BaseModel

from dagster_powerbi.resource import PowerBIServicePrincipal, PowerBIToken, PowerBIWorkspace
from dagster_powerbi.translator import (
    DagsterPowerBITranslator,
    PowerBIContentType,
    PowerBIMetadataSet,
    PowerBITagSet,
    PowerBITranslatorData,
    PowerBIWorkspaceData,
)


class PowerBITokenModel(Model):
    token: str


class PowerBIServicePrincipalModel(Model):
    client_id: str
    client_secret: str
    tenant_id: str


PowerBICredentialsModel: TypeAlias = Union[PowerBITokenModel, PowerBIServicePrincipalModel]


def resolve_powerbi_credentials(
    context: ResolutionContext,
    credentials,
) -> Union[PowerBIToken, PowerBIServicePrincipal]:
    if hasattr(credentials, "token"):
        return PowerBIToken(api_token=context.resolve_value(credentials.token, as_type=str))
    return PowerBIServicePrincipal(
        client_id=context.resolve_value(credentials.client_id, as_type=str),
        client_secret=context.resolve_value(credentials.client_secret, as_type=str),
        tenant_id=context.resolve_value(credentials.tenant_id, as_type=str),
    )


PowerBITranslationFn: TypeAlias = TranslationFn[PowerBITranslatorData]

ResolvedTargetedPowerBITranslationFn = Annotated[
    PowerBITranslationFn,
    TranslationFnResolver[PowerBITranslatorData](lambda data: {"data": data}),
]

ResolvedTargetedKeyOnlyPowerBITranslationFn = Annotated[
    PowerBITranslationFn,
    TranslationFnResolver[PowerBITranslatorData](
        lambda data: {"data": data}, model_field_type=AssetSpecKeyUpdateKwargs.model()
    ),
]


@record
class PowerBIAssetArgs(AssetSpecUpdateKwargs, Resolvable):
    for_dashboard: Optional[ResolvedTargetedPowerBITranslationFn] = None
    for_report: Optional[ResolvedTargetedPowerBITranslationFn] = None
    for_semantic_model: Optional[ResolvedTargetedPowerBITranslationFn] = None
    # data sources are external assets, so only the key can be user-customized
    for_data_source: Optional[ResolvedTargetedKeyOnlyPowerBITranslationFn] = None


def resolve_multilayer_translation(context: ResolutionContext, model):
    """The PowerBI translation schema supports defining global transforms
    as well as per-content-type transforms. This resolver composes the
    per-content-type transforms with the global transforms.
    """
    info = TranslatorResolvingInfo(
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )

    def _translation_fn(base_asset_spec: AssetSpec, data: PowerBITranslatorData):
        processed_spec = info.get_asset_spec(
            base_asset_spec,
            {
                "data": data,
                "spec": base_asset_spec,
            },
        )

        nested_translation_fns = resolve_fields(
            model=model,
            resolved_cls=PowerBIAssetArgs,
            context=context.with_scope(
                **{
                    "data": data,
                    "spec": processed_spec,
                }
            ),
        )
        for_semantic_model = nested_translation_fns.get("for_semantic_model")
        for_dashboard = nested_translation_fns.get("for_dashboard")
        for_report = nested_translation_fns.get("for_report")
        for_data_source = nested_translation_fns.get("for_data_source")

        if data.content_type == PowerBIContentType.SEMANTIC_MODEL and for_semantic_model:
            return for_semantic_model(processed_spec, data)
        if data.content_type == PowerBIContentType.DASHBOARD and for_dashboard:
            return for_dashboard(processed_spec, data)
        if data.content_type == PowerBIContentType.REPORT and for_report:
            return for_report(processed_spec, data)
        if data.content_type == PowerBIContentType.DATA_SOURCE and for_data_source:
            return for_data_source(processed_spec, data)

        return processed_spec

    return _translation_fn


ResolvedMultilayerTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_multilayer_translation,
        model_field_type=Union[str, PowerBIAssetArgs.model()],
    ),
]


@dataclass
class PowerBIWorkspaceModel(Resolvable):
    credentials: Annotated[
        Union[PowerBIToken, PowerBIServicePrincipal],
        Resolver(
            resolve_powerbi_credentials,
            model_field_type=PowerBICredentialsModel,
        ),
    ]
    workspace_id: str


def _resolve_powerbi_workspace(context: ResolutionContext, model: BaseModel) -> PowerBIWorkspace:
    return PowerBIWorkspace(
        **resolve_fields(model=model, resolved_cls=PowerBIWorkspaceModel, context=context)
    )


@public
@dataclass
class PowerBIWorkspaceComponent(StateBackedComponent, Resolvable):
    """Pulls in the contents of a PowerBI workspace into Dagster assets.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_powerbi.PowerBIWorkspaceComponent
            attributes:
              workspace:
                credentials:
                  client_id: "{{ env.POWERBI_CLIENT_ID }}"
                  client_secret: "{{ env.POWERBI_CLIENT_SECRET }}"
                  tenant_id: "{{ env.POWERBI_TENANT_ID }}"
                workspace_id: your-workspace-id
              enable_semantic_model_refresh: true
    """

    workspace: Annotated[
        Any,
        Resolver(
            _resolve_powerbi_workspace,
            model_field_name="workspace",
            model_field_type=PowerBIWorkspaceModel.model(),
        ),
    ]
    use_workspace_scan: bool = True
    # Takes a list of semantic model names to enable refresh for, or True to enable for all semantic models
    enable_semantic_model_refresh: Union[bool, list[str]] = False
    translation: Optional[ResolvedMultilayerTranslationFn] = None
    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.legacy_code_server_snapshots
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.workspace.workspace_id}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    @cached_property
    def translator(self) -> DagsterPowerBITranslator:
        return PowerBIComponentTranslator(self)

    @cached_property
    def _base_translator(self) -> DagsterPowerBITranslator:
        return DagsterPowerBITranslator()

    @public
    def get_asset_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        """Generates an AssetSpec for a given Power BI content item.

        This method can be overridden in a subclass to customize how Power BI content
        (reports, dashboards, semantic models, datasets) are converted to Dagster asset specs.
        By default, it delegates to the configured DagsterPowerBITranslator.

        Args:
            data: The PowerBITranslatorData containing information about the Power BI content
                item and workspace

        Returns:
            An AssetSpec that represents the Power BI content as a Dagster asset

        Example:
            Override this method to add custom metadata based on content properties:

            .. code-block:: python

                from dagster_powerbi import PowerBIWorkspaceComponent
                from dagster import AssetSpec

                class CustomPowerBIWorkspaceComponent(PowerBIWorkspaceComponent):
                    def get_asset_spec(self, data):
                        base_spec = super().get_asset_spec(data)
                        return base_spec.replace_attributes(
                            metadata={
                                **base_spec.metadata,
                                "workspace_name": data.workspace_data.properties.get("name"),
                                "content_type": data.content_type
                            }
                        )
        """
        return self._base_translator.get_asset_spec(data)

    @cached_property
    def workspace_resource(self) -> PowerBIWorkspace:
        return self.workspace

    def _should_spec_be_refreshable(self, spec: AssetSpec) -> bool:
        return spec.tags.get("dagster-powerbi/asset_type") == "semantic_model" and (
            self.enable_semantic_model_refresh is True
            or (
                isinstance(self.enable_semantic_model_refresh, list)
                and spec.metadata.get("dagster-powerbi/name") in self.enable_semantic_model_refresh
            )
        )

    def build_semantic_model_refresh_asset_definition(self, spec: AssetSpec) -> AssetsDefinition:
        """Builds an asset definition for refreshing a PowerBI semantic model, with
        this component's resource implicitly bound to the asset.
        """
        check.invariant(PowerBITagSet.extract(spec.tags).asset_type == "semantic_model")
        dataset_id = check.not_none(PowerBIMetadataSet.extract(spec.metadata).id)

        @multi_asset(
            specs=[spec],
            name="_".join(spec.key.path),
        )
        def asset_fn(context: AssetExecutionContext) -> None:
            self.workspace_resource.trigger_and_poll_refresh(dataset_id)

        return asset_fn

    def _load_asset_specs(self, state: PowerBIWorkspaceData) -> list[AssetSpec]:
        all_external_data = [
            *state.dashboards_by_id.values(),
            *state.reports_by_id.values(),
            *state.semantic_models_by_id.values(),
        ]
        return [
            self.translator.get_asset_spec(
                PowerBITranslatorData(content_data=content, workspace_data=state)
            )
            for content in all_external_data
        ]

    async def write_state_to_path(self, state_path: Path) -> None:
        state = self.workspace_resource.fetch_powerbi_workspace_data(
            use_workspace_scan=self.use_workspace_scan
        )
        state_path.write_text(dg.serialize_value(state))

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state = deserialize_value(state_path.read_text(), PowerBIWorkspaceData)
        specs = self._load_asset_specs(state)

        specs_with_refreshable_semantic_models = [
            self.build_semantic_model_refresh_asset_definition(spec)
            if self._should_spec_be_refreshable(spec)
            else spec
            for spec in specs
        ]
        return dg.Definitions(assets=specs_with_refreshable_semantic_models)


class PowerBIComponentTranslator(
    create_component_translator_cls(PowerBIWorkspaceComponent, DagsterPowerBITranslator),
    ComponentTranslator[PowerBIWorkspaceComponent],
):
    def __init__(self, component: PowerBIWorkspaceComponent):
        self._component = component

    def get_asset_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        base_asset_spec = super().get_asset_spec(data)
        if self.component.translation is None:
            return base_asset_spec
        else:
            return self.component.translation(base_asset_spec, data)
