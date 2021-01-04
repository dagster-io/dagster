from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.scheduler.job import JobStatus

from .utils import capture_dauphin_error


@capture_dauphin_error
def get_unloadable_job_states_or_error(graphene_info, job_type=None):
    check.opt_inst_param(job_type, "job_type", JobType)
    job_states = graphene_info.context.instance.all_stored_job_state(job_type=job_type)
    external_jobs = [
        job
        for repository_location in graphene_info.context.repository_locations
        for repository in repository_location.get_repositories().values()
        for job in repository.get_external_schedules() + repository.get_external_sensors()
    ]

    job_origin_ids = {job.get_external_origin_id() for job in external_jobs}

    unloadable_states = [
        job_state
        for job_state in job_states
        if job_state.job_origin_id not in job_origin_ids and job_state.status == JobStatus.RUNNING
    ]

    return graphene_info.schema.type_named("JobStates")(
        results=[
            graphene_info.schema.type_named("JobState")(job_state=job_state)
            for job_state in unloadable_states
        ]
    )
