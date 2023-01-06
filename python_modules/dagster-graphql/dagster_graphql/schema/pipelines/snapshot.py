import dagster._check as check
import graphene
from dagster._core.host_representation import RepresentedPipeline

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

    def __init__(self, represented_pipeline):
        super().__init__()
        self._represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )

    def get_represented_pipeline(self):
        return self._represented_pipeline


class GraphenePipelineSnapshotOrError(graphene.Union):
    class Meta:
        types = (
            GraphenePipelineNotFoundError,
            GraphenePipelineSnapshot,
            GraphenePipelineSnapshotNotFoundError,
            GraphenePythonError,
        )
        name = "PipelineSnapshotOrError"
