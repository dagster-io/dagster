from dataclasses import dataclass
from functools import cached_property
from typing import Annotated, Callable, Optional, Union

import dagster as dg
from dagster._core.definitions.asset_spec import AssetSpec
from dagster.components import Component, ComponentLoadContext, Model, Resolvable, Resolver
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetAttributesModel
from dagster.components.utils import TranslatorResolvingInfo
from typing_extensions import TypeAlias

from dagster_powerbi.resource import (
    PowerBIServicePrincipal,
    PowerBIToken,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)
from dagster_powerbi.translator import DagsterPowerBITranslator, PowerBITranslatorData


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


TranslationFn: TypeAlias = Callable[[AssetSpec, PowerBITranslatorData], AssetSpec]

ResolvedTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_translation,
        model_field_type=Union[str, AssetAttributesModel],
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
    translation: Optional[ResolvedTranslationFn] = None

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
