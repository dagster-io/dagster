from dataclasses import dataclass
from functools import cached_property
from typing import Annotated, Callable, Optional, Union

import dagster as dg
from dagster._core.definitions.asset_spec import AssetSpec
from dagster.components import Component, ComponentLoadContext, Model, Resolvable, Resolver
from dagster.components.resolved.base import resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetAttributesModel, AssetSpecUpdateKwargs
from dagster.components.utils import TranslatorResolvingInfo
from dagster_shared.record import record
from typing_extensions import TypeAlias

from dagster_powerbi.resource import (
    PowerBIServicePrincipal,
    PowerBIToken,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)
from dagster_powerbi.translator import (
    DagsterPowerBITranslator,
    PowerBIContentType,
    PowerBITranslatorData,
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
        return PowerBIToken(api_token=credentials.token)
    return PowerBIServicePrincipal(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        tenant_id=credentials.tenant_id,
    )


TranslationFn: TypeAlias = Callable[[AssetSpec, PowerBITranslatorData], AssetSpec]


def resolve_translation(context: ResolutionContext, model):
    info = TranslatorResolvingInfo(
        "data",
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )
    return lambda base_asset_spec, data: info.get_asset_spec(
        base_asset_spec,
        {
            "data": data,
            "spec": base_asset_spec,
        },
    )


resolver = Resolver(
    resolve_translation,
    model_field_type=Union[str, AssetAttributesModel],
)
ResolvedTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    resolver,
]


@record
class PowerBIAssetArgs(AssetSpecUpdateKwargs, Resolvable):
    for_dashboard: Optional[ResolvedTranslationFn] = None
    for_report: Optional[ResolvedTranslationFn] = None
    for_semantic_model: Optional[ResolvedTranslationFn] = None


def resolve_multilayer_translation(context: ResolutionContext, model):
    """The PowerBI translation schema supports defining global transforms
    as well as per-content-type transforms. This resolver composes the
    per-content-type transforms with the global transforms.
    """
    info = TranslatorResolvingInfo(
        "data",
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

        if data.content_type == PowerBIContentType.SEMANTIC_MODEL and for_semantic_model:
            return for_semantic_model(processed_spec, data)
        if data.content_type == PowerBIContentType.DASHBOARD and for_dashboard:
            return for_dashboard(processed_spec, data)
        if data.content_type == PowerBIContentType.REPORT and for_report:
            return for_report(processed_spec, data)

        return processed_spec

    return _translation_fn


ResolvedMultilayerTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_multilayer_translation,
        model_field_type=Union[str, PowerBIAssetArgs.model()],
    ),
]


class ProxyDagsterPowerBITranslator(DagsterPowerBITranslator):
    def __init__(self, fn: TranslationFn):
        self._fn = fn

    def get_asset_spec(self, data: PowerBITranslatorData) -> AssetSpec:
        base_asset_spec = super().get_asset_spec(data)
        return self._fn(base_asset_spec, data)


@dataclass
class PowerBIWorkspaceComponent(Component, Resolvable):
    """Pulls in the contents of a PowerBI workspace into Dagster assets."""

    credentials: Annotated[
        Union[PowerBIToken, PowerBIServicePrincipal],
        Resolver(
            resolve_powerbi_credentials,
            model_field_type=PowerBICredentialsModel,
        ),
    ]
    workspace_id: str
    use_workspace_scan: bool = True
    translation: Optional[ResolvedMultilayerTranslationFn] = None

    @cached_property
    def translator(self) -> DagsterPowerBITranslator:
        if self.translation:
            return ProxyDagsterPowerBITranslator(self.translation)
        return DagsterPowerBITranslator()

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        specs = load_powerbi_asset_specs(
            workspace=PowerBIWorkspace(
                credentials=self.credentials, workspace_id=self.workspace_id
            ),
            dagster_powerbi_translator=self.translator,
            use_workspace_scan=self.use_workspace_scan,
        )
        return dg.Definitions(assets=specs)
