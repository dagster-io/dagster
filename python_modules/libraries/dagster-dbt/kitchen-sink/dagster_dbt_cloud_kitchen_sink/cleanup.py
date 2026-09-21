import logging
import time
from collections.abc import Sequence

from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient

from dagster_dbt_cloud_kitchen_sink.resources import parse_adhoc_job_created_at

# Generous enough that a slow-but-live build is never swept out from under itself;
# the live suite runs well under an hour.
ORPHANED_ADHOC_JOB_MAX_AGE_SECONDS = 4 * 60 * 60

logger = logging.getLogger(__name__)


def _destroy_jobs(client: DbtCloudWorkspaceClient, job_ids: Sequence[int]) -> Sequence[int]:
    """Delete each job, keeping going if one fails.

    Two runs can pick the same orphan to reclaim, so losing the race and getting a 404
    is expected — the job being gone is the outcome we wanted. Failing one deletion must
    not strand the rest.

    Returns:
        The IDs actually deleted by this call.
    """
    destroyed_job_ids = []
    for job_id in job_ids:
        try:
            client.destroy_job(job_id=job_id)
        except Exception:
            logger.warning(f"Could not destroy dbt Cloud job {job_id}.", exc_info=True)
        else:
            destroyed_job_ids.append(job_id)
    return destroyed_job_ids


def destroy_adhoc_jobs_in_namespace(
    client: DbtCloudWorkspaceClient,
    *,
    project_id: int,
    environment_id: int,
    namespace: str,
) -> Sequence[int]:
    """Delete the ad hoc jobs owned by this run, leaving concurrent builds' jobs alone.

    Matches on prefix rather than equality so pooled jobs (``{namespace}__{index}``)
    are covered too.

    Returns:
        The IDs of the jobs that were deleted.
    """
    return _destroy_jobs(
        client,
        [
            job["id"]
            for job in client.list_jobs(project_id=project_id, environment_id=environment_id)
            if (job.get("name") or "").startswith(namespace)
        ],
    )


def sweep_orphaned_adhoc_jobs(
    client: DbtCloudWorkspaceClient,
    *,
    project_id: int,
    environment_id: int,
    max_age_seconds: int = ORPHANED_ADHOC_JOB_MAX_AGE_SECONDS,
    now: float | None = None,
) -> Sequence[int]:
    """Delete CI ad hoc jobs left behind by builds that died before their teardown ran.

    Only jobs whose name carries a CI namespace older than ``max_age_seconds`` are
    touched, so a build in flight is never affected.

    Returns:
        The IDs of the jobs that were deleted.
    """
    cutoff = (now if now is not None else time.time()) - max_age_seconds
    orphaned_job_ids = []
    for job in client.list_jobs(project_id=project_id, environment_id=environment_id):
        created_at = parse_adhoc_job_created_at(job.get("name") or "")
        if created_at is not None and created_at < cutoff:
            orphaned_job_ids.append(job["id"])
    return _destroy_jobs(client, orphaned_job_ids)
