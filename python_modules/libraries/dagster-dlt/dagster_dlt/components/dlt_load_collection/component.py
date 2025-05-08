import importlib
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from functools import cached_property
from types import ModuleType
from typing import Annotated, Any, Callable, Optional, Union

import dagster as dg
from dagster import AssetKey, AssetSpec
from dagster._core.definitions.metadata.source_code import (
    LocalFileCodeReference,
    merge_code_references,
)
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
from dagster_dlt.components.dlt_load_collection.scaffolder import DltComponentScaffolder
from dagster_dlt.translator import DagsterDltTranslator, DltResourceTranslatorData

TranslationFn: TypeAlias = Callable[[AssetSpec, DltResourceTranslatorData], AssetSpec]


def _get_module_and_object_from_path(path: str) -> tuple[ModuleType, Any]:
    """Loads a Python object from the given import path, accepting
    relative paths.

    For example, '.foo_module.bar_object' will find the relative module
    'foo_module' and return `foo_module` and 'bar_object'.
    """
    context = ComponentLoadContext.current()

    if path.startswith("."):
        path = f"{context.defs_relative_module_name(context.path)}{path}"
    module_name, object_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)

    # find the line number in module where object_name is
    return module, getattr(module, object_name)


def _get_code_reference_from_path(path: str) -> LocalFileCodeReference:
    """Get a code reference from the given import path, accepting
    relative paths.
    """
    module, _ = _get_module_and_object_from_path(path)

    return LocalFileCodeReference(
        file_path=str(module.__file__),
    )


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
        Resolver(lambda ctx, path: _get_module_and_object_from_path(path)[1], model_field_type=str),
    ]
    source: Annotated[
        DltSource,
        Resolver(
            lambda ctx, path: _get_module_and_object_from_path(path)[1],
            model_field_type=str,
        ),
    ]
    pipeline_code_reference: Annotated[
        Optional[LocalFileCodeReference],
        Resolver.from_model(
            lambda ctx, model: _get_code_reference_from_path(model.pipeline),
            model_field_name="pipeline",
            model_field_type=...,
        ),
    ] = None
    source_code_reference: Annotated[
        Optional[LocalFileCodeReference],
        Resolver.from_model(
            lambda ctx, model: _get_code_reference_from_path(model.source),
            model_field_name="source",
            model_field_type=...,
        ),
    ] = None
    translation: Optional[ResolvedTranslationFn] = None

    @cached_property
    def translator(self):
        if self.translation:
            return ComponentDagsterDltTranslator(fn=self.translation)
        return ComponentDagsterDltTranslator()


@scaffold_with(DltComponentScaffolder)
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
            code_references_to_add = []
            if load.pipeline_code_reference:
                code_references_to_add.append(load.pipeline_code_reference)
            if load.source_code_reference and (
                not load.pipeline_code_reference
                or load.source_code_reference.file_path != load.pipeline_code_reference.file_path
            ):
                code_references_to_add.append(load.source_code_reference)

            translator = load.translator or DagsterDltTranslator()

            class DltTranslatorWithCodeReferences(DagsterDltTranslator):
                def get_asset_spec(self, obj: Any) -> AssetSpec:
                    asset_spec = translator.get_asset_spec(obj)
                    return merge_code_references(
                        asset_spec,
                        code_references_to_add,
                    )

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
