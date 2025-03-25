from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING, AbstractSet, Optional, Union  # noqa: UP035

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.selector import RepositorySelector
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.remote_representation import RemotePartitionSet, RepositoryHandle
from dagster._core.remote_representation.external_data import PartitionExecutionErrorSnap
from dagster._core.storage.dagster_run import DagsterRunStatus, RunPartitionData, RunsFilter
from dagster._core.storage.tags import (
    PARTITION_NAME_TAG,
    PARTITION_SET_TAG,
    REPOSITORY_LABEL_TAG,
    TagType,
    get_tag_type,
)
from dagster_shared.yaml_utils import dump_run_config_yaml

from dagster_graphql.implementation.utils import apply_cursor_limit_reverse
from dagster_graphql.schema.util import ResolveInfo

if TYPE_CHECKING:
    from dagster_graphql.schema.errors import GraphenePartitionSetNotFoundError
    from dagster_graphql.schema.partition_sets import (
        GraphenePartition,
        GraphenePartitionRun,
        GraphenePartitionRunConfig,
        GraphenePartitions,
        GraphenePartitionSet,
        GraphenePartitionSets,
        GraphenePartitionStatus,
        GraphenePartitionStatusCounts,
        GraphenePartitionTags,
    )


def get_partition_sets_or_error(
    graphene_info: ResolveInfo, repository_selector: RepositorySelector, pipeline_name: str
) -> "GraphenePartitionSets":
    from dagster_graphql.schema.partition_sets import GraphenePartitionSet, GraphenePartitionSets

    check.inst_param(repository_selector, "repository_selector", RepositorySelector)
    check.str_param(pipeline_name, "pipeline_name")
    location = graphene_info.context.get_code_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    partition_sets = [
        partition_set
        for partition_set in repository.get_partition_sets()
        if partition_set.job_name == pipeline_name
    ]

    return GraphenePartitionSets(
        results=[
            GraphenePartitionSet(
                repository_handle=repository.handle,
                remote_partition_set=partition_set,
            )
            for partition_set in sorted(
                partition_sets,
                key=lambda partition_set: (
                    partition_set.job_name,
                    partition_set.mode,
                    partition_set.name,
                ),
            )
        ]
    )


def get_partition_set(
    graphene_info: ResolveInfo, repository_selector: RepositorySelector, partition_set_name: str
) -> Union["GraphenePartitionSet", "GraphenePartitionSetNotFoundError"]:
    from dagster_graphql.schema.partition_sets import (
        GraphenePartitionSet,
        GraphenePartitionSetNotFoundError,
    )

    check.inst_param(repository_selector, "repository_selector", RepositorySelector)
    check.str_param(partition_set_name, "partition_set_name")
    location = graphene_info.context.get_code_location(repository_selector.location_name)
    repository = location.get_repository(repository_selector.repository_name)
    partition_sets = repository.get_partition_sets()
    for partition_set in partition_sets:
        if partition_set.name == partition_set_name:
            return GraphenePartitionSet(
                repository_handle=repository.handle,
                remote_partition_set=partition_set,
            )

    return GraphenePartitionSetNotFoundError(partition_set_name)


def get_partition_by_name(
    graphene_info: ResolveInfo,
    repository_handle: RepositoryHandle,
    partition_set: RemotePartitionSet,
    partition_name: str,
) -> "GraphenePartition":
    from dagster_graphql.schema.partition_sets import GraphenePartition

    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.inst_param(partition_set, "partition_set", RemotePartitionSet)
    check.str_param(partition_name, "partition_name")
    return GraphenePartition(
        repository_handle=repository_handle,
        remote_partition_set=partition_set,
        partition_name=partition_name,
    )


def get_partition_config(
    graphene_info: ResolveInfo,
    repository_handle: RepositoryHandle,
    job_name: str,
    partition_name: str,
    selected_asset_keys: Optional[AbstractSet[AssetKey]],
) -> "GraphenePartitionRunConfig":
    from dagster_graphql.schema.partition_sets import GraphenePartitionRunConfig

    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(job_name, "job_name")
    check.str_param(partition_name, "partition_name")

    result = graphene_info.context.get_partition_config(
        repository_handle, job_name, partition_name, graphene_info.context.instance
    )

    if isinstance(result, PartitionExecutionErrorSnap):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return GraphenePartitionRunConfig(yaml=dump_run_config_yaml(result.run_config))


def get_partition_tags(
    graphene_info: ResolveInfo,
    repository_handle: RepositoryHandle,
    job_name: str,
    partition_name: str,
    selected_asset_keys: Optional[AbstractSet[AssetKey]],
) -> "GraphenePartitionTags":
    from dagster_graphql.schema.partition_sets import GraphenePartitionTags
    from dagster_graphql.schema.tags import GraphenePipelineTag

    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(job_name, "job_name")
    check.str_param(partition_name, "partition_name")

    result = graphene_info.context.get_partition_tags(
        repository_handle,
        job_name,
        partition_name,
        graphene_info.context.instance,
        selected_asset_keys=selected_asset_keys,
    )

    if isinstance(result, PartitionExecutionErrorSnap):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return GraphenePartitionTags(
        results=[
            GraphenePipelineTag(key=key, value=value)
            for key, value in result.tags.items()
            if get_tag_type(key) != TagType.HIDDEN
        ]
    )


def get_partitions(
    repository_handle: RepositoryHandle,
    partition_set: RemotePartitionSet,
    partition_names: Sequence[str],
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    reverse: bool = False,
) -> "GraphenePartitions":
    from dagster_graphql.schema.partition_sets import GraphenePartition, GraphenePartitions

    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.inst_param(partition_set, "partition_set", RemotePartitionSet)

    partition_names = apply_cursor_limit_reverse(partition_names, cursor, limit, reverse)

    return GraphenePartitions(
        results=[
            GraphenePartition(
                remote_partition_set=partition_set,
                repository_handle=repository_handle,
                partition_name=partition_name,
            )
            for partition_name in partition_names
        ]
    )


def get_partition_set_partition_statuses(
    graphene_info: ResolveInfo,
    remote_partition_set: RemotePartitionSet,
    partition_names: Sequence[str],
) -> Sequence["GraphenePartitionStatus"]:
    check.inst_param(remote_partition_set, "remote_partition_set", RemotePartitionSet)

    repository_handle = remote_partition_set.repository_handle
    partition_set_name = remote_partition_set.name

    run_partition_data = graphene_info.context.instance.run_storage.get_run_partition_data(
        runs_filter=RunsFilter(
            statuses=[status for status in DagsterRunStatus if status != DagsterRunStatus.CANCELED],
            tags={
                PARTITION_SET_TAG: partition_set_name,
                REPOSITORY_LABEL_TAG: repository_handle.get_remote_origin().get_label(),
            },
        )
    )

    return partition_statuses_from_run_partition_data(
        partition_set_name,
        run_partition_data,
        partition_names,
    )


def partition_statuses_from_run_partition_data(
    partition_set_name: Optional[str],
    run_partition_data: Sequence[RunPartitionData],
    partition_names: Sequence[str],
    backfill_id: Optional[str] = None,
) -> Sequence["GraphenePartitionStatus"]:
    from dagster_graphql.schema.partition_sets import (
        GraphenePartitionStatus,
        GraphenePartitionStatuses,
    )

    partition_data_by_name = {
        partition_data.partition: partition_data for partition_data in run_partition_data
    }

    suffix = f":{backfill_id}" if backfill_id else ""

    results = []
    for name in partition_names:
        partition_id = f'{partition_set_name or "__NO_PARTITION_SET__"}:{name}{suffix}'
        if not partition_data_by_name.get(name):
            results.append(
                GraphenePartitionStatus(
                    id=partition_id,
                    partitionName=name,
                )
            )
            continue
        partition_data = partition_data_by_name[name]
        results.append(
            GraphenePartitionStatus(
                id=partition_id,
                partitionName=name,
                runId=partition_data.run_id,
                runStatus=partition_data.status.value,
                runDuration=(
                    partition_data.end_time - partition_data.start_time
                    if partition_data.end_time and partition_data.start_time
                    else None
                ),
            )
        )

    return GraphenePartitionStatuses(results=results)


def partition_status_counts_from_run_partition_data(
    run_partition_data: Sequence[RunPartitionData], partition_names: Sequence[str]
) -> Sequence["GraphenePartitionStatusCounts"]:
    from dagster_graphql.schema.partition_sets import GraphenePartitionStatusCounts

    partition_data_by_name = {
        partition_data.partition: partition_data for partition_data in run_partition_data
    }

    count_by_status = defaultdict(int)
    for name in partition_names:
        if not partition_data_by_name.get(name):
            count_by_status["NOT_STARTED"] += 1
            continue
        partition_data = partition_data_by_name[name]
        count_by_status[partition_data.status.value] += 1

    return [GraphenePartitionStatusCounts(runStatus=k, count=v) for k, v in count_by_status.items()]


def get_partition_set_partition_runs(
    graphene_info: ResolveInfo,
    partition_set: RemotePartitionSet,
    partition_names: Sequence[str],
) -> Sequence["GraphenePartitionRun"]:
    from dagster_graphql.schema.partition_sets import GraphenePartitionRun
    from dagster_graphql.schema.pipelines.pipeline import GrapheneRun

    run_records = graphene_info.context.instance.get_run_records(
        RunsFilter(tags={PARTITION_SET_TAG: partition_set.name})
    )

    by_partition = {}
    for record in run_records:
        partition_name = record.dagster_run.tags.get(PARTITION_NAME_TAG)
        if not partition_name or partition_name in by_partition:
            # all_partition_set_runs is in descending order by creation time, we should ignore
            # runs for the same partition if we've already considered the partition
            continue
        by_partition[partition_name] = record

    return [
        GraphenePartitionRun(
            id=f"{partition_set.name}:{partition_name}",
            partitionName=partition_name,
            run=(
                GrapheneRun(by_partition[partition_name])
                if partition_name in by_partition
                else None
            ),
        )
        # for partition_name, run_record in by_partition.items()
        for partition_name in partition_names
    ]
