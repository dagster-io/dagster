'''Workhorse functions for individual API requests.'''

import sys

from dagster import check
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import DagsterInvalidSubsetError
from dagster.core.host_representation import external_pipeline_data_from_def
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.utils.error import serializable_error_info_from_exc_info


def get_external_pipeline_subset_result(recon_pipeline, solid_selection):
    check.inst_param(recon_pipeline, 'recon_pipeline', ReconstructablePipeline)

    if solid_selection:
        try:
            sub_pipeline = recon_pipeline.subset_for_execution(solid_selection)
            definition = sub_pipeline.get_definition()
        except DagsterInvalidSubsetError:
            return ExternalPipelineSubsetResult(
                success=False, error=serializable_error_info_from_exc_info(sys.exc_info())
            )
    else:
        definition = recon_pipeline.get_definition()

    external_pipeline_data = external_pipeline_data_from_def(definition)
    return ExternalPipelineSubsetResult(success=True, external_pipeline_data=external_pipeline_data)
