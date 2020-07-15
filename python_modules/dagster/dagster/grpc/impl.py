'''Workhorse functions for individual API requests.'''

import sys

from dagster import check
from dagster.core.definitions import ScheduleExecutionContext
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import (
    DagsterInvalidSubsetError,
    PartitionExecutionError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.host_representation import external_pipeline_data_from_def
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionTagsData,
    ExternalPipelineSubsetResult,
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.instance import DagsterInstance
from dagster.grpc.types import ExternalScheduleExecutionArgs, PartitionArgs, PartitionNamesArgs
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


def get_partition_config(args):
    check.inst_param(args, 'args', PartitionArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    partition = partition_set_def.get_partition(args.partition_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: 'Error occurred during the evaluation of the `run_config_for_partition` '
            'function for partition set {partition_set_name}'.format(
                partition_set_name=partition_set_def.name
            ),
        ):
            run_config = partition_set_def.run_config_for_partition(partition)
            return ExternalPartitionConfigData(name=partition.name, run_config=run_config)
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_names(args):
    check.inst_param(args, 'args', PartitionNamesArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: 'Error occurred during the execution of the partition generation function for '
            'partition set {partition_set_name}'.format(partition_set_name=partition_set_def.name),
        ):
            return ExternalPartitionNamesData(
                partition_names=partition_set_def.get_partition_names()
            )
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_tags(args):
    check.inst_param(args, 'args', PartitionArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    partition = partition_set_def.get_partition(args.partition_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: 'Error occurred during the evaluation of the `tags_for_partition` function for '
            'partition set {partition_set_name}'.format(partition_set_name=partition_set_def.name),
        ):
            tags = partition_set_def.tags_for_partition(partition)
            return ExternalPartitionTagsData(name=partition.name, tags=tags)
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )
