import importlib
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Optional

import dagster as dg
from dagster import AssetKey, AssetSpec, Component, ComponentLoadContext, Resolvable, Resolver
from dagster._annotations import public
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.resolved.context import ResolutionContext
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dlt import Pipeline
from dlt.extract.source import DltSource

from dagster_dlt.asset_decorator import dlt_assets
from dagster_dlt.components.dlt_load_collection.scaffolder import DltLoadCollectionScaffolder
from dagster_dlt.translator import DagsterDltTranslator, DltResourceTranslatorData

if TYPE_CHECKING:
    from dagster_dlt import DagsterDltResource


def _load_object_from_python_path(resolution_context: ResolutionContext, path: str):
    """Loads a Python object from the given import path, accepting
    relative paths.

    For example, '.foo_module.bar_object' will find the relative module
    'foo_module' and return 'bar_object'.
    """
    context = ComponentLoadContext.from_resolution_context(resolution_context)

    if path.startswith("."):
        path = f"{context.defs_relative_module_name(context.path)}{path}"
    module_name, object_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


@dataclass
class DltLoadSpecModel(Resolvable):
    """Represents a single dlt load, a combination of pipeline and source."""

    pipeline: Annotated[
        Pipeline,
        Resolver(lambda ctx, path: _load_object_from_python_path(ctx, path), model_field_type=str),
    ]
    source: Annotated[
        DltSource,
        Resolver(
            lambda ctx, path: _load_object_from_python_path(ctx, path),
            model_field_type=str,
        ),
    ]
    translation: Optional[
        Annotated[
            TranslationFn[DltResourceTranslatorData],
            TranslationFnResolver[DltResourceTranslatorData](
                lambda data: {"resource": data.resource, "pipeline": data.pipeline}
            ),
        ]
    ] = None


@public
@scaffold_with(DltLoadCollectionScaffolder)
@dataclass
class DltLoadCollectionComponent(Component, Resolvable):
    """Expose one or more dlt loads to Dagster as assets."""

    loads: Sequence[DltLoadSpecModel]

    @property
    def dlt_pipeline_resource(self) -> "DagsterDltResource":
        from dagster_dlt import DagsterDltResource

        return DagsterDltResource()

    @cached_property
    def _base_translator(self) -> DagsterDltTranslator:
        return DagsterDltTranslator()

    @public
    def get_asset_spec(self, data: DltResourceTranslatorData) -> AssetSpec:
        """Generates an AssetSpec for a given dlt resource.

        This method can be overridden in a subclass to customize how dlt resources are
        converted to Dagster asset specs. By default, it delegates to the configured
        DagsterDltTranslator.

        Args:
            data: The DltResourceTranslatorData containing information about the dlt source
                and resource being loaded

        Returns:
            An AssetSpec that represents the dlt resource as a Dagster asset

        Example:
            Override this method to add custom tags based on resource properties:

            .. code-block:: python

                from dagster_dlt import DltLoadCollectionComponent
                from dagster import AssetSpec

                class CustomDltLoadCollectionComponent(DltLoadCollectionComponent):
                    def get_asset_spec(self, data):
                        base_spec = super().get_asset_spec(data)
                        return base_spec.replace_attributes(
                            tags={
                                **base_spec.tags,
                                "source": data.source_name,
                                "resource": data.resource_name
                            }
                        )
        """
        return self._base_translator.get_asset_spec(data)

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        output = []
        for load in self.loads:
            translator = DltComponentTranslator(self, load)

            @dlt_assets(
                dlt_source=load.source,
                dlt_pipeline=load.pipeline,
                name=f"dlt_assets_{load.source.name}_{load.pipeline.dataset_name}",
                dagster_dlt_translator=translator,
            )
            def dlt_assets_def(context: AssetExecutionContext):
                yield from self.execute(context, self.dlt_pipeline_resource)

            output.append(dlt_assets_def)

        return dg.Definitions(assets=output)

    @public
    def execute(
        self, context: AssetExecutionContext, dlt_pipeline_resource: "DagsterDltResource"
    ) -> Iterator:
        """Executes the dlt pipeline for the selected resources.

        This method can be overridden in a subclass to customize the pipeline execution behavior,
        such as adding custom logging, validation, or error handling.

        Args:
            context: The asset execution context provided by Dagster
            dlt_pipeline_resource: The DagsterDltResource used to run the dlt pipeline

        Yields:
            Events from the dlt pipeline execution (e.g., AssetMaterialization, MaterializeResult)

        Example:
            Override this method to add custom logging during pipeline execution:

            .. code-block:: python

                from dagster_dlt import DltLoadCollectionComponent
                from dagster import AssetExecutionContext

                class CustomDltLoadCollectionComponent(DltLoadCollectionComponent):
                    def execute(self, context, dlt_pipeline_resource):
                        context.log.info("Starting dlt pipeline execution")
                        yield from super().execute(context, dlt_pipeline_resource)
                        context.log.info("dlt pipeline execution completed")
        """
        yield from dlt_pipeline_resource.run(context=context)


class DltComponentTranslator(
    create_component_translator_cls(DltLoadCollectionComponent, DagsterDltTranslator),
    ComponentTranslator[DltLoadCollectionComponent],
):
    def __init__(self, component: "DltLoadCollectionComponent", load_spec: "DltLoadSpecModel"):
        self._component = component
        self._load_spec = load_spec

    def get_asset_spec(self, data: DltResourceTranslatorData) -> AssetSpec:
        table_name = data.resource.table_name
        if isinstance(table_name, Callable):
            table_name = data.resource.name
        prefix = (
            [data.pipeline.dataset_name] if data.pipeline and data.pipeline.dataset_name else []
        )
        base_asset_spec = (
            super().get_asset_spec(data).replace_attributes(key=AssetKey(prefix + [table_name]))
        )
        if self._load_spec.translation is None:
            return base_asset_spec
        else:
            return self._load_spec.translation(base_asset_spec, data)
