import dagster._check as check
import graphene
from dagster._core.host_representation import RepresentedJob

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

    def __init__(self, represented_job: RepresentedJob):
        super().__init__()
        self._represented_job = check.inst_param(
            represented_job, "represented_pipeline", RepresentedJob
        )

    def get_represented_job(self) -> RepresentedJob:
        return self._represented_job


class GraphenePipelineSnapshotOrError(graphene.Union):
    class Meta:
        types = (
            GraphenePipelineNotFoundError,
            GraphenePipelineSnapshot,
            GraphenePipelineSnapshotNotFoundError,
            GraphenePythonError,
        )
        name = "PipelineSnapshotOrError"
