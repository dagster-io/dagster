from typing import Optional

import dagster._check as check
from dagster._core.snap import PipelineSnapshot

from .pipeline_index import PipelineIndex
from .represented import RepresentedPipeline


class HistoricalPipeline(RepresentedPipeline):
    """
    HistoricalPipeline represents a pipeline that executed in the past
    and has been reloaded into process by querying the instance. Notably
    the user must pass in the pipeline snapshot id that was originally
    assigned to the snapshot, rather than recomputing it which could
    end up different if the schema of the snapshot has changed
    since persistence.
    """

    def __init__(
        self,
        pipeline_snapshot: PipelineSnapshot,
        identifying_pipeline_snapshot_id: str,
        parent_pipeline_snapshot: Optional[PipelineSnapshot],
    ):
        self._snapshot = check.inst_param(pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot)
        self._parent_snapshot = check.opt_inst_param(
            parent_pipeline_snapshot, "parent_pipeline_snapshot", PipelineSnapshot
        )
        self._identifying_pipeline_snapshot_id = check.str_param(
            identifying_pipeline_snapshot_id, "identifying_pipeline_snapshot_id"
        )
        self._index = None

    @property
    def _pipeline_index(self):
        if self._index is None:
            self._index = PipelineIndex(
                self._snapshot,
                self._parent_snapshot,
            )
        return self._index

    @property
    def identifying_pipeline_snapshot_id(self):
        return self._identifying_pipeline_snapshot_id

    @property
    def computed_pipeline_snapshot_id(self):
        return self._pipeline_index.pipeline_snapshot_id
