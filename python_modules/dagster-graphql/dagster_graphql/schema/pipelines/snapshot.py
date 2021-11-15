import graphene
from dagster import check
from dagster.core.host_representation import RepresentedPipeline, ExternalRepository

from ..errors import (
    GraphenePipelineNotFoundError,
    GraphenePipelineSnapshotNotFoundError,
    GraphenePythonError,
)
from ..solids import GrapheneSolidContainer
from .pipeline import GrapheneIPipelineSnapshot, GrapheneIPipelineSnapshotMixin
from .pipeline_ref import GraphenePipelineReference


class GraphenePipelineSnapshot(GrapheneIPipelineSnapshotMixin, graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneSolidContainer, GrapheneIPipelineSnapshot, GraphenePipelineReference)
        name = "PipelineSnapshot"

    def __init__(self, represented_pipeline, external_repository=None):
        super().__init__()
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )
        self._external_repository = check.opt_inst_param(
            external_repository, "external_repository", ExternalRepository
        )

    def get_represented_pipeline(self):
        return self._represented_pipeline

    def get_external_repository(self):
        raise self._external_repository


class GraphenePipelineSnapshotOrError(graphene.Union):
    class Meta:
        types = (
            GraphenePipelineNotFoundError,
            GraphenePipelineSnapshot,
            GraphenePipelineSnapshotNotFoundError,
            GraphenePythonError,
        )
        name = "PipelineSnapshotOrError"
