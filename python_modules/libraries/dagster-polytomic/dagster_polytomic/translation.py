from typing import Annotated, Optional, TypeAlias, Union

from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.metadata.metadata_set import NamespacedMetadataSet
from dagster.components import Resolvable, Resolver
from dagster.components.resolved.base import resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetSpecUpdateKwargs
from dagster.components.utils import TranslatorResolvingInfo
from dagster.components.utils.translation import TranslationFn, TranslationFnResolver
from dagster_shared.record import record
from typing_extensions import Self

from dagster_polytomic.objects import PolytomicBulkSyncEnrichedSchema, PolytomicWorkspaceData

_TRANSLATOR_DATA_METADATA_KEY = ".dagster-polytomic/translator_data"


class PolytomicSchemaMetadataSet(NamespacedMetadataSet):
    """Represents metadata that is captured from a Polytomic schema."""

    id: str
    bulk_sync_id: str
    output_name: Optional[str] = None
    partition_key: Optional[str] = None
    tracking_field: Optional[str] = None
    source_connection_id: Optional[str] = None
    source_connection_name: Optional[str] = None
    destination_connection_id: Optional[str] = None
    destination_connection_name: Optional[str] = None

    @classmethod
    def from_enriched_schema(cls, enriched_schema: PolytomicBulkSyncEnrichedSchema) -> Self:
        return cls(
            id=enriched_schema.id,
            bulk_sync_id=enriched_schema.bulk_sync_id,
            output_name=enriched_schema.output_name,
            partition_key=enriched_schema.partition_key,
            tracking_field=enriched_schema.tracking_field,
            source_connection_id=enriched_schema.source_connection_id,
            source_connection_name=enriched_schema.source_connection_name,
            destination_connection_id=enriched_schema.destination_connection_id,
            destination_connection_name=enriched_schema.destination_connection_name,
        )

    @classmethod
    def namespace(cls) -> str:
        return "dagster-polytomic"


@record
class PolytomicTranslatorData:
    """Container class for data required to translate an object in an
    Polytomic workspace into a Dagster definition.

    Properties:
        obj (PolytomicBulkSyncEnrichedSchema): The object to translate.
        workspace_data (PolytomicWorkspaceData): Global workspace data.
    """

    obj: PolytomicBulkSyncEnrichedSchema
    workspace_data: PolytomicWorkspaceData


def _resolve_multilayer_translation(context: ResolutionContext, model):
    """The Polytomic translation schema supports defining global transforms
    as well as per-object-type transforms. This resolver composes the
    per-object-type transforms with the global transforms.
    """
    info = TranslatorResolvingInfo(
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )

    def _translation_fn(base_asset_spec: AssetSpec, data: PolytomicTranslatorData):
        processed_spec = info.get_asset_spec(
            base_asset_spec,
            {
                "data": data,
                "spec": base_asset_spec,
            },
        )

        nested_translation_fns = resolve_fields(
            model=model,
            resolved_cls=PolytomicTranslationArgs,
            context=context.with_scope(
                **{
                    "data": data,
                    "spec": processed_spec,
                }
            ),
        )
        for_schema = nested_translation_fns.get("for_schema")

        if isinstance(data.obj, PolytomicBulkSyncEnrichedSchema) and for_schema:
            return for_schema(processed_spec, data)

        return processed_spec

    return _translation_fn


PolytomicTranslationFn: TypeAlias = TranslationFn[PolytomicTranslatorData]

ResolvedTargetedPolytomicTranslationFn = Annotated[
    PolytomicTranslationFn,
    TranslationFnResolver[PolytomicTranslatorData](lambda data: {"data": data}),
]


@record
class PolytomicTranslationArgs(AssetSpecUpdateKwargs, Resolvable):
    """Model used to allow per-object-type translation of a Polytomic object."""

    for_schema: Optional[ResolvedTargetedPolytomicTranslationFn] = None


ResolvedPolytomicTranslationFn = Annotated[
    PolytomicTranslationFn,
    Resolver(
        _resolve_multilayer_translation,
        model_field_type=Union[str, PolytomicTranslationArgs.model()],
    ),
]
