import graphene
from dagster.core.scheduler.job import JobTickStatus

from ..errors import GraphenePythonError
from ..jobs import GrapheneJobTickStatus


class GrapheneScheduleTickSuccessData(graphene.ObjectType):
    run = graphene.Field("dagster_graphql.schema.pipelines.pipeline.GraphenePipelineRun")

    class Meta:
        name = "ScheduleTickSuccessData"


class GrapheneScheduleTickFailureData(graphene.ObjectType):
    error = graphene.NonNull(GraphenePythonError)

    class Meta:
        name = "ScheduleTickFailureData"


def tick_specific_data_from_dagster_tick(graphene_info, tick):
    from ..pipelines.pipeline import GraphenePipelineRun

    if tick.status == JobTickStatus.SUCCESS:
        if tick.run_ids and graphene_info.context.instance.has_run(tick.run_ids[0]):
            return GrapheneScheduleTickSuccessData(
                run=GraphenePipelineRun(
                    graphene_info.context.instance.get_run_by_id(tick.run_ids[0])
                )
            )
        return GrapheneScheduleTickSuccessData(run=None)
    elif tick.status == JobTickStatus.FAILURE:
        error = tick.error
        return GrapheneScheduleTickFailureData(error=error)


class GrapheneScheduleTickSpecificData(graphene.Union):
    class Meta:
        types = (
            GrapheneScheduleTickSuccessData,
            GrapheneScheduleTickFailureData,
        )
        name = "ScheduleTickSpecificData"


class GrapheneScheduleTick(graphene.ObjectType):
    tick_id = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneJobTickStatus)
    timestamp = graphene.NonNull(graphene.Float)
    tick_specific_data = graphene.Field(GrapheneScheduleTickSpecificData)

    class Meta:
        name = "ScheduleTick"
