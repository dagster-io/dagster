from collections.abc import Sequence
from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.external_data import (
    PartitionConfigSnap,
    PartitionExecutionErrorSnap,
    PartitionNamesSnap,
    PartitionSetExecutionParamSnap,
    PartitionTagsSnap,
    partition_set_snap_name_for_job_name,
)
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._grpc.types import PartitionArgs, PartitionNamesArgs, PartitionSetExecutionParamArgs
from dagster._serdes import deserialize_value

if TYPE_CHECKING:
    from dagster._grpc.client import DagsterGrpcClient


def sync_get_external_partition_names_grpc(
    api_client: "DagsterGrpcClient",
    repository_handle: RepositoryHandle,
    job_name: str,
) -> PartitionNamesSnap:
    from dagster._grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(job_name, "job_name")
    repository_origin = repository_handle.get_remote_origin()
    result = deserialize_value(
        api_client.external_partition_names(
            partition_names_args=PartitionNamesArgs(
                repository_origin=repository_origin,
                job_name=job_name,
                partition_set_name=partition_set_snap_name_for_job_name(job_name),
            ),
        ),
        (PartitionNamesSnap, PartitionExecutionErrorSnap),
    )
    if isinstance(result, PartitionExecutionErrorSnap):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result


def sync_get_external_partition_config_grpc(
    api_client: "DagsterGrpcClient",
    repository_handle: RepositoryHandle,
    job_name: str,
    partition_name: str,
    instance: DagsterInstance,
) -> PartitionConfigSnap:
    from dagster._grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(job_name, "job_name")
    check.str_param(partition_name, "partition_name")
    repository_origin = repository_handle.get_remote_origin()
    result = deserialize_value(
        api_client.external_partition_config(
            partition_args=PartitionArgs(
                repository_origin=repository_origin,
                job_name=job_name,
                partition_set_name=partition_set_snap_name_for_job_name(job_name),
                partition_name=partition_name,
                instance_ref=instance.get_ref(),
            ),
        ),
        (PartitionConfigSnap, PartitionExecutionErrorSnap),
    )
    if isinstance(result, PartitionExecutionErrorSnap):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result


def sync_get_external_partition_tags_grpc(
    api_client: "DagsterGrpcClient",
    repository_handle: RepositoryHandle,
    job_name: str,
    partition_name: str,
    instance: DagsterInstance,
) -> PartitionTagsSnap:
    from dagster._grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(job_name, "job_name")
    check.str_param(partition_name, "partition_name")

    repository_origin = repository_handle.get_remote_origin()
    result = deserialize_value(
        api_client.external_partition_tags(
            partition_args=PartitionArgs(
                repository_origin=repository_origin,
                job_name=job_name,
                partition_set_name=partition_set_snap_name_for_job_name(job_name),
                partition_name=partition_name,
                instance_ref=instance.get_ref(),
            ),
        ),
        (PartitionTagsSnap, PartitionExecutionErrorSnap),
    )
    if isinstance(result, PartitionExecutionErrorSnap):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result


def sync_get_external_partition_set_execution_param_data_grpc(
    api_client: "DagsterGrpcClient",
    repository_handle: RepositoryHandle,
    partition_set_name: str,
    partition_names: Sequence[str],
    instance: DagsterInstance,
) -> PartitionSetExecutionParamSnap:
    from dagster._grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
    check.str_param(partition_set_name, "partition_set_name")
    check.sequence_param(partition_names, "partition_names", of_type=str)

    repository_origin = repository_handle.get_remote_origin()

    result = deserialize_value(
        api_client.external_partition_set_execution_params(
            partition_set_execution_param_args=PartitionSetExecutionParamArgs(
                repository_origin=repository_origin,
                partition_set_name=partition_set_name,
                partition_names=partition_names,
                instance_ref=instance.get_ref(),
            ),
        ),
        (PartitionSetExecutionParamSnap, PartitionExecutionErrorSnap),
    )
    if isinstance(result, PartitionExecutionErrorSnap):
        raise DagsterUserCodeProcessError.from_error_info(result.error)

    return result
