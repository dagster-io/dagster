import importlib
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Annotated, Callable

import dagster as dg
from dagster import AssetKey, AssetSpec
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components import Component, ComponentLoadContext, Resolvable
from dagster.components.resolved.core_models import Resolver
from dlt import Pipeline
from dlt.extract.source import DltSource

from dagster_dlt.asset_decorator import dlt_assets
from dagster_dlt.translator import DagsterDltTranslator, DltResourceTranslatorData


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


class ComponentDagsterDltTranslator(DagsterDltTranslator):
    """Custom base translator, which generates keys from dataset and table names."""

    def get_asset_spec(self, data: DltResourceTranslatorData) -> AssetSpec:
        table_name = data.resource.table_name
        if isinstance(table_name, Callable):
            table_name = data.resource.name
        prefix = [data.pipeline.dataset_name] if data.pipeline else []
        return super().get_asset_spec(data).replace_attributes(key=AssetKey(prefix + [table_name]))


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
                dagster_dlt_translator=ComponentDagsterDltTranslator(),
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
