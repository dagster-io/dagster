from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, TypeAlias, Union

from dagster import Resolvable, Resolver
from dagster._annotations import public
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
from dagster.components.resolved.core_models import OpSpec
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dagster_shared.utils.warnings import deprecation_warning
from pydantic import BaseModel, ConfigDict, Field

from dagster_sling.asset_decorator import sling_assets
from dagster_sling.components.sling_replication_collection.scaffolder import (
    SlingReplicationComponentScaffolder,
)
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_sling.resources import AssetExecutionContext, SlingConnectionResource, SlingResource

SlingMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]


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
    include_metadata: Annotated[
        list[SlingMetadataAddons],
        Resolver.default(
            description="Optionally include additional metadata in materializations generated while executing your Sling models",
            examples=[
                ["row_count"],
                ["row_count", "column_metadata"],
            ],
        ),
    ] = field(default_factory=list)


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


@public
@scaffold_with(SlingReplicationComponentScaffolder)
@dataclass
class SlingReplicationCollectionComponent(Component, Resolvable):
    """Expose one or more Sling replications to Dagster as assets.

    To get started, run:

    ``dg scaffold defs dagster_sling.SlingReplicationCollectionComponent {defs_path}``

    This will create a defs.yaml as well as a ``replication.yaml``, which is a Sling-specific configuration
    file. See Sling's `documentation <https://docs.slingdata.io/concepts/replication#overview>`_ on ``replication.yaml``.
    """

    connections: ResolvedSlingConnections = field(default_factory=list)
    replications: Sequence[SlingReplicationSpecModel] = field(default_factory=list)
    resource: Annotated[
        Optional[SlingResource],
        Resolver(resolve_resource, model_field_name="sling"),
    ] = None

    @cached_property
    def sling_resource(self) -> SlingResource:
        return self.resource or SlingResource(connections=self.connections)

    @cached_property
    def _base_translator(self) -> DagsterSlingTranslator:
        return DagsterSlingTranslator()

    @public
    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
        """Generates an AssetSpec for a given Sling stream definition.

        This method can be overridden in a subclass to customize how Sling stream definitions
        are converted to Dagster asset specs. By default, it delegates to the configured
        DagsterSlingTranslator.

        Args:
            stream_definition: A dictionary representing a single stream from the Sling
                replication config, containing source and target information

        Returns:
            An AssetSpec that represents the Sling stream as a Dagster asset

        Example:
            Override this method to add custom metadata based on stream properties:

            .. code-block:: python

                from dagster_sling import SlingReplicationCollectionComponent
                from dagster import AssetSpec

                class CustomSlingComponent(SlingReplicationCollectionComponent):
                    def get_asset_spec(self, stream_definition):
                        base_spec = super().get_asset_spec(stream_definition)
                        return base_spec.replace_attributes(
                            metadata={
                                **base_spec.metadata,
                                "source": stream_definition.get("source"),
                                "target": stream_definition.get("target")
                            }
                        )
        """
        return self._base_translator.get_asset_spec(stream_definition)

    def build_asset(
        self, context: ComponentLoadContext, replication_spec_model: SlingReplicationSpecModel
    ) -> AssetsDefinition:
        op_spec = replication_spec_model.op or OpSpec()
        translator = SlingComponentTranslator(self, replication_spec_model, context.path)

        @sling_assets(
            name=op_spec.name or Path(replication_spec_model.path).stem,
            op_tags=op_spec.tags,
            replication_config=context.path / replication_spec_model.path,
            dagster_sling_translator=translator,
            backfill_policy=op_spec.backfill_policy,
        )
        def _asset(context: AssetExecutionContext):
            yield from self.execute(
                context=context,
                sling=self.sling_resource,
                replication_spec_model=replication_spec_model,
            )

        return _asset

    @public
    def execute(
        self,
        context: AssetExecutionContext,
        sling: SlingResource,
        replication_spec_model: SlingReplicationSpecModel,
    ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
        """Executes a Sling replication for the selected streams.

        This method can be overridden in a subclass to customize the replication execution
        behavior, such as adding custom logging, modifying metadata collection, or handling
        results differently.

        Args:
            context: The asset execution context provided by Dagster
            sling: The SlingResource used to execute the replication
            replication_spec_model: The model containing replication configuration and metadata options

        Yields:
            AssetMaterialization or MaterializeResult events from the Sling replication

        Example:
            Override this method to add custom logging during replication:

            .. code-block:: python

                from dagster_sling import SlingReplicationCollectionComponent
                from dagster import AssetExecutionContext

                class CustomSlingComponent(SlingReplicationCollectionComponent):
                    def execute(self, context, sling, replication_spec_model):
                        context.log.info("Starting Sling replication")
                        yield from super().execute(context, sling, replication_spec_model)
                        context.log.info("Sling replication completed")
        """
        iterator = sling.replicate(context=context)
        if "column_metadata" in replication_spec_model.include_metadata:
            iterator = iterator.fetch_column_metadata()
        if "row_count" in replication_spec_model.include_metadata:
            iterator = iterator.fetch_row_count()
        yield from iterator

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions(
            assets=[self.build_asset(context, replication) for replication in self.replications],
        )


class SlingComponentTranslator(
    create_component_translator_cls(SlingReplicationCollectionComponent, DagsterSlingTranslator),
    ComponentTranslator[SlingReplicationCollectionComponent],
):
    def __init__(
        self,
        component: SlingReplicationCollectionComponent,
        replication_spec: SlingReplicationSpecModel,
        base_path: Path,
    ):
        self._component = component
        self._replication_spec = replication_spec
        self._base_path = base_path

    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> AssetSpec:
        spec = super().get_asset_spec(stream_definition)
        if self._replication_spec.translation is not None:
            spec = self._replication_spec.translation(spec, stream_definition)

        # always add code references to the replication spec
        code_reference = LocalFileCodeReference(
            file_path=str(self._base_path / self._replication_spec.path)
        )
        return merge_code_references(spec, [code_reference])
