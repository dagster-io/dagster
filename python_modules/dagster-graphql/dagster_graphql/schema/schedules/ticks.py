import graphene
from dagster._core.scheduler.instigation import TickStatus
from dagster._core.storage.dagster_run import RunsFilter

from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.instigation import GrapheneInstigationTickStatus


class GrapheneScheduleTickSuccessData(graphene.ObjectType):
    run = graphene.Field("dagster_graphql.schema.pipelines.pipeline.GrapheneRun")

    class Meta:
        name = "ScheduleTickSuccessData"


class GrapheneScheduleTickFailureData(graphene.ObjectType):
    error = graphene.NonNull(GraphenePythonError)

    class Meta:
        name = "ScheduleTickFailureData"


def tick_specific_data_from_dagster_tick(graphene_info, tick):
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun

    if tick.status == TickStatus.SUCCESS:
        if tick.run_ids and graphene_info.context.instance.has_run(tick.run_ids[0]):
            record = graphene_info.context.instance.get_run_records(
                RunsFilter(run_ids=[tick.run_ids[0]])
            )[0]
            return GrapheneScheduleTickSuccessData(run=GrapheneRun(record))
        return GrapheneScheduleTickSuccessData(run=None)
    elif tick.status == TickStatus.FAILURE:
        error = tick.error
        return GrapheneScheduleTickFailureData(error=GraphenePythonError(error))


class GrapheneScheduleTickSpecificData(graphene.Union):
    class Meta:
        types = (
            GrapheneScheduleTickSuccessData,
            GrapheneScheduleTickFailureData,
        )
        name = "ScheduleTickSpecificData"


class GrapheneScheduleTick(graphene.ObjectType):
    tick_id = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneInstigationTickStatus)
    timestamp = graphene.NonNull(graphene.Float)
    tick_specific_data = graphene.Field(GrapheneScheduleTickSpecificData)

    class Meta:
        name = "ScheduleTick"
