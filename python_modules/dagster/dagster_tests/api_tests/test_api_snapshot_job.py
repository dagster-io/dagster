import json
import sys

import dagster._check as check
import pytest
from dagster._api.snapshot_job import (
    gen_external_job_subset_grpc,
    sync_get_external_job_subset_grpc,
)
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.remote_representation.external import RemoteJob
from dagster._core.remote_representation.external_data import RemoteJobSubsetResult
from dagster._core.remote_representation.handle import JobHandle
from dagster._core.test_utils import environ
from dagster._utils.error import serializable_error_info_from_exc_info

from dagster_tests.api_tests.utils import get_bar_repo_code_location, get_bar_workspace


def _test_job_subset_grpc(job_handle, api_client, op_selection=None, include_parent_snapshot=True):
    return sync_get_external_job_subset_grpc(
        api_client,
        job_handle.get_remote_origin(),
        op_selection=op_selection,
        include_parent_snapshot=include_parent_snapshot,
    )


async def _async_test_job_subset_grpc(
    job_handle, api_client, op_selection=None, include_parent_snapshot=True
):
    return await gen_external_job_subset_grpc(
        api_client,
        job_handle.get_remote_origin(),
        op_selection=op_selection,
        include_parent_snapshot=include_parent_snapshot,
    )


def test_job_snapshot_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        repo = code_location.get_repository("bar_repo")
        job_handle = JobHandle("foo", repo.handle)
        api_client = code_location.client

        remote_job_subset_result = _test_job_subset_grpc(job_handle, api_client)
        assert isinstance(remote_job_subset_result, RemoteJobSubsetResult)
        assert remote_job_subset_result.success is True
        assert remote_job_subset_result.job_data_snap.name == "foo"  # pyright: ignore[reportOptionalMemberAccess]
        assert (
            remote_job_subset_result.repository_python_origin
            == code_location.get_repository("bar_repo").handle.repository_python_origin
        )


@pytest.mark.asyncio
async def test_async_job_snapshot_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        remote_job_subset_result = await _async_test_job_subset_grpc(job_handle, api_client)
        assert isinstance(remote_job_subset_result, RemoteJobSubsetResult)
        assert remote_job_subset_result.success is True
        assert remote_job_subset_result.job_data_snap.name == "foo"  # pyright: ignore[reportOptionalMemberAccess]
        assert (
            remote_job_subset_result.repository_python_origin
            == code_location.get_repository("bar_repo").handle.repository_python_origin
        )
        subset_selector = JobSubsetSelector(
            location_name=code_location.name,
            repository_name="bar_repo",
            job_name="foo",
            op_selection=["do_something"],
            asset_selection=None,
        )

        assert (
            code_location.get_job(subset_selector).job_snapshot
            == (await code_location.gen_job(subset_selector)).job_snapshot
        )

        full_selector = JobSubsetSelector(
            location_name=code_location.name,
            repository_name="bar_repo",
            job_name="foo",
            op_selection=None,
            asset_selection=None,
        )

        assert (
            code_location.get_job(full_selector).job_snapshot
            == (await code_location.gen_job(full_selector)).job_snapshot
        )


@pytest.mark.asyncio
async def test_job_loader(instance):
    with get_bar_workspace(instance) as workspace:
        foo_selector = JobSubsetSelector(
            location_name="bar_code_location",
            repository_name="bar_repo",
            job_name="foo",
            op_selection=None,
            asset_selection=None,
        )
        foo_selector_with_subset = JobSubsetSelector(
            location_name="bar_code_location",
            repository_name="bar_repo",
            job_name="foo",
            op_selection=["do_something"],
            asset_selection=None,
        )

        bar_selector = JobSubsetSelector(
            location_name="bar_code_location",
            repository_name="bar_repo",
            job_name="bar",
            op_selection=None,
            asset_selection=None,
        )

        jobs = list(
            await RemoteJob.gen_many(
                workspace,
                [
                    foo_selector,
                    foo_selector,
                    foo_selector_with_subset,
                    bar_selector,
                ],
            )
        )

        assert check.not_none(jobs[0]).name == "foo"
        assert jobs[0] is jobs[1]

        assert check.not_none(jobs[2]).node_names == ["do_something"]

        assert check.not_none(jobs[3]).name == "bar"


def test_job_snapshot_api_grpc_with_container_context(instance):
    container_context = {"k8s": {"namespace": "foo"}}
    with environ({"DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT": json.dumps(container_context)}):
        with get_bar_repo_code_location(instance) as code_location:
            assert code_location.container_context == container_context
            job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
            api_client = code_location.client

            remote_job_subset_result = _test_job_subset_grpc(job_handle, api_client)
            assert isinstance(remote_job_subset_result, RemoteJobSubsetResult)
            assert remote_job_subset_result.success is True
            assert check.not_none(remote_job_subset_result.job_data_snap).name == "foo"
            assert (
                remote_job_subset_result.repository_python_origin
                == code_location.get_repository("bar_repo").handle.repository_python_origin
            )
            assert (
                check.not_none(remote_job_subset_result.repository_python_origin).container_context
                == container_context
            )


def test_job_with_valid_subset_snapshot_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        remote_job_subset_result = _test_job_subset_grpc(job_handle, api_client, ["do_something"])
        assert isinstance(remote_job_subset_result, RemoteJobSubsetResult)
        assert remote_job_subset_result.success is True
        assert remote_job_subset_result.job_data_snap.name == "foo"  # pyright: ignore[reportOptionalMemberAccess]
        assert (
            remote_job_subset_result.job_data_snap.parent_job  # pyright: ignore[reportOptionalMemberAccess]
            == code_location.get_repository("bar_repo").get_full_job("foo").job_snapshot
        )


def test_job_with_valid_subset_snapshot_without_parent_snapshot(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("foo", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        remote_job_subset_result = _test_job_subset_grpc(
            job_handle, api_client, ["do_something"], include_parent_snapshot=False
        )
        assert isinstance(remote_job_subset_result, RemoteJobSubsetResult)
        assert remote_job_subset_result.success is True
        assert remote_job_subset_result.job_data_snap.name == "foo"  # pyright: ignore[reportOptionalMemberAccess]
        assert not remote_job_subset_result.job_data_snap.parent_job  # pyright: ignore[reportOptionalMemberAccess]


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


@pytest.mark.asyncio
async def test_async_job_with_invalid_definition_snapshot_api_grpc(instance):
    with get_bar_repo_code_location(instance) as code_location:
        job_handle = JobHandle("bar", code_location.get_repository("bar_repo").handle)
        api_client = code_location.client

        try:
            await _async_test_job_subset_grpc(job_handle, api_client, ["fail_subset"])
        except DagsterUserCodeProcessError:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            assert (
                "Input 'some_input' of op 'fail_subset' has no way of being resolved"
                in error_info.cause.message
            )
