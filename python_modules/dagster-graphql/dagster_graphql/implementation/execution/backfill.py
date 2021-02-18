from dagster import check
from dagster.core.host_representation import RepositorySelector
from dagster.core.host_representation.external import ExternalPartitionSet
from dagster.core.host_representation.external_data import (
    ExternalPartitionExecutionErrorData,
    ExternalPartitionExecutionParamData,
    ExternalPartitionSetExecutionParamData,
)
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG, PARTITION_SET_TAG, RESUME_RETRY_TAG
from dagster.core.utils import make_new_backfill_id
from dagster.utils import merge_dicts

from ..utils import ExecutionMetadata, ExecutionParams, capture_error
from .run_lifecycle import create_valid_pipeline_run


@capture_error
def create_and_launch_partition_backfill(graphene_info, backfill_params):
    from ...schema.backfill import GraphenePartitionBackfillSuccess
    from ...schema.errors import GraphenePartitionSetNotFoundError, GraphenePythonError

    partition_set_selector = backfill_params.get("selector")
    partition_set_name = partition_set_selector.get("partitionSetName")
    repository_selector = RepositorySelector.from_graphql_input(
        partition_set_selector.get("repositorySelector")
    )
    location = graphene_info.context.get_repository_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    matches = [
        partition_set
        for partition_set in repository.get_external_partition_sets()
        if partition_set.name == partition_set_selector.get("partitionSetName")
    ]
    if not matches:
        return GraphenePartitionSetNotFoundError(partition_set_name)

    check.invariant(
        len(matches) == 1,
        "Partition set names must be unique: found {num} matches for {partition_set_name}".format(
            num=len(matches), partition_set_name=partition_set_name
        ),
    )

    external_partition_set = next(iter(matches))
    external_pipeline = repository.get_full_external_pipeline(external_partition_set.pipeline_name)
    pipeline_selector = PipelineSelector(
        location_name=location.name,
        repository_name=repository.name,
        pipeline_name=external_pipeline.name,
        solid_selection=external_partition_set.solid_selection,
    )

    partition_names = backfill_params.get("partitionNames")

    backfill_id = make_new_backfill_id()
    result = graphene_info.context.get_external_partition_set_execution_param_data(
        repository.handle, partition_set_name, partition_names
    )

    if isinstance(result, ExternalPartitionExecutionErrorData):
        return GraphenePythonError(result.error)

    assert isinstance(result, ExternalPartitionSetExecutionParamData)

    launched_run_ids = []
    execution_param_list = _build_execution_param_list_for_backfill(
        graphene_info.context.instance,
        result.partition_data,
        backfill_id,
        backfill_params,
        pipeline_selector,
        external_partition_set,
    )

    for execution_params in execution_param_list:
        pipeline_run = create_valid_pipeline_run(graphene_info, external_pipeline, execution_params)
        graphene_info.context.instance.submit_run(pipeline_run.run_id, external_pipeline)
        launched_run_ids.append(pipeline_run.run_id)

    return GraphenePartitionBackfillSuccess(
        backfill_id=backfill_id, launched_run_ids=launched_run_ids
    )


def _build_execution_param_list_for_backfill(
    instance,
    partition_data_list,
    backfill_id,
    backfill_params,
    pipeline_selector,
    external_partition_set,
):
    check.inst_param(instance, "instance", DagsterInstance)
    check.list_param(
        partition_data_list, "partition_data_list", of_type=ExternalPartitionExecutionParamData
    )
    check.str_param(backfill_id, "backfill_id")
    check.dict_param(backfill_params, "backfill_params")
    check.inst_param(pipeline_selector, "pipeline_selector", PipelineSelector)
    check.inst_param(external_partition_set, "external_partition_set", ExternalPartitionSet)

    backfill_tags = PipelineRun.tags_for_backfill_id(backfill_id)
    execution_tags = {t["key"]: t["value"] for t in backfill_params.get("tags", [])}
    execution_param_list = []
    for partition_data in partition_data_list:
        tags = merge_dicts(merge_dicts(partition_data.tags, backfill_tags), execution_tags)
        if not backfill_params.get("fromFailure") and not backfill_params.get("reexecutionSteps"):
            # full pipeline execution
            execution_param_list.append(
                ExecutionParams(
                    selector=pipeline_selector,
                    run_config=partition_data.run_config,
                    mode=external_partition_set.mode,
                    execution_metadata=ExecutionMetadata(run_id=None, tags=tags),
                    step_keys=None,
                )
            )
            continue

        last_run = _fetch_last_run(instance, external_partition_set, partition_data.name)

        if backfill_params.get("fromFailure"):
            if not last_run or last_run.status != PipelineRunStatus.FAILURE:
                continue

            execution_param_list.append(
                ExecutionParams(
                    selector=pipeline_selector,
                    run_config=partition_data.run_config,
                    mode=external_partition_set.mode,
                    execution_metadata=ExecutionMetadata(
                        run_id=None,
                        tags=merge_dicts(tags, {RESUME_RETRY_TAG: "true"}),
                        root_run_id=last_run.root_run_id or last_run.run_id,
                        parent_run_id=last_run.run_id,
                    ),
                    step_keys=None,
                )
            )
            continue

        if last_run:
            root_run_id = last_run.root_run_id or last_run.run_id
            parent_run_id = last_run.run_id
        else:
            root_run_id = None
            parent_run_id = None

        execution_param_list.append(
            ExecutionParams(
                selector=pipeline_selector,
                run_config=partition_data.run_config,
                mode=external_partition_set.mode,
                execution_metadata=ExecutionMetadata(
                    run_id=None,
                    tags=tags,
                    root_run_id=root_run_id,
                    parent_run_id=parent_run_id,
                ),
                step_keys=backfill_params["reexecutionSteps"],
            )
        )
        continue

    return execution_param_list


def _fetch_last_run(instance, external_partition_set, partition_name):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(external_partition_set, "external_partition_set", ExternalPartitionSet)
    check.str_param(partition_name, "partition_name")

    runs = instance.get_runs(
        PipelineRunsFilter(
            pipeline_name=external_partition_set.pipeline_name,
            tags={
                PARTITION_SET_TAG: external_partition_set.name,
                PARTITION_NAME_TAG: partition_name,
            },
        ),
        limit=1,
    )

    if len(runs) == 0:
        return None

    return runs[0]
