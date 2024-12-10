import importlib
from typing import Any, Iterator, Mapping, Optional, Sequence

import dlt
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._record import record
from dagster_embedded_elt.dlt.asset_decorator import dlt_assets
from dagster_embedded_elt.dlt.resource import DagsterDltResource
from dlt.extract import DltSource
from dlt.pipeline import Pipeline
from pydantic import BaseModel, TypeAdapter

from dagster_components.core.component import (
    Component,
    ComponentDeclNode,
    ComponentLoadContext,
    component,
)
from dagster_components.core.component_decl_builder import YamlComponentDecl


@record
class DltPipelineRun:
    pipeline: Pipeline
    source: DltSource


class DltPipelineBaseModel(BaseModel):
    """Passed into `dlt.pipeline()` to create a pipeline."""

    pipeline_name: str
    dataset_name: str
    destination: str


class DltSourceBaseModel(BaseModel):
    """Pointer to a dlt source factory and the params to pass to it."""

    source_reference: str
    params: Optional[Mapping[str, Any]] = None


class DltPipelineRunSpecBaseModel(BaseModel):
    """Holds configuration for a dlt pipeline run."""

    pipeline: DltPipelineBaseModel
    source: DltSourceBaseModel


class DltPipelineCollectionParamsSchema(BaseModel):
    pipeline_runs: Sequence[DltPipelineRunSpecBaseModel]


def _get_source(source_reference: str, params: Mapping[str, Any]) -> DltSource:
    source_module, source_factory = source_reference.rsplit(".", 1)
    source_module = importlib.import_module(source_module)
    source_factory = getattr(source_module, source_factory)
    return source_factory(**(params or {}))


@component(name="dlt_pipeline_collection")
class DltPipelineCollection(Component):
    params_schema = DltPipelineCollectionParamsSchema

    def __init__(self, pipeline_runs: Sequence[DltPipelineRun]):
        self.pipeline_runs = pipeline_runs

    @classmethod
    def from_decl_node(
        cls, context: ComponentLoadContext, decl_node: ComponentDeclNode
    ) -> "DltPipelineCollection":
        assert isinstance(decl_node, YamlComponentDecl)
        loaded_params = TypeAdapter(cls.params_schema).validate_python(
            decl_node.component_file_model.params
        )

        pipeline_runs = []
        for pipeline_run_spec in loaded_params.pipeline_runs:
            pipeline = dlt.pipeline(**pipeline_run_spec.pipeline.model_dump())
            source = _get_source(
                pipeline_run_spec.source.source_reference, pipeline_run_spec.source.params or {}
            )
            pipeline_runs.append(DltPipelineRun(pipeline=pipeline, source=source))

        return cls(pipeline_runs=pipeline_runs)

    def build_defs(self, load_context: "ComponentLoadContext") -> "Definitions":
        return Definitions(
            assets=[self._create_asset_def(pipeline_run) for pipeline_run in self.pipeline_runs]
        )

    def _create_asset_def(self, pipeline_run: DltPipelineRun) -> AssetsDefinition:
        source = pipeline_run.source
        pipeline = pipeline_run.pipeline

        @dlt_assets(dlt_source=source, dlt_pipeline=pipeline)
        def _asset(context: AssetExecutionContext):
            yield from self.execute(context, dlt=DagsterDltResource())

        return _asset

    def execute(self, context: AssetExecutionContext, dlt: DagsterDltResource) -> Iterator:
        yield from dlt.run(context)
