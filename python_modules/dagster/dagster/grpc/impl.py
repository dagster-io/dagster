'''Workhorse functions for individual API requests.'''

import sys

from dagster import check
from dagster.core.definitions import ScheduleExecutionContext
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import (
    DagsterInvalidSubsetError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.host_representation import external_pipeline_data_from_def
from dagster.core.host_representation.external_data import (
    ExternalPipelineSubsetResult,
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.instance import DagsterInstance
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import recon_repository_from_origin

from .types import ExternalScheduleExecutionArgs


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


def get_external_schedule_execution(external_schedule_execution_args):
    check.inst_param(
        external_schedule_execution_args,
        'external_schedule_execution_args',
        ExternalScheduleExecutionArgs,
    )

    recon_repo = recon_repository_from_origin(external_schedule_execution_args.repository_origin)
    definition = recon_repo.get_definition()
    schedule_def = definition.get_schedule_def(external_schedule_execution_args.schedule_name)
    instance = DagsterInstance.from_ref(external_schedule_execution_args.instance_ref)
    schedule_context = ScheduleExecutionContext(instance)
    try:
        with user_code_error_boundary(
            ScheduleExecutionError,
            lambda: 'Error occurred during the execution of run_config_fn for schedule '
            '{schedule_name}'.format(schedule_name=schedule_def.name),
        ):
            run_config = schedule_def.get_run_config(schedule_context)
            return ExternalScheduleExecutionData(run_config=run_config)
    except ScheduleExecutionError:
        return ExternalScheduleExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )
