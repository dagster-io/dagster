import re
import sys

import pytest

from dagster import file_relative_path
from dagster.api.snapshot_pipeline import sync_get_external_pipeline_subset
from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import RepositoryLocationHandle
from dagster.core.host_representation.external_data import ExternalPipelineSubsetResult
from dagster.core.host_representation.handle import PipelineHandle, RepositoryHandle


def test_pipeline_snapshot_api():
    location_handle = RepositoryLocationHandle.create_in_process_location(
        FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    external_pipeline_subset_result = sync_get_external_pipeline_subset(pipeline_handle)
    assert isinstance(external_pipeline_subset_result, ExternalPipelineSubsetResult)
    assert external_pipeline_subset_result.success == True
    assert external_pipeline_subset_result.external_pipeline_data.name == 'foo'


def test_pipeline_with_valid_subset_snapshot_api():
    location_handle = RepositoryLocationHandle.create_in_process_location(
        FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    external_pipeline_subset_result = sync_get_external_pipeline_subset(
        pipeline_handle, solid_subset=["do_something"]
    )
    assert isinstance(external_pipeline_subset_result, ExternalPipelineSubsetResult)
    assert external_pipeline_subset_result.success == True
    assert external_pipeline_subset_result.external_pipeline_data.name == 'foo'


def test_pipeline_with_invalid_subset_snapshot_api():
    location_handle = RepositoryLocationHandle.create_in_process_location(
        FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    external_pipeline_subset_result = sync_get_external_pipeline_subset(
        pipeline_handle, solid_subset=["invalid_solid"]
    )
    assert isinstance(external_pipeline_subset_result, ExternalPipelineSubsetResult)
    assert external_pipeline_subset_result.success == False
    assert (
        "Pipeline foo has no solid named invalid_solid"
        in external_pipeline_subset_result.error.message
    )


@pytest.mark.skipif(sys.version_info.major < 3, reason='Exception cause only vailable in py3+')
def test_pipeline_with_invalid_definition_snapshot_api():
    location_handle = RepositoryLocationHandle.create_in_process_location(
        FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('bar', RepositoryHandle('bar', location_handle))

    external_pipeline_subset_result = sync_get_external_pipeline_subset(
        pipeline_handle, solid_subset=["fail_subset"]
    )
    assert isinstance(external_pipeline_subset_result, ExternalPipelineSubsetResult)
    assert external_pipeline_subset_result.success == False
    assert re.match(
        (
            r'.*DagsterInvalidSubsetError[\s\S]*'
            r"The atempted subset \['fail_subset'\] for pipeline bar results in an invalid pipeline"
        ),
        external_pipeline_subset_result.error.message,
    )
    assert re.match(
        (
            r'.*DagsterInvalidDefinitionError[\s\S]*'
            r'add a input_hydration_config for the type "InputTypeWithoutHydration"'
        ),
        external_pipeline_subset_result.error.cause.message,
    )
