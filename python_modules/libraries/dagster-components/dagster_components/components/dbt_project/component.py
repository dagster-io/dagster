from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from typing import Annotated, Any, Optional

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_dbt import (
    DagsterDbtTranslator,
    DbtCliResource,
    DbtManifestAssetSelection,
    DbtProject,
    dbt_assets,
)
from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.dbt_manifest import validate_manifest

from dagster_components import Component, ComponentLoadContext
from dagster_components.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_components.resolved.core_models import (
    AssetAttributesModel,
    AssetPostProcessor,
    AssetPostProcessorModel,
    OpSpec,
    OpSpecModel,
    ResolutionContext,
)
from dagster_components.resolved.metadata import ResolvableFieldInfo
from dagster_components.resolved.model import FieldResolver, ResolvableModel, ResolvedFrom
from dagster_components.scaffoldable.decorator import scaffoldable
from dagster_components.utils import (
    AssetSpecTranslator,
    TranslatorResolvingInfo,
    get_wrapped_translator_class,
)


class DbtProjectModel(ResolvableModel):
    dbt: DbtCliResource
    op: Optional[OpSpecModel] = None
    asset_attributes: Annotated[
        Optional[AssetAttributesModel],
        ResolvableFieldInfo(required_scope={"node", "spec"}),
    ] = None
    asset_post_processors: Optional[Sequence[AssetPostProcessorModel]] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None


def resolve_translator(context: ResolutionContext, model: DbtProjectModel) -> DagsterDbtTranslator:
    project = DbtProject(model.dbt.project_dir)
    manifest = project.manifest_path

    class DagsterDbtTranslatorWithSpecs(DagsterDbtTranslator, AssetSpecTranslator):
        """dagster-dbt's asset specs are not wholly determined by the translator.
        They're built externally, using build_dbt_specs. This class wraps the base
        translator, while emulating a get_asset_spec method by reaching out to
        build_dbt_specs and caching the result.
        """

        def __init__(self):
            self._specs_map: Optional[Mapping[AssetKey, AssetSpec]] = None

        def get_specs_by_key(self) -> Mapping[AssetKey, AssetSpec]:
            if not self._specs_map:
                specs, _ = build_dbt_specs(
                    translator=self,
                    manifest=validate_manifest(manifest),
                    select=model.select,
                    exclude=model.exclude or "",
                    io_manager_key=None,
                    project=project,
                )
                self._specs_map = {spec.key: spec for spec in specs}
            return self._specs_map

        def get_asset_spec(self, obj: Any) -> AssetSpec:
            return self.get_specs_by_key()[self.get_asset_key(obj)]

    if model.asset_attributes and model.asset_attributes.deps:
        # TODO: Consider supporting alerting deps in the future
        raise ValueError("deps are not supported for dbt_project component")
    return get_wrapped_translator_class(DagsterDbtTranslatorWithSpecs)(
        resolving_info=TranslatorResolvingInfo(
            "node", model.asset_attributes or AssetAttributesModel(), context
        )
    )


def resolve_dbt(context: ResolutionContext, dbt: DbtCliResource) -> DbtCliResource:
    return DbtCliResource(**context.resolve_value(dbt.model_dump()))


@scaffoldable(scaffolder=DbtProjectComponentScaffolder)
@dataclass
class DbtProjectComponent(Component, ResolvedFrom[DbtProjectModel]):
    """Expose a DBT project to Dagster as a set of assets."""

    dbt: Annotated[DbtCliResource, FieldResolver(resolve_dbt)]
    op: Annotated[Optional[OpSpec], FieldResolver(OpSpec.from_optional)] = None
    # This requires from_parent because it access asset_attributes in the model
    translator: Annotated[DagsterDbtTranslator, FieldResolver.from_model(resolve_translator)] = (
        field(default_factory=DagsterDbtTranslator)
    )
    asset_post_processors: Annotated[
        Optional[Sequence[AssetPostProcessor]],
        FieldResolver(AssetPostProcessor.from_optional_seq),
    ] = None
    select: str = "fqn:*"
    exclude: Optional[str] = None

    @cached_property
    def project(self) -> DbtProject:
        return DbtProject(self.dbt.project_dir)

    def get_asset_selection(
        self, select: str, exclude: Optional[str] = None
    ) -> DbtManifestAssetSelection:
        return DbtManifestAssetSelection.build(
            manifest=self.project.manifest_path,
            dagster_dbt_translator=self.translator,
            select=select,
            exclude=exclude,
        )

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        self.project.prepare_if_dev()

        @dbt_assets(
            manifest=self.project.manifest_path,
            project=self.project,
            name=self.op.name if self.op else self.project.name,
            op_tags=self.op.tags if self.op else None,
            dagster_dbt_translator=self.translator,
            select=self.select,
            exclude=self.exclude,
            backfill_policy=self.op.backfill_policy if self.op else None,
        )
        def _fn(context: AssetExecutionContext):
            yield from self.execute(context=context, dbt=self.dbt)

        defs = Definitions(assets=[_fn])
        for post_processor in self.asset_post_processors or []:
            defs = post_processor.fn(defs)
        return defs

    def execute(self, context: AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        yield from dbt.cli(["build"], context=context).stream()
