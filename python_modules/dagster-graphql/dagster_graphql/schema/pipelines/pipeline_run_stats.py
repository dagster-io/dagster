import dagster._check as check
import graphene
from dagster._core.storage.dagster_run import DagsterRunStatsSnapshot

from dagster_graphql.schema.errors import GraphenePythonError


class GraphenePipelineRunStatsSnapshot(graphene.Interface):
    id = graphene.NonNull(graphene.String)
    runId = graphene.NonNull(graphene.String)
    stepsSucceeded = graphene.NonNull(
        graphene.Int
    )  # Can you really have a pipeline with so many steps that you need a BigInt?
    stepsFailed = graphene.NonNull(graphene.Int)  # Same
    materializations = graphene.NonNull(graphene.Int)  # Same
    expectations = graphene.NonNull(graphene.Int)  # Same
    enqueuedTime = graphene.Field(graphene.Float)
    launchTime = graphene.Field(graphene.Float)
    startTime = graphene.Field(graphene.Float)
    endTime = graphene.Field(graphene.Float)

    class Meta:
        name = "PipelineRunStatsSnapshot"


class GrapheneRunStatsSnapshot(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    runId = graphene.NonNull(graphene.String)
    stepsSucceeded = graphene.NonNull(graphene.Int)  # Same
    stepsFailed = graphene.NonNull(graphene.Int)  # Same
    materializations = graphene.NonNull(graphene.Int)  # Same
    expectations = graphene.NonNull(graphene.Int)  # Same
    enqueuedTime = graphene.Field(graphene.Float)
    launchTime = graphene.Field(graphene.Float)
    startTime = graphene.Field(graphene.Float)
    endTime = graphene.Field(graphene.Float)

    class Meta:
        interfaces = (GraphenePipelineRunStatsSnapshot,)
        name = "RunStatsSnapshot"

    def __init__(self, stats):
        self._stats = check.inst_param(stats, "stats", DagsterRunStatsSnapshot)
        super().__init__(
            id="stats-" + self._stats.run_id,
            runId=self._stats.run_id,
            stepsSucceeded=self._stats.steps_succeeded,
            stepsFailed=self._stats.steps_failed,
            materializations=self._stats.materializations,
            expectations=self._stats.expectations,
            enqueuedTime=stats.enqueued_time,
            launchTime=stats.launch_time,
            startTime=self._stats.start_time,
            endTime=self._stats.end_time,
        )


class GrapheneRunStatsSnapshotOrError(graphene.Union):
    class Meta:
        types = (GrapheneRunStatsSnapshot, GraphenePythonError)
        name = "RunStatsSnapshotOrError"
