import pytest

from dagster import file_relative_path
from dagster.api.snapshot_pipeline import sync_get_external_pipeline
from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import LocationHandle
from dagster.core.host_representation.external import ExternalPipeline
from dagster.core.host_representation.handle import PipelineHandle, RepositoryHandle
from dagster.serdes.ipc import DagsterIPCProtocolError


def test_pipeline_snapshot_api():
    location_handle = LocationHandle(
        'test', FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    external_pipeline = sync_get_external_pipeline(pipeline_handle)
    assert isinstance(external_pipeline, ExternalPipeline)
    assert external_pipeline.name == 'foo'


def test_pipeline_with_valid_subset_snapshot_api():
    location_handle = LocationHandle(
        'test', FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    external_pipeline = sync_get_external_pipeline(pipeline_handle, solid_subset=["do_something"])
    assert isinstance(external_pipeline, ExternalPipeline)
    assert external_pipeline.name == 'foo'


def test_pipeline_with_invalid_subset_snapshot_api():
    location_handle = LocationHandle(
        'test', FileCodePointer(file_relative_path(__file__, 'api_tests_repo.py'), 'bar_repo'),
    )
    pipeline_handle = PipelineHandle('foo', RepositoryHandle('bar', location_handle))

    with pytest.raises(
        DagsterIPCProtocolError, match="Pipeline foo has no solid named invalid_solid"
    ):
        sync_get_external_pipeline(pipeline_handle, solid_subset=["invalid_solid"])
