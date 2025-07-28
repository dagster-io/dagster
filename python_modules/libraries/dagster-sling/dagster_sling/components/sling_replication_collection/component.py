import textwrap
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Union

from dagster import Resolvable, Resolver
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.metadata.source_code import (
    LocalFileCodeReference,
    merge_code_references,
)
from dagster._core.definitions.result import MaterializeResult
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetPostProcessor, OpSpec
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.translation import TranslationFn, TranslationFnResolver
from dagster_shared.utils.warnings import deprecation_warning
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypeAlias

from dagster_sling.asset_decorator import sling_assets
from dagster_sling.components.sling_replication_collection.scaffolder import (
    SlingReplicationComponentScaffolder,
)
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_sling.resources import AssetExecutionContext, SlingConnectionResource, SlingResource

SlingMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]


class ProxyDagsterSlingTranslator(DagsterSlingTranslator):
    def __init__(self, fn: TranslationFn[Mapping[str, Any]]):
        self._fn = fn

    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
        base_asset_spec = super().get_asset_spec(stream_definition)
        return self._fn(base_asset_spec, stream_definition)


@dataclass
class SlingReplicationSpecModel(Resolvable):
    path: str
    op: Optional[OpSpec] = None
    translation: Optional[
        Annotated[
            TranslationFn[Mapping[str, Any]],
            TranslationFnResolver(
                template_vars_for_translation_fn=lambda data: {"stream_definition": data}
            ),
        ]
    ] = None
    include_metadata: list[SlingMetadataAddons] = field(default_factory=list)

    @cached_property
    def translator(self):
        if self.translation:
            return ProxyDagsterSlingTranslator(self.translation)
        return DagsterSlingTranslator()


def resolve_resource(
    context: ResolutionContext,
    sling,
) -> Optional[SlingResource]:
    if sling:
        deprecation_warning(
            "The `sling` field is deprecated, use `connections` instead. This field will be removed in a future release.",
            "1.11.1",
        )
    return SlingResource(**context.resolve_value(sling.model_dump())) if sling else None


def replicate(
    context: AssetExecutionContext,
    connections: list[SlingConnectionResource],
) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
    sling = SlingResource(connections=connections)
    yield from sling.replicate(context=context)


class SlingConnectionResourcePropertiesModel(Resolvable, BaseModel):
    """Properties of a Sling connection resource."""

    # each connection type supports a variety of different properties
    model_config = ConfigDict(extra="allow")

    type: str = Field(
        description="Type of the source connection, must match the Sling connection types. Use 'file' for local storage."
    )
    connection_string: Optional[str] = Field(
        description="The optional connection string for the source database, if not using keyword arguments.",
        default=None,
    )


def resolve_connections(
    context: ResolutionContext,
    connections: Mapping[str, SlingConnectionResourcePropertiesModel],
) -> list[SlingConnectionResource]:
    return [
        SlingConnectionResource(
            name=name,
            **context.resolve_value(
                connection if isinstance(connection, dict) else connection.model_dump()
            ),
        )
        for name, connection in connections.items()
    ]


ResolvedSlingConnections: TypeAlias = Annotated[
    list[SlingConnectionResource],
    Resolver(
        resolve_connections, model_field_type=Mapping[str, SlingConnectionResourcePropertiesModel]
    ),
]


@scaffold_with(SlingReplicationComponentScaffolder)
@dataclass
class SlingReplicationCollectionComponent(Component, Resolvable):
    """Expose one or more Sling replications to Dagster as assets.

    [Sling](https://slingdata.io/) is a Powerful Data Integration tool enabling seamless ELT
    operations as well as quality checks across files, databases, and storage systems.

    dg scaffold dagster_sling.SlingReplicationCollectionComponent {defs_path} to get started.

    This will create a defs.yaml as well as a `replication.yaml` which is a Sling-specific configuration
    file. See Sling's [documentation](https://docs.slingdata.io/concepts/replication#overview) on `replication.yaml`.
    """

    connections: ResolvedSlingConnections = field(default_factory=list)
    replications: Sequence[SlingReplicationSpecModel] = field(default_factory=list)
    # TODO: deprecate and then delete -- schrockn 2025-06-10
    asset_post_processors: Optional[Sequence[AssetPostProcessor]] = None
    resource: Annotated[
        Optional[SlingResource],
        Resolver(resolve_resource, model_field_name="sling"),
    ] = None

    @cached_property
    def sling_resource(self) -> SlingResource:
        return self.resource or SlingResource(connections=self.connections)

    def build_asset(
        self, context: ComponentLoadContext, replication_spec_model: SlingReplicationSpecModel
    ) -> AssetsDefinition:
        op_spec = replication_spec_model.op or OpSpec()

        class ReplicationTranslatorWithCodeReferences(DagsterSlingTranslator):
            def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
                asset_spec = replication_spec_model.translator.get_asset_spec(stream_definition)
                return merge_code_references(
                    asset_spec,
                    [
                        LocalFileCodeReference(
                            file_path=str(context.path / replication_spec_model.path)
                        )
                    ],
                )

        @sling_assets(
            name=op_spec.name or Path(replication_spec_model.path).stem,
            op_tags=op_spec.tags,
            replication_config=context.path / replication_spec_model.path,
            dagster_sling_translator=ReplicationTranslatorWithCodeReferences(),
            backfill_policy=op_spec.backfill_policy,
        )
        def _asset(context: AssetExecutionContext):
            yield from self.execute(
                context=context,
                sling=self.sling_resource,
                replication_spec_model=replication_spec_model,
            )

        return _asset

    def execute(
        self,
        context: AssetExecutionContext,
        sling: SlingResource,
        replication_spec_model: SlingReplicationSpecModel,
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        iterator = sling.replicate(context=context)
        if "column_metadata" in replication_spec_model.include_metadata:
            iterator = iterator.fetch_column_metadata()
        if "row_count" in replication_spec_model.include_metadata:
            iterator = iterator.fetch_row_count()
        yield from iterator

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        if self.asset_post_processors:
            raise Exception(
                "The asset_post_processors field is deprecated, place your post-processors in the assets"
                " field in the top-level post_processing field instead, as in this example:\n"
                + textwrap.dedent(
                    """
                    type: dagster_sling.SlingReplicationCollectionComponent

                    attributes: ~

                    post_processing:
                      assets:
                        - target: "*"
                          attributes:
                            group_name: "my_group"
                    """
                )
            )

        return Definitions(
            assets=[self.build_asset(context, replication) for replication in self.replications],
        )
