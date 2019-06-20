import os

import pytest

from dagster import (
    PipelineDefinition,
    ModeDefinition,
    execute_pipeline,
    ResourceDefinition,
    DagsterInvalidDefinitionError,
)
from dagster_aws.s3.resources import S3Resource
from dagster.core.storage.file_cache import fs_file_cache, LocalFileHandle
from dagster.seven import mock
from dagster.utils.test import get_temp_dir
from dagster_examples.airline_demo.cache_file_from_s3 import cache_file_from_s3


def execute_solid_with_resources(solid_def, resources, environment_dict):
    pipeline_def = PipelineDefinition(
        name='{}_solid_test'.format(solid_def.name),
        solid_defs=[solid_def],
        mode_definitions=[ModeDefinition(resources=resources)],
    )

    return execute_pipeline(pipeline_def, environment_dict)


def test_cache_file_from_s3_basic():
    s3_session = mock.MagicMock()
    with get_temp_dir() as temp_dir:
        pipeline_result = execute_solid_with_resources(
            cache_file_from_s3,
            resources={
                'file_cache': fs_file_cache,
                's3': ResourceDefinition.hardcoded_resource(S3Resource(s3_session)),
            },
            environment_dict={
                'solids': {
                    'cache_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {'file_cache': {'config': {'target_folder': temp_dir}}},
            },
        )

        # assert the download occured
        assert s3_session.download_file.call_count == 1

        assert pipeline_result.success

        solid_result = pipeline_result.result_for_solid('cache_file_from_s3')

        assert solid_result.success

        expectation_results = solid_result.expectation_results_during_compute
        assert len(expectation_results) == 1
        expectation_result = expectation_results[0]
        assert expectation_result.success
        assert expectation_result.label == 'file_handle_exists'
        path_in_metadata = expectation_result.metadata_entries[0].entry_data.path
        assert isinstance(path_in_metadata, str)
        assert os.path.exists(path_in_metadata)

        assert isinstance(solid_result.result_value(), LocalFileHandle)
        assert 'some-key' in solid_result.result_value().path_desc


def test_cache_file_from_s3_specify_target_key():
    s3_session = mock.MagicMock()
    with get_temp_dir() as temp_dir:
        pipeline_result = execute_solid_with_resources(
            cache_file_from_s3,
            resources={
                'file_cache': fs_file_cache,
                's3': ResourceDefinition.hardcoded_resource(S3Resource(s3_session)),
            },
            environment_dict={
                'solids': {
                    'cache_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}},
                        'config': {'file_key': 'specified-file-key'},
                    }
                },
                'resources': {'file_cache': {'config': {'target_folder': temp_dir}}},
            },
        )

        # assert the download occured
        assert s3_session.download_file.call_count == 1
        assert pipeline_result.success
        solid_result = pipeline_result.result_for_solid('cache_file_from_s3')
        assert solid_result.success
        assert isinstance(solid_result.result_value(), LocalFileHandle)
        assert 'specified-file-key' in solid_result.result_value().path_desc


def test_cache_file_from_s3_skip_download():
    with get_temp_dir() as temp_dir:
        s3_session_one = mock.MagicMock()
        pipeline_result_one = execute_solid_with_resources(
            cache_file_from_s3,
            resources={
                'file_cache': fs_file_cache,
                's3': ResourceDefinition.hardcoded_resource(S3Resource(s3_session_one)),
            },
            environment_dict={
                'solids': {
                    'cache_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {'file_cache': {'config': {'target_folder': temp_dir}}},
            },
        )

        assert pipeline_result_one.success
        # assert the download occured
        assert s3_session_one.download_file.call_count == 1

        s3_session_two = mock.MagicMock()
        pipeline_result_two = execute_solid_with_resources(
            cache_file_from_s3,
            resources={
                'file_cache': fs_file_cache,
                's3': ResourceDefinition.hardcoded_resource(S3Resource(s3_session_two)),
            },
            environment_dict={
                'solids': {
                    'cache_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {'file_cache': {'config': {'target_folder': temp_dir}}},
            },
        )

        assert pipeline_result_two.success
        # assert the download did not occur because file is already there
        assert s3_session_two.download_file.call_count == 0


def test_cache_file_from_s3_overwrite():
    with get_temp_dir() as temp_dir:
        s3_session_one = mock.MagicMock()
        pipeline_result_one = execute_solid_with_resources(
            cache_file_from_s3,
            resources={
                'file_cache': fs_file_cache,
                's3': ResourceDefinition.hardcoded_resource(S3Resource(s3_session_one)),
            },
            environment_dict={
                'solids': {
                    'cache_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {
                    'file_cache': {'config': {'target_folder': temp_dir, 'overwrite': True}}
                },
            },
        )

        assert pipeline_result_one.success
        # assert the download occured
        assert s3_session_one.download_file.call_count == 1

        s3_session_two = mock.MagicMock()
        pipeline_result_two = execute_solid_with_resources(
            cache_file_from_s3,
            resources={
                'file_cache': fs_file_cache,
                's3': ResourceDefinition.hardcoded_resource(s3_session_two),
            },
            environment_dict={
                'solids': {
                    'cache_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {
                    'file_cache': {'config': {'target_folder': temp_dir, 'overwrite': True}}
                },
            },
        )

        assert pipeline_result_two.success
        # assert the download did not occur because file is already there
        assert s3_session_two.download_file.call_count == 0


def test_missing_resources():
    with pytest.raises(DagsterInvalidDefinitionError):
        with get_temp_dir() as temp_dir:
            execute_solid_with_resources(
                cache_file_from_s3,
                resources={'file_cache': fs_file_cache},
                environment_dict={
                    'solids': {
                        'cache_file_from_s3': {
                            'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                        }
                    },
                    'resources': {'file_cache': {'config': {'target_folder': temp_dir}}},
                },
            )
