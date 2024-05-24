from typing import Optional

import dagster._check as check
from dagster._core.snap import JobSnapshot

from .job_index import JobIndex
from .represented import RepresentedJob


class HistoricalJob(RepresentedJob):
    """HistoricalPipeline represents a pipeline that executed in the past
    and has been reloaded into process by querying the instance. Notably
    the user must pass in the pipeline snapshot id that was originally
    assigned to the snapshot, rather than recomputing it which could
    end up different if the schema of the snapshot has changed
    since persistence.
    """

    def __init__(
        self,
        job_snapshot: JobSnapshot,
        identifying_job_snapshot_id: str,
        parent_job_snapshot: Optional[JobSnapshot],
    ):
        self._snapshot = check.inst_param(job_snapshot, "job_snapshot", JobSnapshot)
        self._parent_snapshot = check.opt_inst_param(
            parent_job_snapshot, "parent_job_snapshot", JobSnapshot
        )
        self._identifying_job_snapshot_id = check.str_param(
            identifying_job_snapshot_id, "identifying_job_snapshot_id"
        )
        self._index = None

    @property
    def _job_index(self):
        if self._index is None:
            self._index = JobIndex(
                self._snapshot,
                self._parent_snapshot,
            )
        return self._index

    @property
    def identifying_job_snapshot_id(self):
        return self._identifying_job_snapshot_id

    @property
    def computed_job_snapshot_id(self):
        return self._job_index.job_snapshot_id
