from dagster.core.scheduler import ScheduleTickStatus


def tick_specific_data_from_dagster_tick(graphene_info, tick):
    if tick.status == ScheduleTickStatus.SUCCESS:
        run_id = tick.run_id
        run = None
        if graphene_info.context.instance.has_run(run_id):
            run = graphene_info.schema.type_named("PipelineRun")(
                graphene_info.context.instance.get_run_by_id(run_id)
            )
        return graphene_info.schema.type_named("ScheduleTickSuccessData")(run=run)
    elif tick.status == ScheduleTickStatus.FAILURE:
        error = tick.error
        return graphene_info.schema.type_named("ScheduleTickFailureData")(error=error)
