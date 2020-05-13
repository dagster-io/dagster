'''
This subpackage contains all classes that host processes (e.g. dagit)
use to manipulate and represent definitions that are resident
in user processes and containers.  e.g. ExternalPipeline

It also contains classes that represent historical representations
that have been persisted. e.g. HistoricalPipeline
'''
from .external import ExternalPipeline, ExternalRepository
from .external_data import (
    ExternalPipelineData,
    ExternalPresetData,
    ExternalRepositoryData,
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
