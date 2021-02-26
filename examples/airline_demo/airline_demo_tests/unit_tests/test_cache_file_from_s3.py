import os
import tempfile
from unittest import mock

import pytest
from airline_demo.cache_file_from_s3 import cache_file_from_s3
from dagster import (
    DagsterInvalidDefinitionError,
    ModeDefinition,
    ResourceDefinition,
    execute_pipeline,
    execute_solid,
    pipeline,
)
from dagster.core.storage.file_cache import LocalFileHandle, fs_file_cache


def execute_solid_with_resources(solid_def, resource_defs, run_config):
    @pipeline(
        name="{}_solid_test".format(solid_def.name),
        mode_defs=[ModeDefinition(resource_defs=resource_defs)],
    )
    def test_pipeline():
        return solid_def()

    return execute_pipeline(test_pipeline, run_config)


def test_cache_file_from_s3_basic():
    s3_session = mock.MagicMock()
    with tempfile.TemporaryDirectory() as temp_dir:
        solid_result = execute_solid(
            cache_file_from_s3,
            ModeDefinition(
                resource_defs={
                    "file_cache": fs_file_cache,
                    "s3": ResourceDefinition.hardcoded_resource(s3_session),
                }
            ),
            run_config={
                "solids": {
                    "cache_file_from_s3": {
                        "inputs": {"s3_coordinate": {"bucket": "some-bucket", "key": "some-key"}}
                    }
                },
                "resources": {"file_cache": {"config": {"target_folder": temp_dir}}},
            },
        )

        # assert the download occurred
        assert s3_session.download_file.call_count == 1

        assert solid_result.success

        expectation_results = solid_result.expectation_results_during_compute
        assert len(expectation_results) == 1
        expectation_result = expectation_results[0]
        assert expectation_result.success
        assert expectation_result.label == "file_handle_exists"
        path_in_metadata = expectation_result.metadata_entries[0].entry_data.path
        assert isinstance(path_in_metadata, str)
        assert os.path.exists(path_in_metadata)

        assert isinstance(solid_result.output_value(), LocalFileHandle)
        assert "some-key" in solid_result.output_value().path_desc


def test_cache_file_from_s3_specify_target_key():
    s3_session = mock.MagicMock()
    with tempfile.TemporaryDirectory() as temp_dir:
        solid_result = execute_solid(
            cache_file_from_s3,
            ModeDefinition(
                resource_defs={
                    "file_cache": fs_file_cache,
                    "s3": ResourceDefinition.hardcoded_resource(s3_session),
                }
            ),
            run_config={
                "solids": {
                    "cache_file_from_s3": {
                        "inputs": {"s3_coordinate": {"bucket": "some-bucket", "key": "some-key"}},
                        "config": {"file_key": "specified-file-key"},
                    }
                },
                "resources": {"file_cache": {"config": {"target_folder": temp_dir}}},
            },
        )

        # assert the download occurred
        assert s3_session.download_file.call_count == 1
        assert solid_result.success
        assert isinstance(solid_result.output_value(), LocalFileHandle)
        assert "specified-file-key" in solid_result.output_value().path_desc


def test_cache_file_from_s3_skip_download():
    with tempfile.TemporaryDirectory() as temp_dir:
        s3_session_one = mock.MagicMock()
        execute_solid(
            cache_file_from_s3,
            ModeDefinition(
                resource_defs={
                    "file_cache": fs_file_cache,
                    "s3": ResourceDefinition.hardcoded_resource(s3_session_one),
                }
            ),
            run_config={
                "solids": {
                    "cache_file_from_s3": {
                        "inputs": {"s3_coordinate": {"bucket": "some-bucket", "key": "some-key"}}
                    }
                },
                "resources": {"file_cache": {"config": {"target_folder": temp_dir}}},
            },
        )

        # assert the download occurred
        assert s3_session_one.download_file.call_count == 1

        s3_session_two = mock.MagicMock()
        execute_solid(
            cache_file_from_s3,
            ModeDefinition(
                resource_defs={
                    "file_cache": fs_file_cache,
                    "s3": ResourceDefinition.hardcoded_resource(s3_session_two),
                }
            ),
            run_config={
                "solids": {
                    "cache_file_from_s3": {
                        "inputs": {"s3_coordinate": {"bucket": "some-bucket", "key": "some-key"}}
                    }
                },
                "resources": {"file_cache": {"config": {"target_folder": temp_dir}}},
            },
        )

        # assert the download did not occur because file is already there
        assert s3_session_two.download_file.call_count == 0


def test_cache_file_from_s3_overwrite():
    with tempfile.TemporaryDirectory() as temp_dir:
        s3_session_one = mock.MagicMock()
        execute_solid(
            cache_file_from_s3,
            ModeDefinition(
                resource_defs={
                    "file_cache": fs_file_cache,
                    "s3": ResourceDefinition.hardcoded_resource(s3_session_one),
                }
            ),
            run_config={
                "solids": {
                    "cache_file_from_s3": {
                        "inputs": {"s3_coordinate": {"bucket": "some-bucket", "key": "some-key"}}
                    }
                },
                "resources": {
                    "file_cache": {"config": {"target_folder": temp_dir, "overwrite": True}}
                },
            },
        )

        # assert the download occurred
        assert s3_session_one.download_file.call_count == 1

        s3_session_two = mock.MagicMock()
        execute_solid(
            cache_file_from_s3,
            ModeDefinition(
                resource_defs={
                    "file_cache": fs_file_cache,
                    "s3": ResourceDefinition.hardcoded_resource(s3_session_two),
                }
            ),
            run_config={
                "solids": {
                    "cache_file_from_s3": {
                        "inputs": {"s3_coordinate": {"bucket": "some-bucket", "key": "some-key"}}
                    }
                },
                "resources": {
                    "file_cache": {"config": {"target_folder": temp_dir, "overwrite": True}}
                },
            },
        )

        # assert the download did not occur because file is already there
        assert s3_session_two.download_file.call_count == 0


def test_missing_resources():
    with pytest.raises(DagsterInvalidDefinitionError):
        with tempfile.TemporaryDirectory() as temp_dir:
            execute_solid(
                cache_file_from_s3,
                ModeDefinition(resource_defs={"file_cache": fs_file_cache}),
                run_config={
                    "solids": {
                        "cache_file_from_s3": {
                            "inputs": {
                                "s3_coordinate": {"bucket": "some-bucket", "key": "some-key"}
                            }
                        }
                    },
                    "resources": {"file_cache": {"config": {"target_folder": temp_dir}}},
                },
            )
