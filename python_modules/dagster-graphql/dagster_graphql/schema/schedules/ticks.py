from dagster.core.scheduler.job import JobTickStatus


def tick_specific_data_from_dagster_tick(graphene_info, tick):
    if tick.status == JobTickStatus.SUCCESS:
        if tick.run_ids and graphene_info.context.instance.has_run(tick.run_ids[0]):
            return graphene_info.schema.type_named("ScheduleTickSuccessData")(
                run=graphene_info.schema.type_named("PipelineRun")(
                    graphene_info.context.instance.get_run_by_id(tick.run_ids[0])
                )
            )
        return graphene_info.schema.type_named("ScheduleTickSuccessData")(run=None)
    elif tick.status == JobTickStatus.FAILURE:
        error = tick.error
        return graphene_info.schema.type_named("ScheduleTickFailureData")(error=error)
