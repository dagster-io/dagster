from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.errors import DagsterBackfillFailedError
from dagster.core.execution.plan.resume_retry import get_retry_steps_from_execution_plan
from dagster.core.host_representation import (
    ExternalPartitionSet,
    ExternalPipeline,
    RepositoryLocation,
)
from dagster.core.host_representation.external_data import (
    ExternalPartitionExecutionErrorData,
    ExternalPartitionExecutionParamData,
    ExternalPartitionSetExecutionParamData,
)
from dagster.core.host_representation.origin import ExternalPartitionSetOrigin
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG, PARTITION_SET_TAG, RESUME_RETRY_TAG
from dagster.core.utils import make_new_run_id
from dagster.serdes import whitelist_for_serdes
from dagster.utils import merge_dicts
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class BulkActionStatus(Enum):
    REQUESTED = "REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@whitelist_for_serdes
class PartitionBackfill(
    namedtuple(
        "_PartitionBackfill",
        (
            "backfill_id partition_set_origin status partition_names from_failure "
            "reexecution_steps tags backfill_timestamp last_submitted_partition_name error"
        ),
    ),
):
    def __new__(
        cls,
        backfill_id,
        partition_set_origin,
        status,
        partition_names,
        from_failure,
        reexecution_steps,
        tags,
        backfill_timestamp,
        last_submitted_partition_name=None,
        error=None,
    ):
        return super(PartitionBackfill, cls).__new__(
            cls,
            check.str_param(backfill_id, "backfill_id"),
            check.inst_param(
                partition_set_origin, "partition_set_origin", ExternalPartitionSetOrigin
            ),
            check.inst_param(status, "status", BulkActionStatus),
            check.list_param(partition_names, "partition_names", of_type=str),
            check.bool_param(from_failure, "from_failure"),
            check.opt_list_param(reexecution_steps, "reexecution_steps", of_type=str),
            check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
            check.float_param(backfill_timestamp, "backfill_timestamp"),
            check.opt_str_param(last_submitted_partition_name, "last_submitted_partition_name"),
            check.opt_inst_param(error, "error", SerializableErrorInfo),
        )

    def with_status(self, status):
        check.inst_param(status, "status", BulkActionStatus)
        return PartitionBackfill(
            self.backfill_id,
            self.partition_set_origin,
            status,
            self.partition_names,
            self.from_failure,
            self.reexecution_steps,
            self.tags,
            self.backfill_timestamp,
            self.last_submitted_partition_name,
            self.error,
        )

    def with_partition_checkpoint(self, last_submitted_partition_name):
        check.str_param(last_submitted_partition_name, "last_submitted_partition_name")
        return PartitionBackfill(
            self.backfill_id,
            self.partition_set_origin,
            self.status,
            self.partition_names,
            self.from_failure,
            self.reexecution_steps,
            self.tags,
            self.backfill_timestamp,
            last_submitted_partition_name,
            self.error,
        )

    def with_error(self, error):
        check.opt_inst_param(error, "error", SerializableErrorInfo)
        return PartitionBackfill(
            self.backfill_id,
            self.partition_set_origin,
            self.status,
            self.partition_names,
            self.from_failure,
            self.reexecution_steps,
            self.tags,
            self.backfill_timestamp,
            self.last_submitted_partition_name,
            error,
        )


def submit_backfill_runs(instance, repo_location, backfill_job, partition_names=None):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(repo_location, "repo_location", RepositoryLocation)
    check.inst_param(backfill_job, "backfill_job", PartitionBackfill)

    repository_origin = backfill_job.partition_set_origin.external_repository_origin
    repo_name = repository_origin.repository_name

    if not partition_names:
        partition_names = backfill_job.partition_names

    check.invariant(
        repo_location.has_repository(repo_name),
        "Could not find repository {repo_name} in location {repo_location_name}".format(
            repo_name=repo_name, repo_location_name=repo_location.name
        ),
    )
    external_repo = repo_location.get_repository(repo_name)
    partition_set_name = backfill_job.partition_set_origin.partition_set_name
    external_partition_set = external_repo.get_external_partition_set(partition_set_name)
    result = repo_location.get_external_partition_set_execution_param_data(
        external_repo.handle, partition_set_name, partition_names
    )
    if isinstance(result, ExternalPartitionExecutionErrorData):
        raise DagsterBackfillFailedError(serializable_error_info=result.error)

    assert isinstance(result, ExternalPartitionSetExecutionParamData)
    external_pipeline = external_repo.get_full_external_pipeline(
        external_partition_set.pipeline_name
    )
    submitted = []
    for partition_data in result.partition_data:
        pipeline_run = create_backfill_run(
            instance,
            repo_location,
            external_pipeline,
            external_partition_set,
            backfill_job,
            partition_data,
        )
        if pipeline_run:
            # we skip runs in certain cases, e.g. we are running a `from_failure` backfill job
            # and the partition has had a successful run since the time the backfill was
            # scheduled
            instance.submit_run(pipeline_run.run_id, external_pipeline)
            submitted.append(pipeline_run.run_id)
    return submitted


def create_backfill_run(
    instance, repo_location, external_pipeline, external_partition_set, backfill_job, partition_data
):
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(repo_location, "repo_location", RepositoryLocation)
    check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
    check.inst_param(external_partition_set, "external_partition_set", ExternalPartitionSet)
    check.inst_param(backfill_job, "backfill_job", PartitionBackfill)
    check.inst_param(partition_data, "partition_data", ExternalPartitionExecutionParamData)

    # potentially wrap this so we don't waste resources if plan is bad
    full_external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline,
        partition_data.run_config,
        external_partition_set.mode,
        step_keys_to_execute=None,
    )

    tags = merge_dicts(
        external_pipeline.tags,
        partition_data.tags,
        PipelineRun.tags_for_backfill_id(backfill_job.backfill_id),
        backfill_job.tags,
    )

    if not backfill_job.from_failure and not backfill_job.reexecution_steps:
        step_keys_to_execute = None
        parent_run_id = None
        root_run_id = None

    elif backfill_job.from_failure:
        last_run = _fetch_last_run(instance, external_partition_set, partition_data.name)
        if not last_run or last_run.status != PipelineRunStatus.FAILURE:
            return None

        parent_run_id = last_run.run_id
        root_run_id = last_run.root_run_id or last_run.run_id
        tags = merge_dicts(tags, {RESUME_RETRY_TAG: "true"})
        step_keys_to_execute = get_retry_steps_from_execution_plan(
            instance, full_external_execution_plan, parent_run_id
        )
    elif backfill_job.reexecution_steps:
        last_run = _fetch_last_run(instance, external_partition_set, partition_data.name)
        parent_run_id = last_run.run_id if last_run else None
        root_run_id = (last_run.root_run_id or last_run.run_id) if last_run else None
        step_keys_to_execute = backfill_job.reexecution_steps

    if step_keys_to_execute:
        external_execution_plan = repo_location.get_external_execution_plan(
            external_pipeline,
            partition_data.run_config,
            external_partition_set.mode,
            step_keys_to_execute=step_keys_to_execute,
        )
    else:
        external_execution_plan = full_external_execution_plan

    return instance.create_run(
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        pipeline_name=external_pipeline.name,
        run_id=make_new_run_id(),
        solids_to_execute=frozenset(external_partition_set.solid_selection)
        if external_partition_set.solid_selection
        else None,
        run_config=partition_data.run_config,
        mode=external_partition_set.mode,
        step_keys_to_execute=step_keys_to_execute,
        tags=tags,
        root_run_id=root_run_id,
        parent_run_id=parent_run_id,
        status=PipelineRunStatus.NOT_STARTED,
        external_pipeline_origin=external_pipeline.get_external_origin(),
    )


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

    return runs[0] if runs else None
