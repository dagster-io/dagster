from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Optional, TypeAlias, Union

import dagster as dg
from dagster._annotations import beta, public
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
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
from dagster_shared.record import record
from pydantic import Field

from dagster_sigma.resource import SigmaFilter, SigmaOrganization
from dagster_sigma.translator import (
    DagsterSigmaTranslator,
    SigmaDatasetTranslatorData,
    SigmaOrganizationData,
    SigmaWorkbookTranslatorData,
)


class SigmaOrganizationArgs(Model, Resolvable):
    """Arguments for configuring a Sigma organization connection."""

    base_url: str = Field(
        ...,
        description=(
            "Base URL for the cloud type of your Sigma organization, found under Administration -> Account -> Site settings. "
            "See https://help.sigmacomputing.com/reference/get-started-sigma-api#identify-your-api-request-url for more information."
        ),
    )
    client_id: str = Field(..., description="A client ID with access to the Sigma API.")
    client_secret: str = Field(..., description="A client secret with access to the Sigma API.")
    warn_on_lineage_fetch_error: bool = Field(
        default=False,
        description="Whether to warn rather than raise when lineage data cannot be fetched for an element.",
    )


def resolve_sigma_organization(context: ResolutionContext, model) -> SigmaOrganization:
    """Resolver function for SigmaOrganization that properly resolves templated strings."""
    args = SigmaOrganizationArgs.resolve_from_model(context, model)
    return SigmaOrganization(
        base_url=args.base_url,
        client_id=args.client_id,
        client_secret=args.client_secret,
        warn_on_lineage_fetch_error=args.warn_on_lineage_fetch_error,
    )


SigmaTranslatorData: TypeAlias = Union[SigmaDatasetTranslatorData, SigmaWorkbookTranslatorData]
SigmaTranslationFn: TypeAlias = TranslationFn[SigmaTranslatorData]

ResolvedTargetedSigmaTranslationFn = Annotated[
    SigmaTranslationFn,
    TranslationFnResolver[SigmaTranslatorData](lambda data: {"data": data}),
]

ResolvedTargetedKeyOnlySigmaTranslationFn = Annotated[
    SigmaTranslationFn,
    TranslationFnResolver[SigmaTranslatorData](
        lambda data: {"data": data}, model_field_type=AssetSpecKeyUpdateKwargs.model()
    ),
]


@record
class SigmaAssetArgs(AssetSpecUpdateKwargs, Resolvable):
    for_workbook: Optional[ResolvedTargetedSigmaTranslationFn] = None
    for_dataset: Optional[ResolvedTargetedSigmaTranslationFn] = None


def resolve_multilayer_translation(context: ResolutionContext, model):
    """The Sigma translation schema supports defining global transforms
    as well as per-content-type transforms. This resolver composes the
    per-content-type transforms with the global transforms.
    """
    info = TranslatorResolvingInfo(
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )

    def _translation_fn(base_asset_spec: AssetSpec, data: SigmaTranslatorData):
        processed_spec = info.get_asset_spec(
            base_asset_spec,
            {
                "data": data,
                "spec": base_asset_spec,
            },
        )

        nested_translation_fns = resolve_fields(
            model=model,
            resolved_cls=SigmaAssetArgs,
            context=context.with_scope(
                **{
                    "data": data,
                    "spec": processed_spec,
                }
            ),
        )
        for_workbook = nested_translation_fns.get("for_workbook")
        for_dataset = nested_translation_fns.get("for_dataset")

        if isinstance(data, SigmaWorkbookTranslatorData) and for_workbook:
            return for_workbook(processed_spec, data)
        if isinstance(data, SigmaDatasetTranslatorData) and for_dataset:
            return for_dataset(processed_spec, data)

        return processed_spec

    return _translation_fn


ResolvedMultilayerTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_multilayer_translation,
        model_field_type=Union[str, SigmaAssetArgs.model()],
    ),
]


class SigmaFilterArgs(Model, Resolvable):
    """Arguments for filtering which Sigma objects to load."""

    workbook_folders: Optional[list[list[str]]] = Field(
        default=None,
        description=(
            "A list of folder paths to fetch workbooks from. Each folder path is a list of folder names, "
            "starting from the root folder. All workbooks contained in the specified folders will be fetched."
        ),
    )
    workbooks: Optional[list[list[str]]] = Field(
        default=None,
        description=(
            "A list of fully qualified workbook paths to fetch. Each workbook path is a list of folder names, "
            "starting from the root folder, and ending with the workbook name."
        ),
    )
    include_unused_datasets: bool = Field(
        default=True,
        description="Whether to include datasets that are not used in any workbooks.",
    )


def resolve_sigma_filter(context: ResolutionContext, model) -> Optional[SigmaFilter]:
    """Resolver function for SigmaFilter that properly resolves templated strings."""
    if model is None:
        return None
    args = SigmaFilterArgs.resolve_from_model(context, model)
    return SigmaFilter(
        workbook_folders=args.workbook_folders,
        workbooks=args.workbooks,
        include_unused_datasets=args.include_unused_datasets,
    )


@beta
@public
@dataclass
class SigmaComponent(StateBackedComponent, Resolvable):
    """Pulls in the contents of a Sigma organization into Dagster assets.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_sigma.SigmaComponent
            attributes:
              organization:
                base_url: https://aws-api.sigmacomputing.com
                client_id: "{{ env.SIGMA_CLIENT_ID }}"
                client_secret: "{{ env.SIGMA_CLIENT_SECRET }}"
              sigma_filter:
                workbook_folders:
                  - ["My Documents", "Analytics"]
                include_unused_datasets: false
    """

    organization: Annotated[
        SigmaOrganization,
        Resolver(
            resolve_sigma_organization,
            model_field_type=SigmaOrganizationArgs.model(),
            description="Configuration for connecting to the Sigma organization",
            examples=[
                {
                    "base_url": "https://aws-api.sigmacomputing.com",
                    "client_id": "{{ env.SIGMA_CLIENT_ID }}",
                    "client_secret": "{{ env.SIGMA_CLIENT_SECRET }}",
                }
            ],
        ),
    ]
    sigma_filter: Annotated[
        Optional[SigmaFilter],
        Resolver(
            resolve_sigma_filter,
            model_field_type=SigmaFilterArgs.model(),
            description="Optional filter for selecting which Sigma workbooks and datasets to load",
            examples=[
                {
                    "workbook_folders": [["My Documents", "Analytics"]],
                    "include_unused_datasets": False,
                }
            ],
        ),
    ] = None
    fetch_column_data: bool = True
    fetch_lineage_data: bool = True
    translation: Optional[ResolvedMultilayerTranslationFn] = None
    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.legacy_code_server_snapshots
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.organization.base_url}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    @cached_property
    def translator(self) -> DagsterSigmaTranslator:
        return SigmaComponentTranslator(self)

    @cached_property
    def _base_translator(self) -> DagsterSigmaTranslator:
        return DagsterSigmaTranslator()

    @public
    def get_asset_spec(self, data: SigmaTranslatorData) -> AssetSpec:
        """Generates an AssetSpec for a given Sigma content item.

        This method can be overridden in a subclass to customize how Sigma content
        (workbooks, datasets) are converted to Dagster asset specs. By default, it delegates
        to the configured DagsterSigmaTranslator.

        Args:
            data: The SigmaTranslatorData containing information about the Sigma content item
                and organization

        Returns:
            An AssetSpec that represents the Sigma content as a Dagster asset

        Example:
            Override this method to add custom tags based on content properties:

            .. code-block:: python

                from dagster_sigma import SigmaComponent
                from dagster import AssetSpec

                class CustomSigmaComponent(SigmaComponent):
                    def get_asset_spec(self, data):
                        base_spec = super().get_asset_spec(data)
                        return base_spec.replace_attributes(
                            tags={
                                **base_spec.tags,
                                "sigma_type": data.properties.get("type"),
                                "owner": data.properties.get("ownerId")
                            }
                        )
        """
        return self._base_translator.get_asset_spec(data)

    @cached_property
    def organization_resource(self) -> SigmaOrganization:
        return self.organization

    def _load_asset_specs(self, state: SigmaOrganizationData) -> list[AssetSpec]:
        translator_data_workbooks = [
            SigmaWorkbookTranslatorData(workbook=workbook, organization_data=state)
            for workbook in state.workbooks
        ]
        translator_data_datasets = [
            SigmaDatasetTranslatorData(dataset=dataset, organization_data=state)
            for dataset in state.datasets
        ]
        return [
            self.translator.get_asset_spec(data)
            for data in [*translator_data_workbooks, *translator_data_datasets]
        ]

    async def write_state_to_path(self, state_path: Path) -> None:
        state = await self.organization_resource.build_organization_data(
            sigma_filter=self.sigma_filter,
            fetch_column_data=self.fetch_column_data,
            fetch_lineage_data=self.fetch_lineage_data,
        )
        state_path.write_text(dg.serialize_value(state))

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        state = dg.deserialize_value(state_path.read_text(), SigmaOrganizationData)
        specs = self._load_asset_specs(state)

        return dg.Definitions(assets=specs)


class SigmaComponentTranslator(
    create_component_translator_cls(SigmaComponent, DagsterSigmaTranslator),
    ComponentTranslator[SigmaComponent],
):
    def __init__(self, component: SigmaComponent):
        self._component = component

    def get_asset_spec(self, data: SigmaTranslatorData) -> AssetSpec:
        base_asset_spec = super().get_asset_spec(data)
        if self.component.translation is None:
            return base_asset_spec
        else:
            return self.component.translation(base_asset_spec, data)
