import sys

import pytest
from dagster._api.snapshot_job import sync_get_external_job_subset_grpc
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.remote_representation.external_data import ExternalJobSubsetResult
from dagster._core.remote_representation.handle import JobHandle
from dagster._grpc.types import JobSubsetSnapshotArgs
from dagster._serdes import deserialize_value
from dagster._utils.error import serializable_error_info_from_exc_info

from dagster_tests.api_tests.utils import get_bar_repo_code_location


def _test_job_subset_grpc(job_handle, api_client, op_selection=None, include_parent_snapshot=True):
    return sync_get_external_job_subset_grpc(
        api_client,
        job_handle.get_external_origin(),
        op_selection=op_selection,
        include_parent_snapshot=include_parent_snapshot,
    )


def test_job_snapshot_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        external_job_subset_result = _test_job_subset_grpc(job_handle, api_client)
        assert isinstance(external_job_subset_result, ExternalJobSubsetResult)
        assert external_job_subset_result.success is True
        assert external_job_subset_result.external_job_data.name == "foo"


def test_job_snapshot_deserialize_error(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        external_pipeline_subset_result = deserialize_value(
            api_client.external_pipeline_subset(
                pipeline_subset_snapshot_args=JobSubsetSnapshotArgs(
                    job_origin=job_handle.get_external_origin(),
                    op_selection=None,
                    asset_selection=None,
                    include_parent_snapshot=True,
                )._replace(job_origin="INVALID"),
            )
        )
        assert isinstance(external_pipeline_subset_result, ExternalJobSubsetResult)
        assert external_pipeline_subset_result.success is False
        assert external_pipeline_subset_result.error


def test_job_with_valid_subset_snapshot_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        external_job_subset_result = _test_job_subset_grpc(job_handle, api_client, ["do_something"])
        assert isinstance(external_job_subset_result, ExternalJobSubsetResult)
        assert external_job_subset_result.success is True
        assert external_job_subset_result.external_job_data.name == "foo"
        assert (
            external_job_subset_result.external_job_data.parent_job_snapshot
            == code_location.get_repository("bar_repo").get_full_external_job("foo").job_snapshot
        )


def test_job_with_valid_subset_snapshot_without_parent_snapshot(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        external_job_subset_result = _test_job_subset_grpc(
            job_handle, api_client, ["do_something"], include_parent_snapshot=False
        )
        assert isinstance(external_job_subset_result, ExternalJobSubsetResult)
        assert external_job_subset_result.success is True
        assert external_job_subset_result.external_job_data.name == "foo"
        assert not external_job_subset_result.external_job_data.parent_job_snapshot


def test_job_with_invalid_subset_snapshot_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        with pytest.raises(
            DagsterUserCodeProcessError,
            match="No qualified ops to execute found for op_selection",
        ):
            _test_job_subset_grpc(job_handle, api_client, ["invalid_op"])


def test_job_with_invalid_definition_snapshot_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("bar", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        try:
            _test_job_subset_grpc(job_handle, api_client, ["fail_subset"])
        except DagsterUserCodeProcessError:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            assert (
                "Input 'some_input' of op 'fail_subset' has no way of being resolved"
                in error_info.cause.message
            )
