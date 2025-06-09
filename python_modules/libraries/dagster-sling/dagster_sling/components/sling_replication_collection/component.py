from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Callable, Literal, Optional, Union

import dagster as dg
from dagster._core.definitions.metadata.source_code import (
    LocalFileCodeReference,
    merge_code_references,
)
from dagster.components.lib.enclosing_component import EnclosingComponent
from dagster.components.lib.executable_component.component import ExecutionMetadataSpec
from dagster.components.lib.executable_component.function_component import (
    FunctionComponent,
    FunctionSpec,
)
from dagster.components.resolved.core_models import AssetAttributesModel
from dagster.components.utils import TranslatorResolvingInfo
from pydantic import Field
from typing_extensions import TypeAlias

from dagster_sling.asset_decorator import get_sling_asset_specs
from dagster_sling.components.sling_replication_collection.scaffolder import (
    SlingReplicationComponentScaffolder,
)
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_sling.resources import SlingResource

SlingMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]


def resolve_translation(context: dg.ResolutionContext, model):
    info = TranslatorResolvingInfo(
        "stream_definition",
        asset_attributes=model,
        resolution_context=context,
        model_key="translation",
    )
    return lambda base_asset_spec, stream_definition: info.get_asset_spec(
        base_asset_spec,
        {
            "stream_definition": stream_definition,
            "spec": base_asset_spec,
        },
    )


TranslationFn: TypeAlias = Callable[[dg.AssetSpec, Mapping[str, Any]], dg.AssetSpec]

ResolvedTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    dg.Resolver(
        resolve_translation,
        model_field_type=Union[str, AssetAttributesModel],
        inject_before_resolve=False,
    ),
]


class ProxyDagsterSlingTranslator(DagsterSlingTranslator):
    def __init__(self, fn: TranslationFn):
        self._fn = fn

    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> dg.AssetSpec:
        base_asset_spec = super().get_asset_spec(stream_definition)
        return self._fn(base_asset_spec, stream_definition)


@dataclass
class SlingReplicationSpecModel(dg.Resolvable):
    path: str
    execution: ExecutionMetadataSpec = field(default_factory=ExecutionMetadataSpec)
    translation: Optional[ResolvedTranslationFn] = None
    include_metadata: list[SlingMetadataAddons] = field(default_factory=list)

    @cached_property
    def translator(self):
        if self.translation:
            return ProxyDagsterSlingTranslator(self.translation)
        return DagsterSlingTranslator()


def resolve_resource(
    context: dg.ResolutionContext,
    sling,
) -> SlingResource:
    return SlingResource(**context.resolve_value(sling.model_dump())) if sling else SlingResource()


class ReplicationTranslatorWithCodeReferences(DagsterSlingTranslator):
    def __init__(self, path: Path, replication_spec_model: SlingReplicationSpecModel):
        self.path = path
        self.replication_spec_model = replication_spec_model

    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> dg.AssetSpec:
        asset_spec = self.replication_spec_model.translator.get_asset_spec(stream_definition)
        return merge_code_references(
            asset_spec,
            [LocalFileCodeReference(file_path=str(self.path / self.replication_spec_model.path))],
        )


@dg.scaffold_with(SlingReplicationComponentScaffolder)
class SlingReplicationCollectionComponent(EnclosingComponent):
    """Expose one or more Sling replications to Dagster as assets.

    [Sling](https://slingdata.io/) is a Powerful Data Integration tool enabling seamless ELT
    operations as well as quality checks across files, databases, and storage systems.

    dg scaffold dagster_sling.SlingReplicationCollectionComponent {component_path} to get started.

    This will create a defs.yaml as well as a `replication.yaml` which is a Sling-specific configuration
    file. See Sling's [documentation](https://docs.slingdata.io/concepts/replication#overview) on `replication.yaml`.
    """

    resource: Annotated[
        SlingResource,
        dg.Resolver(
            resolve_resource,
            model_field_name="sling",
        ),
    ] = Field(SlingResource())
    replications: Sequence[SlingReplicationSpecModel] = Field([])

    def build_components(self, context: dg.ComponentLoadContext) -> Iterable[dg.Component]:
        return [replication_component(replication, context) for replication in self.replications]

    def resources(self) -> Mapping[str, Any]:
        return {"sling": self.resource}


def replication_component(
    replication_spec_model: SlingReplicationSpecModel,
    context: dg.ComponentLoadContext,
) -> FunctionComponent:
    def _execute_fn(context: dg.AssetExecutionContext, sling: SlingResource):
        iterator = sling.replicate(context=context)
        if "column_metadata" in replication_spec_model.include_metadata:
            iterator = iterator.fetch_column_metadata()
        if "row_count" in replication_spec_model.include_metadata:
            iterator = iterator.fetch_row_count()
        yield from iterator

    return FunctionComponent(
        execution=FunctionSpec.to_function_spec(
            replication_spec_model.execution, _execute_fn, Path(replication_spec_model.path).stem
        ),
        assets=get_sling_asset_specs(
            replication_config=context.path / replication_spec_model.path,
            dagster_sling_translator=ReplicationTranslatorWithCodeReferences(
                path=context.path,
                replication_spec_model=replication_spec_model,
            ),
            partitions_def=None,
        ),
    )
