import dagster._check as check
import graphene
from dagster._core.remote_representation import RepresentedJob

from dagster_graphql.schema.errors import (
    GraphenePipelineNotFoundError,
    GraphenePipelineSnapshotNotFoundError,
    GraphenePythonError,
)
from dagster_graphql.schema.pipelines.pipeline import (
    GrapheneIPipelineSnapshot,
    GrapheneIPipelineSnapshotMixin,
)
from dagster_graphql.schema.pipelines.pipeline_ref import GraphenePipelineReference
from dagster_graphql.schema.solids import GrapheneSolidContainer


class GraphenePipelineSnapshot(GrapheneIPipelineSnapshotMixin, graphene.ObjectType):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
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
