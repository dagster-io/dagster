import graphene
from dagster import check
from dagster.core.storage.dagster_run import DagsterRunStatsSnapshot

from ..errors import GraphenePythonError


class GrapheneDagsterRunStatsSnapshot(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    runId = graphene.NonNull(graphene.String)
    stepsSucceeded = graphene.NonNull(graphene.Int)
    stepsFailed = graphene.NonNull(graphene.Int)
    materializations = graphene.NonNull(graphene.Int)
    expectations = graphene.NonNull(graphene.Int)
    enqueuedTime = graphene.Field(graphene.Float)
    launchTime = graphene.Field(graphene.Float)
    startTime = graphene.Field(graphene.Float)
    endTime = graphene.Field(graphene.Float)

    class Meta:
        name = "DagsterRunStatsSnapshot"

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


class GrapheneDagsterRunStatsOrError(graphene.Union):
    class Meta:
        types = (GrapheneDagsterRunStatsSnapshot, GraphenePythonError)
        name = "DagsterRunStatsOrError"
