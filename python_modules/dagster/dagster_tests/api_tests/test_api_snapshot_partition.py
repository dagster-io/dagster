import string

import pytest
from dagster._api.snapshot_partition import (
    sync_get_external_partition_config_grpc,
    sync_get_external_partition_names_grpc,
    sync_get_external_partition_set_execution_param_data_grpc,
    sync_get_external_partition_tags_grpc,
)
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.host_representation import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
)
from dagster._core.instance import DagsterInstance
from dagster._grpc.types import PartitionArgs, PartitionNamesArgs, PartitionSetExecutionParamArgs
from dagster._serdes import deserialize_value

from .utils import get_bar_repo_code_location


def test_external_partition_names_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle
        data = sync_get_external_partition_names_grpc(
            code_location.client, repository_handle, "baz_partition_set"
        )
        assert isinstance(data, ExternalPartitionNamesData)
        assert data.partition_names == list(string.ascii_lowercase)


def test_external_partition_names_deserialize_error_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        api_client = code_location.client

        repository_handle = code_location.get_repository("bar_repo").handle
        repository_origin = repository_handle.get_external_origin()

        result = deserialize_value(
            api_client.external_partition_names(
                partition_names_args=PartitionNamesArgs(
                    repository_origin=repository_origin,
                    partition_set_name="foo",
                )._replace(repository_origin="INVALID"),
            )
        )
        assert isinstance(result, ExternalPartitionExecutionErrorData)


def test_external_partitions_config_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle

        data = sync_get_external_partition_config_grpc(
            code_location.client, repository_handle, "baz_partition_set", "c", instance
        )
        assert isinstance(data, ExternalPartitionConfigData)
        assert data.run_config
        assert data.run_config["ops"]["do_input"]["inputs"]["x"]["value"] == "c"  # type: ignore


def test_external_partitions_config_error_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle

        with pytest.raises(DagsterUserCodeProcessError):
            sync_get_external_partition_config_grpc(
                code_location.client,
                repository_handle,
                "error_partition_config",
                "c",
                instance,
            )


def test_external_partition_config_deserialize_error_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle

        api_client = code_location.client

        result = deserialize_value(
            api_client.external_partition_config(
                partition_args=PartitionArgs(
                    repository_origin=repository_handle.get_external_origin(),
                    partition_set_name="foo",
                    partition_name="bar",
                    instance_ref=instance.get_ref(),
                )._replace(repository_origin="INVALID"),
            )
        )

        assert isinstance(result, ExternalPartitionExecutionErrorData)


def test_external_partitions_tags_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle

        data = sync_get_external_partition_tags_grpc(
            code_location.client, repository_handle, "baz_partition_set", "c", instance=instance
        )
        assert isinstance(data, ExternalPartitionTagsData)
        assert data.tags
        assert data.tags["foo"] == "bar"


def test_external_partitions_tags_deserialize_error_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle
        repository_origin = repository_handle.get_external_origin()

        api_client = code_location.client

        result = deserialize_value(
            api_client.external_partition_tags(
                partition_args=PartitionArgs(
                    repository_origin=repository_origin,
                    partition_set_name="fooba",
                    partition_name="c",
                    instance_ref=instance.get_ref(),
                )._replace(repository_origin="INVALID"),
            )
        )
        assert isinstance(result, ExternalPartitionExecutionErrorData)


def test_external_partitions_tags_error_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle

        with pytest.raises(DagsterUserCodeProcessError):
            sync_get_external_partition_tags_grpc(
                code_location.client, repository_handle, "error_partition_tags", "c", instance
            )


def test_external_partition_set_execution_params_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle

        data = sync_get_external_partition_set_execution_param_data_grpc(
            code_location.client,
            repository_handle,
            "baz_partition_set",
            ["a", "b", "c"],
            instance=instance,
        )
        assert isinstance(data, ExternalPartitionSetExecutionParamData)
        assert len(data.partition_data) == 3


def test_external_partition_set_execution_params_deserialize_error_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        repository_handle = code_location.get_repository("bar_repo").handle

        repository_origin = repository_handle.get_external_origin()

        api_client = code_location.client

        result = deserialize_value(
            api_client.external_partition_set_execution_params(
                partition_set_execution_param_args=PartitionSetExecutionParamArgs(
                    repository_origin=repository_origin,
                    partition_set_name="baz_partition_set",
                    partition_names=["a", "b", "c"],
                    instance_ref=instance.get_ref(),
                )._replace(repository_origin="INVALID"),
            )
        )

        assert isinstance(result, ExternalPartitionExecutionErrorData)


def test_dynamic_partition_set_grpc(instance: DagsterInstance):
    with get_bar_repo_code_location(instance) as code_location:
        instance.add_dynamic_partitions("dynamic_partitions", ["a", "b", "c"])
        repository_handle = code_location.get_repository("bar_repo").handle

        data = sync_get_external_partition_set_execution_param_data_grpc(
            code_location.client,
            repository_handle,
            "dynamic_job_partition_set",
            ["a", "b", "c"],
            instance=instance,
        )
        assert isinstance(data, ExternalPartitionSetExecutionParamData)
        assert len(data.partition_data) == 3

        data = sync_get_external_partition_config_grpc(
            code_location.client,
            repository_handle,
            "dynamic_job_partition_set",
            "a",
            instance,
        )
        assert isinstance(data, ExternalPartitionConfigData)
        assert data.name == "a"
        assert data.run_config == {}

        data = sync_get_external_partition_tags_grpc(
            code_location.client,
            repository_handle,
            "dynamic_job_partition_set",
            "a",
            instance,
        )
        assert isinstance(data, ExternalPartitionTagsData)
        assert data.tags
        assert data.tags["dagster/partition"] == "a"

        data = sync_get_external_partition_set_execution_param_data_grpc(
            code_location.client,
            repository_handle,
            "dynamic_job_partition_set",
            ["nonexistent_partition"],
            instance=instance,
        )
        assert isinstance(data, ExternalPartitionSetExecutionParamData)
        assert data.partition_data == []

        with pytest.raises(DagsterUserCodeProcessError, match="Could not find a partition"):
            sync_get_external_partition_config_grpc(
                code_location.client,
                repository_handle,
                "dynamic_job_partition_set",
                "nonexistent_partition",
                instance,
            )

        with pytest.raises(DagsterUserCodeProcessError, match="Could not find a partition"):
            sync_get_external_partition_tags_grpc(
                code_location.client,
                repository_handle,
                "dynamic_job_partition_set",
                "nonexistent_partition",
                instance,
            )
