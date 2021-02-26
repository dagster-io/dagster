import os
from unittest import mock

import boto3
from dagster import ModeDefinition, pipeline, solid
from dagster.core.storage.file_cache import FSFileCache, fs_file_cache
from dagster.utils.temp_file import get_temp_dir, get_temp_file_name
from dagster.utils.test import execute_solid
from dagster_aws.s3 import S3Coordinate


@solid(required_resource_keys={"file_cache"})
def cache_file_from_s3(context, s3_coord: S3Coordinate) -> str:
    # we default the target_key to the last component of the s3 key.
    target_key = s3_coord["key"].split("/")[-1]

    with get_temp_file_name() as tmp_file:
        boto3.client("s3").download_file(
            Bucket=s3_coord["bucket"], Key=s3_coord["key"], Filename=tmp_file
        )

        file_cache = context.resources.file_cache
        with open(tmp_file, "rb") as tmp_file_object:
            # returns a handle rather than a path
            file_handle = file_cache.write_file_object(target_key, tmp_file_object)
            return file_handle.path


def test_cache_file_from_s3_step_two_skip_config():
    boto_s3 = mock.MagicMock()
    with get_temp_dir() as temp_dir, mock.patch(
        "boto3.client", new=lambda *_args, **_kwargs: boto_s3
    ):
        execute_solid(
            cache_file_from_s3,
            ModeDefinition.from_resources({"file_cache": FSFileCache(temp_dir)}),
            input_values={"s3_coord": {"bucket": "some-bucket", "key": "some-key"}},
        )

        assert boto_s3.download_file.call_count == 1

        assert os.path.exists(os.path.join(temp_dir, "some-key"))


def test_cache_file_from_s3_step_two_use_config():
    boto_s3 = mock.MagicMock()
    with get_temp_dir() as temp_dir, mock.patch(
        "boto3.client", new=lambda *_args, **_kwargs: boto_s3
    ):
        execute_solid(
            cache_file_from_s3,
            ModeDefinition(resource_defs={"file_cache": fs_file_cache}),
            run_config={
                "resources": {"file_cache": {"config": {"target_folder": temp_dir}}},
                "solids": {
                    "cache_file_from_s3": {
                        "inputs": {"s3_coord": {"bucket": "some-bucket", "key": "some-key"}}
                    }
                },
            },
        )

        assert boto_s3.download_file.call_count == 1

        assert os.path.exists(os.path.join(temp_dir, "some-key"))


@pipeline(mode_defs=[ModeDefinition(name="local", resource_defs={"file_cache": fs_file_cache})])
def step_two_pipeline():

    cache_file_from_s3()
