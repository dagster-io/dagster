from dagster import check
from dagster.core.snap import PipelineSnapshot

from .pipeline_index import PipelineIndex
from .represented import RepresentedPipeline


class HistoricalPipeline(RepresentedPipeline):
    def __init__(self, pipeline_snapshot):
        check.inst_param(pipeline_snapshot, 'pipeline_snapshot', PipelineSnapshot)
        super(HistoricalPipeline, self).__init__(pipeline_index=PipelineIndex(pipeline_snapshot))
