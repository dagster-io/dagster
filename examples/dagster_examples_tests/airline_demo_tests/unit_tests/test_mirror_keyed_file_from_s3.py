import os

import pytest

from dagster import (
    PipelineDefinition,
    ModeDefinition,
    execute_pipeline,
    ResourceDefinition,
    DagsterInvalidDefinitionError,
)
from dagster.seven import mock
from dagster.utils.test import get_temp_dir
from dagster_examples.airline_demo.mirror_keyed_file_from_s3 import mirror_keyed_file_from_s3
from dagster_examples.airline_demo.keyed_file_store import keyed_fs_file_store, LocalFileHandle


def execute_solid_with_resources(solid_def, resources, environment_dict):
    pipeline_def = PipelineDefinition(
        name='{}_solid_test'.format(solid_def.name),
        solids=[solid_def],
        mode_definitions=[ModeDefinition(resources=resources)],
    )

    return execute_pipeline(pipeline_def, environment_dict)


def test_mirror_keyed_file_from_s3_basic():
    s3_session = mock.MagicMock()
    with get_temp_dir() as temp_dir:
        pipeline_result = execute_solid_with_resources(
            mirror_keyed_file_from_s3,
            resources={
                'keyed_file_store': keyed_fs_file_store,
                's3': ResourceDefinition.hardcoded_resource(s3_session),
            },
            environment_dict={
                'solids': {
                    'mirror_keyed_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {'keyed_file_store': {'config': {'target_folder': temp_dir}}},
            },
        )

        # assert the download occured
        assert s3_session.download_file.call_count == 1

        assert pipeline_result.success

        solid_result = pipeline_result.result_for_solid('mirror_keyed_file_from_s3')

        assert solid_result.success

        expectation_results = solid_result.expectation_results_during_compute
        assert len(expectation_results) == 1
        expectation_result = expectation_results[0]
        assert expectation_result.success
        assert expectation_result.name == 'file_handle_exists'
        assert isinstance(expectation_result.result_metadata['path'], str)
        assert os.path.exists(expectation_result.result_metadata['path'])

        assert isinstance(solid_result.result_value(), LocalFileHandle)
        assert 'some-key' in solid_result.result_value().path_desc


def test_mirror_keyed_file_from_s3_specify_target_key():
    s3_session = mock.MagicMock()
    with get_temp_dir() as temp_dir:
        pipeline_result = execute_solid_with_resources(
            mirror_keyed_file_from_s3,
            resources={
                'keyed_file_store': keyed_fs_file_store,
                's3': ResourceDefinition.hardcoded_resource(s3_session),
            },
            environment_dict={
                'solids': {
                    'mirror_keyed_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}},
                        'config': {'file_key': 'specified-file-key'},
                    }
                },
                'resources': {'keyed_file_store': {'config': {'target_folder': temp_dir}}},
            },
        )

        # assert the download occured
        assert s3_session.download_file.call_count == 1
        assert pipeline_result.success
        solid_result = pipeline_result.result_for_solid('mirror_keyed_file_from_s3')
        assert solid_result.success
        assert isinstance(solid_result.result_value(), LocalFileHandle)
        assert 'specified-file-key' in solid_result.result_value().path_desc


def test_mirror_keyed_file_from_s3_skip_download():
    with get_temp_dir() as temp_dir:
        s3_one = mock.MagicMock()
        pipeline_result_one = execute_solid_with_resources(
            mirror_keyed_file_from_s3,
            resources={
                'keyed_file_store': keyed_fs_file_store,
                's3': ResourceDefinition.hardcoded_resource(s3_one),
            },
            environment_dict={
                'solids': {
                    'mirror_keyed_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {'keyed_file_store': {'config': {'target_folder': temp_dir}}},
            },
        )

        assert pipeline_result_one.success
        # assert the download occured
        assert s3_one.download_file.call_count == 1

        s3_two = mock.MagicMock()
        pipeline_result_two = execute_solid_with_resources(
            mirror_keyed_file_from_s3,
            resources={
                'keyed_file_store': keyed_fs_file_store,
                's3': ResourceDefinition.hardcoded_resource(s3_two),
            },
            environment_dict={
                'solids': {
                    'mirror_keyed_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {'keyed_file_store': {'config': {'target_folder': temp_dir}}},
            },
        )

        assert pipeline_result_two.success
        # assert the download did not occur because file is already there
        assert s3_two.download_file.call_count == 0


def test_mirror_keyed_file_from_s3_overwrite():
    with get_temp_dir() as temp_dir:
        s3_one = mock.MagicMock()
        pipeline_result_one = execute_solid_with_resources(
            mirror_keyed_file_from_s3,
            resources={
                'keyed_file_store': keyed_fs_file_store,
                's3': ResourceDefinition.hardcoded_resource(s3_one),
            },
            environment_dict={
                'solids': {
                    'mirror_keyed_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {
                    'keyed_file_store': {'config': {'target_folder': temp_dir, 'overwrite': True}}
                },
            },
        )

        assert pipeline_result_one.success
        # assert the download occured
        assert s3_one.download_file.call_count == 1

        s3_two = mock.MagicMock()
        pipeline_result_two = execute_solid_with_resources(
            mirror_keyed_file_from_s3,
            resources={
                'keyed_file_store': keyed_fs_file_store,
                's3': ResourceDefinition.hardcoded_resource(s3_two),
            },
            environment_dict={
                'solids': {
                    'mirror_keyed_file_from_s3': {
                        'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                    }
                },
                'resources': {
                    'keyed_file_store': {'config': {'target_folder': temp_dir, 'overwrite': True}}
                },
            },
        )

        assert pipeline_result_two.success
        # assert the download did not occur because file is already there
        assert s3_two.download_file.call_count == 0


def test_missing_resources():
    with pytest.raises(DagsterInvalidDefinitionError):
        with get_temp_dir() as temp_dir:
            execute_solid_with_resources(
                mirror_keyed_file_from_s3,
                resources={'keyed_file_store': keyed_fs_file_store},
                environment_dict={
                    'solids': {
                        'mirror_keyed_file_from_s3': {
                            'inputs': {'bucket_data': {'bucket': 'some-bucket', 'key': 'some-key'}}
                        }
                    },
                    'resources': {'keyed_file_store': {'config': {'target_folder': temp_dir}}},
                },
            )
