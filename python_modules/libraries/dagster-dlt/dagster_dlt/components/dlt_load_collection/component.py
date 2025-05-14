import importlib
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Annotated, Callable, Optional, Union

import dagster as dg
from dagster import AssetKey, AssetSpec
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Component, ComponentLoadContext, Resolvable, Resolver
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetAttributesModel
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils import TranslatorResolvingInfo
from dlt import Pipeline
from dlt.extract.source import DltSource
from typing_extensions import TypeAlias

from dagster_dlt.asset_decorator import dlt_assets
from dagster_dlt.components.dlt_load_collection.scaffolder import DltLoadCollectionScaffolder
from dagster_dlt.translator import DagsterDltTranslator, DltResourceTranslatorData

TranslationFn: TypeAlias = Callable[[AssetSpec, DltResourceTranslatorData], AssetSpec]


def _load_object_from_python_path(path: str):
    """Loads a Python object from the given import path, accepting
    relative paths.

    For example, '.foo_module.bar_object' will find the relative module
    'foo_module' and return 'bar_object'.
    """
    context = ComponentLoadContext.current()

    if path.startswith("."):
        path = f"{context.defs_relative_module_name(context.path)}{path}"
    module_name, object_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


class ComponentDagsterDltTranslator(DagsterDltTranslator):
    """Custom base translator, which generates keys from dataset and table names."""

    def __init__(self, *, fn: Optional[TranslationFn] = None):
        super().__init__()
        self._fn = fn or (lambda spec, _: spec)

    def get_asset_spec(self, data: DltResourceTranslatorData) -> AssetSpec:
        table_name = data.resource.table_name
        if isinstance(table_name, Callable):
            table_name = data.resource.name
        prefix = [data.pipeline.dataset_name] if data.pipeline else []
        base_asset_spec = (
            super().get_asset_spec(data).replace_attributes(key=AssetKey(prefix + [table_name]))
        )

        return self._fn(base_asset_spec, data)


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
            "resource": data.resource,
            "pipeline": data.pipeline,
            "spec": base_asset_spec,
        },
    )


ResolvedTranslationFn: TypeAlias = Annotated[
    TranslationFn,
    Resolver(
        resolve_translation,
        model_field_type=Union[str, AssetAttributesModel],
    ),
]


@dataclass
class DltLoadSpecModel(Resolvable):
    """Represents a single dlt load, a combination of pipeline and source."""

    pipeline: Annotated[
        Pipeline,
        Resolver(lambda ctx, path: _load_object_from_python_path(path), model_field_type=str),
    ]
    source: Annotated[
        DltSource,
        Resolver(
            lambda ctx, path: _load_object_from_python_path(path),
            model_field_type=str,
        ),
    ]
    translation: Optional[ResolvedTranslationFn] = None

    @cached_property
    def translator(self):
        if self.translation:
            return ComponentDagsterDltTranslator(fn=self.translation)
        return ComponentDagsterDltTranslator()


@scaffold_with(DltLoadCollectionScaffolder)
@dataclass
class DltLoadCollectionComponent(Component, Resolvable):
    """Expose one or more dlt loads to Dagster as assets.

    [dlt](https://dlthub.com/) is a tool for extracting data from various sources and loading it into a
    destination.
    """

    loads: Sequence[DltLoadSpecModel]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        output = []
        for load in self.loads:

            @dlt_assets(
                dlt_source=load.source,
                dlt_pipeline=load.pipeline,
                name=f"dlt_assets_{load.source.name}_{load.pipeline.dataset_name}",
                dagster_dlt_translator=load.translator,
            )
            def dlt_assets_def(context: AssetExecutionContext):
                yield from self.execute(context, load.source, load.pipeline)

            output.append(dlt_assets_def)

        return dg.Definitions(assets=output)

    def execute(
        self, context: AssetExecutionContext, source: DltSource, pipeline: Pipeline
    ) -> Iterator:
        """Runs the dlt pipeline. Override this method to customize the execution logic."""
        yield from pipeline.run(source)
