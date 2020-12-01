from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.scheduler.job import JobStatus, JobTick, JobTickStatus
from dagster_graphql import dauphin


class DauphinJobTick(dauphin.ObjectType):
    class Meta:
        name = "JobTick"

    id = dauphin.NonNull(dauphin.ID)
    status = dauphin.NonNull("JobTickStatus")
    timestamp = dauphin.NonNull(dauphin.Float)
    runIds = dauphin.non_null_list(dauphin.String)
    error = dauphin.Field("PythonError")

    run = dauphin.non_null_list("PipelineRun")

    def __init__(self, _, job_tick):
        self._job_tick = check.inst_param(job_tick, "job_tick", JobTick)

        super(DauphinJobTick, self).__init__(
            status=job_tick.status,
            timestamp=job_tick.timestamp,
            runIds=job_tick.run_ids,
            error=job_tick.error,
        )

    def resolve_id(self, _):
        return "%s:%s" % (self._job_tick.job_origin_id, self._job_tick.timestamp)

    def resolve_runs(self, graphene_info):
        instance = graphene_info.context.instance
        return [
            graphene_info.schema.type_named("PipelineRun")(instance.get_run_by_id(run_id))
            for run_id in self._job_tick.run_ids
            if instance.has_run(run_id)
        ]


DauphinJobType = dauphin.Enum.from_enum(JobType)
DauphinJobStatus = dauphin.Enum.from_enum(JobStatus)
DauphinJobTickStatus = dauphin.Enum.from_enum(JobTickStatus)
