from dagster import check
from dagster.core.snap import PipelineSnapshot

from .pipeline_index import PipelineIndex
from .represented import RepresentedPipeline


class HistoricalPipeline(RepresentedPipeline):
    """
    HistoricalPipeline represents a pipeline that executed in the past
    and has been reloaded into process by quering the instance. Notably
    the user must pass in the pipeline snapshot id that was originally
    assigned to the snapshot, rather than recomputing it which could
    end up different if the schema of the snapshot has changed
    since persistence.
    """

    def __init__(
        self, pipeline_snapshot, identifying_pipeline_snapshot_id, parent_pipeline_snapshot
    ):
        check.inst_param(pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot)
        check.opt_inst_param(parent_pipeline_snapshot, "parent_pipeline_snapshot", PipelineSnapshot)
        self._identifying_pipeline_snapshot_id = check.str_param(
            identifying_pipeline_snapshot_id, "identifying_pipeline_snapshot_id"
        )
        super(HistoricalPipeline, self).__init__(
            pipeline_index=PipelineIndex(pipeline_snapshot, parent_pipeline_snapshot)
        )

    @property
    def identifying_pipeline_snapshot_id(self):
        return self._identifying_pipeline_snapshot_id

    @property
    def computed_pipeline_snapshot_id(self):
        return self._pipeline_index.pipeline_snapshot_id
