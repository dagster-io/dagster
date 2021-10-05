import re
import sys

import pytest
from dagster.api.snapshot_pipeline import sync_get_external_pipeline_subset_grpc
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.host_representation.handle import PipelineHandle
from dagster.utils.error import serializable_error_info_from_exc_info

from .utils import get_bar_repo_repository_location


def _test_pipeline_subset_grpc(pipeline_handle, api_client, solid_selection=None):
    return sync_get_external_pipeline_subset_grpc(
        api_client, pipeline_handle.get_external_origin(), solid_selection=solid_selection
    )


def test_pipeline_snapshot_api_grpc():
    with get_bar_repo_repository_location() as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        external_pipeline_subset_result = _test_pipeline_subset_grpc(pipeline_handle, api_client)
        assert isinstance(external_pipeline_subset_result, ExternalPipelineSubsetResult)
        assert external_pipeline_subset_result.success == True
        assert external_pipeline_subset_result.external_pipeline_data.name == "foo"


def test_pipeline_with_valid_subset_snapshot_api_grpc():
    with get_bar_repo_repository_location() as repository_location:
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


def test_pipeline_with_invalid_subset_snapshot_api_grpc():
    with get_bar_repo_repository_location() as repository_location:
        pipeline_handle = PipelineHandle(
            "foo", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        with pytest.raises(
            DagsterUserCodeProcessError,
            match="No qualified solids to execute found for solid_selection",
        ):
            _test_pipeline_subset_grpc(pipeline_handle, api_client, ["invalid_solid"])


def test_pipeline_with_invalid_definition_snapshot_api_grpc():
    with get_bar_repo_repository_location() as repository_location:
        pipeline_handle = PipelineHandle(
            "bar", repository_location.get_repository("bar_repo").handle
        )
        api_client = repository_location.client

        try:
            _test_pipeline_subset_grpc(pipeline_handle, api_client, ["fail_subset"])
        except DagsterUserCodeProcessError:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            assert re.match(
                (
                    r".*DagsterInvalidSubsetError[\s\S]*"
                    r"The attempted subset \['fail_subset'\] for pipeline bar results in an invalid pipeline"
                ),
                error_info.message,
            )
            assert re.match(
                (
                    r".*DagsterInvalidDefinitionError[\s\S]*"
                    r"add a dagster_type_loader for the type 'InputTypeWithoutHydration'"
                ),
                error_info.cause.message,
            )
