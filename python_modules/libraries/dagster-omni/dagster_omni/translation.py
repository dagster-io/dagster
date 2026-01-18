from typing import Annotated, Optional, TypeAlias, Union

import dateutil
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster._core.definitions.metadata.metadata_value import (
    TimestampMetadataValue,
    UrlMetadataValue,
)
from dagster.components import Resolvable, Resolver
from dagster.components.resolved.base import resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetSpecKeyUpdateKwargs, AssetSpecUpdateKwargs
from dagster.components.utils import TranslatorResolvingInfo
from dagster.components.utils.translation import TranslationFn, TranslationFnResolver
from dagster_shared.record import record
from typing_extensions import Self

from dagster_omni.objects import OmniDocument, OmniQuery, OmniWorkspaceData
from dagster_omni.workspace import OmniWorkspace

TRANSLATOR_DATA_METADATA_KEY = ".dagster-omni/translator_data"


class OmniDocumentMetadataSet(NamespacedMetadataSet):
    """Represents metadata that is captured from an Omni document."""

    url: Optional[UrlMetadataValue] = None
    owner_name: str
    document_name: str
    document_type: str
    updated_at: TimestampMetadataValue
    favorites: Optional[int] = None
    views: Optional[int] = None

    @classmethod
    def from_document(cls, workspace: OmniWorkspace, document: OmniDocument) -> Self:
        url_str = f"{workspace.base_url.rstrip('/')}/dashboards/{document.identifier}"

        return cls(
            url=UrlMetadataValue(url_str) if document.has_dashboard else None,
            document_name=document.name,
            document_type=document.type,
            updated_at=TimestampMetadataValue(
                dateutil.parser.parse(document.updated_at).timestamp()
            ),
            owner_name=document.owner.name,
            favorites=document.favorites,
            views=document.views,
        )

    @classmethod
    def namespace(cls) -> str:
        return "dagster-omni"


@record
class OmniTranslatorData:
    """Container class for data required to translate an object in an
    Omni workspace into a Dagster definition.

    Properties:
        obj (Union[OmniDocument, OmniQuery]): The object to translate.
        workspace_data (OmniWorkspaceData): Global workspace data.
    """

    obj: Union[OmniDocument, OmniQuery]
    workspace_data: OmniWorkspaceData


def _resolve_multilayer_translation(context: ResolutionContext, model):
    """The Omni translation schema supports defining global transforms
    as well as per-object-type transforms. This resolver composes the
    per-object-type transforms with the global transforms.
    """
    info = TranslatorResolvingInfo(
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )

    def _translation_fn(base_asset_spec: AssetSpec, data: OmniTranslatorData):
        processed_spec = info.get_asset_spec(
            base_asset_spec,
            {
                "data": data,
                "spec": base_asset_spec,
            },
        )

        nested_translation_fns = resolve_fields(
            model=model,
            resolved_cls=OmniTranslationArgs,
            context=context.with_scope(
                **{
                    "data": data,
                    "spec": processed_spec,
                }
            ),
        )
        for_document = nested_translation_fns.get("for_document")
        for_query = nested_translation_fns.get("for_query")

        if isinstance(data.obj, OmniDocument) and for_document:
            return for_document(processed_spec, data)
        if isinstance(data.obj, OmniQuery) and for_query:
            return for_query(processed_spec, data)

        return processed_spec

    return _translation_fn


OmniTranslationFn: TypeAlias = TranslationFn[OmniTranslatorData]

ResolvedTargetedOmniTranslationFn = Annotated[
    OmniTranslationFn,
    TranslationFnResolver[OmniTranslatorData](lambda data: {"data": data}),
]

ResolvedTargetedKeyOnlyOmniTranslationFn = Annotated[
    OmniTranslationFn,
    TranslationFnResolver[OmniTranslatorData](
        lambda data: {"data": data}, model_field_type=AssetSpecKeyUpdateKwargs.model()
    ),
]


@record
class OmniTranslationArgs(AssetSpecUpdateKwargs, Resolvable):
    """Model used to allow per-object-type translation of an Omni object."""

    for_document: Optional[ResolvedTargetedOmniTranslationFn] = None
    for_query: Optional[ResolvedTargetedKeyOnlyOmniTranslationFn] = None


ResolvedOmniTranslationFn = Annotated[
    OmniTranslationFn,
    Resolver(
        _resolve_multilayer_translation,
        model_field_type=Union[str, OmniTranslationArgs.model()],
    ),
]
