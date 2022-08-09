import sys

import pytest

from dagster._api.snapshot_pipeline import sync_get_external_pipeline_subset_grpc
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster._core.host_representation.handle import PipelineHandle
from dagster._utils.error import serializable_error_info_from_exc_info

from .utils import get_bar_repo_repository_location


def _test_pipeline_subset_grpc(pipeline_handle, api_client, solid_selection=None):
    return sync_get_external_pipeline_subset_grpc(
        api_client, pipeline_handle.get_external_origin(), solid_selection=solid_selection
    )


def test_pipeline_snapshot_api_grpc(instance):
    with get_bar_repo_repository_location(instance) as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        external_pipeline_subset_result = _test_pipeline_subset_grpc(pipeline_handle, api_client)
        assert isinstance(external_pipeline_subset_result, ExternalPipelineSubsetResult)
        assert external_pipeline_subset_result.success == True
        assert external_pipeline_subset_result.external_pipeline_data.name == "foo"


def test_pipeline_with_valid_subset_snapshot_api_grpc(instance):
    with get_bar_repo_repository_location(instance) as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        external_pipeline_subset_result = _test_pipeline_subset_grpc(
            pipeline_handle, api_client, ["do_something"]
        )
        assert isinstance(external_pipeline_subset_result, ExternalPipelineSubsetResult)
        assert external_pipeline_subset_result.success == True
        assert external_pipeline_subset_result.external_pipeline_data.name == "foo"


def test_pipeline_with_invalid_subset_snapshot_api_grpc(instance):
    with get_bar_repo_repository_location(instance) as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        with pytest.raises(
            DagsterUserCodeProcessError,
            match="No qualified solids to execute found for solid_selection",
        ):
            _test_pipeline_subset_grpc(pipeline_handle, api_client, ["invalid_solid"])


def test_pipeline_with_invalid_definition_snapshot_api_grpc(instance):
    with get_bar_repo_repository_location(instance) as repository_location:
        pipeline_handle = PipelineHandle(
            "bar", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        try:
            _test_pipeline_subset_grpc(pipeline_handle, api_client, ["fail_subset"])
        except DagsterUserCodeProcessError:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            assert (
                "Input 'some_input' of op 'fail_subset' has no way of being resolved"
                in error_info.cause.message
            )
